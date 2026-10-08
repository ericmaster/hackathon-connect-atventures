"""Tests offline (sin AWS): FV_STORE=memory, GLiNER deshabilitado, LLM simulado.

python3 -m unittest discover -s services/api/tests -v
"""
import json
import os
import sys
import unittest
from pathlib import Path

os.environ["FV_STORE"] = "memory"
os.environ["FV_GLINER_DISABLED"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import validate  # noqa: E402,F401  (agrega tests/llm al path)
import checks  # noqa: E402
import fsm  # noqa: E402
import handler  # noqa: E402
import llm  # noqa: E402
import mock  # noqa: E402
import store  # noqa: E402
import validate  # noqa: E402
from cedula import valid_cedula, valid_id  # noqa: E402

CUIDADOR, PRACTICO, NEW = "1710034065", "1712456787", "1729876548"


def fake_llm_cards(ctx, deadline, extra=None):
    sid = ctx["surfaceId"]
    lines = [{"version": "v0.9.1", "createSurface": {"surfaceId": sid, "catalogId": "https://farmaenlace.ec/a2ui/fv/v1"}}]
    kids = ["t1"] + [f"p{i}" for i, _ in enumerate(ctx["data"]["products"])] + ["av"]
    comps = [{"id": "root", "component": "Column", "children": kids},
             {"id": "t1", "component": "Text", "text": "Para la gripe te puede ayudar:", "variant": "h3"},
             {"id": "av", "component": "AvisoSalud", "text": "Si persiste, consulta a un médico."}]
    for i, p in enumerate(ctx["data"]["products"]):
        comps.append(dict({"id": f"p{i}", "component": "ProductCard"}, **dict(p, price="$0,01")))
    for c in comps:
        lines.append({"version": "v0.9.1", "updateComponents": {"surfaceId": sid, "components": [c]}})
    return {"ok": True, "text": "\n".join(json.dumps(l, ensure_ascii=False) for l in lines), "ms": 5, "retries": 0}


def call(route, body=None, identity=None):
    ev = {"route": route, "body": body or {}}
    if identity:
        ev["identityId"] = identity
    return handler.handler(ev)


def types(resp):
    return [c["component"] for c in checks.components_of(resp["messages"])]


class Base(unittest.TestCase):
    def setUp(self):
        store.set_store(store.MemoryStore())
        mock._CACHE.clear()
        mock.seed()
        self.calls = 0
        self._orig = llm.generate

        def gen(ctx, deadline, extra=None):
            self.calls += 1
            return fake_llm_cards(ctx, deadline, extra)
        llm.generate = gen

    def tearDown(self):
        llm.generate = self._orig

    def act(self, r, name, ctx=None):
        return call("POST /action", {"sessionId": r["sessionId"], "revision": r["revision"], "action": {"name": name, "context": ctx or {}}})

    def onboard(self, ced=CUIDADOR, consent=True):
        r = call("POST /session", {"qr": "BIENVENIDA"})
        r = self.act(r, "enviar_cedula", {"cedula": ced})
        return self.act(r, "consentimiento", {"acepta": consent})


class TestCedula(unittest.TestCase):
    def test_mod10(self):
        for c in (CUIDADOR, PRACTICO, NEW, "0912345675"):
            self.assertTrue(valid_cedula(c), c)
        for c in ("1710034066", "171003406", "2510034065", "1770034065", "abc", "", None):
            self.assertFalse(valid_cedula(c), c)

    def test_ids(self):
        self.assertEqual(valid_id(CUIDADOR), "05")
        self.assertEqual(valid_id("1710034065001"), "04")
        self.assertEqual(valid_id("AB123456"), "06")
        self.assertIsNone(valid_id("123"))


class TestFSM(Base):
    def test_session_shape(self):
        r = call("POST /session")
        for k in ("sessionId", "state", "revision", "messages", "spokenText", "mode"):
            self.assertIn(k, r)
        self.assertEqual(r["state"], "cedula")
        ok, det = checks.check_shape(r["messages"], f"fv-{r['revision']}")
        self.assertTrue(ok, det)
        self.assertIn("cedulaEc", json.dumps(r["messages"]))

    def test_onboarding_and_new_profile(self):
        r = call("POST /session")
        r = self.act(r, "enviar_cedula", {"cedula": NEW})
        self.assertEqual(r["state"], "consentimiento")
        r = self.act(r, "consentimiento", {"acepta": False})
        self.assertEqual(r["state"], "consulta")
        self.assertIsNotNone(store.get_store().get("SBX#" + r["sessionId"], "CRM#" + NEW))

    def test_third_invalid_offers_handoff(self):
        r = call("POST /session")
        for i in range(3):
            r = self.act(r, "enviar_cedula", {"cedula": "1710034066"})
            self.assertEqual(r["state"], "cedula")
        self.assertIn("HandoffCard", types(r))

    def test_stale_revision_and_not_allowed(self):
        r = call("POST /session")
        bad = call("POST /action", {"sessionId": r["sessionId"], "revision": r["revision"] - 1,
                                    "action": {"name": "enviar_cedula", "context": {"cedula": CUIDADOR}}})
        self.assertEqual(bad["_status"], 409)
        bad = self.act(r, "confirmar_reserva", {"confirm": True})
        self.assertEqual(bad["error"]["code"], "action_not_allowed")
        bad = self.act(r, "borrar_todo")
        self.assertEqual(bad["_status"], 400)

    def test_cuidador_reposicion_and_why_has_no_condition(self):
        r = self.onboard(CUIDADOR)
        self.assertIn("SugerenciaPersonalizada", types(r))
        self.assertEqual(r["messages"][0]["createSurface"].get("theme"), {"senior": True})
        self.assertNotIn("por_que", json.dumps(r))  # el botón lo pinta la PWA
        rep = next(c for c in checks.components_of(r["messages"]) if c["component"] == "SugerenciaPersonalizada")
        self.assertTrue(rep["why"])
        blob = json.dumps(r, ensure_ascii=False).lower()
        self.assertNotIn("hipertens", blob)
        r = self.act(r, "por_que", {"sku": "FV-2001"})
        self.assertNotIn("hipertens", json.dumps(r, ensure_ascii=False).lower())
        self.assertIn("sueles", json.dumps(r, ensure_ascii=False).lower())

    def test_no_senior_theme_without_consent_or_for_practico(self):
        for ced, consent in ((CUIDADOR, False), (PRACTICO, True)):
            r = self.onboard(ced, consent)
            self.assertNotIn("theme", r["messages"][0]["createSurface"])

    def test_owner_check(self):
        r = call("POST /session", identity="us-east-1:aaa")
        x = call("POST /turn", {"sessionId": r["sessionId"], "text": CUIDADOR}, identity="us-east-1:bbb")
        self.assertEqual(x["_status"], 403)


class TestGuardrails(Base):
    def test_red_flag_blocks_products_and_commerce(self):
        r = self.onboard()
        r = call("POST /turn", {"sessionId": r["sessionId"], "text": "me duele el pecho y no puedo respirar"})
        t = types(r)
        self.assertIn("AlertaRoja", t)
        self.assertNotIn("ProductCard", t)
        self.assertEqual(self.calls, 0)  # el LLM nunca decide la alarma
        x = self.act(r, "agregar_pedido", {"sku": "FV-1002", "confirm": True})
        self.assertEqual(x["error"]["code"], "blocked_red_flag")

    def test_condition_never_in_llm_context_nor_output(self):
        seen = {}

        def spy(ctx, deadline, extra=None):
            seen["ctx"] = json.dumps(ctx, ensure_ascii=False)
            return fake_llm_cards(ctx, deadline, extra)
        llm.generate = spy
        r = self.onboard(CUIDADOR)
        r = call("POST /turn", {"sessionId": r["sessionId"], "text": "algo para la gripe"})
        self.assertNotIn("condiciones", seen["ctx"])
        self.assertNotIn("hipertens", seen["ctx"])
        skus = [c.get("sku") for c in checks.components_of(r["messages"]) if c["component"] == "ProductCard"]
        self.assertNotIn("FV-1001", skus)  # filtrado server-side (con fenilefrina)
        self.assertNotIn("FV-9001", skus)  # receta
        self.assertNotIn("$0,01", json.dumps(r))  # precio recalculado por el servidor
        ok, hits = checks.check_no_condition(r["messages"])
        self.assertTrue(ok, hits)

    def test_llm_leak_is_rejected_then_fail_closed(self):
        def leaky(ctx, deadline, extra=None):
            sid = ctx["surfaceId"]
            l = [{"version": "v0.9.1", "createSurface": {"surfaceId": sid, "catalogId": "x"}},
                 {"version": "v0.9.1", "updateComponents": {"surfaceId": sid, "components": [
                     {"id": "root", "component": "Column", "children": ["t"]},
                     {"id": "t", "component": "Text", "text": "Como tienes hipertensión, toma esto."}]}}]
            return {"ok": True, "text": "\n".join(json.dumps(x, ensure_ascii=False) for x in l)}
        llm.generate = leaky
        r = self.onboard(CUIDADOR)
        r = call("POST /turn", {"sessionId": r["sessionId"], "text": "algo para la gripe"})
        self.assertEqual(r["mode"], "simulado")
        self.assertNotIn("hipertens", json.dumps(r, ensure_ascii=False).lower())
        self.assertIn("ProductCard", types(r))

    def test_rx_goes_to_handoff(self):
        r = self.onboard(PRACTICO)
        r = call("POST /turn", {"sessionId": r["sessionId"], "text": "quiero amoxicilina"})
        self.assertIn("HandoffCard", types(r))
        self.assertNotIn("ProductCard", types(r))
        x = self.act(r, "agregar_pedido", {"sku": "FV-9002", "confirm": True})
        self.assertIn("HandoffCard", types(x))


class TestCheckout(Base):
    def _to_resumen(self, sku="FV-1002", qty=1, ced=PRACTICO):
        r = self.onboard(ced)
        r = call("POST /turn", {"sessionId": r["sessionId"], "text": "algo para la gripe"})
        r = self.act(r, "agregar_pedido", {"sku": sku, "qty": qty, "confirm": True})
        self.assertEqual(r["state"], "farmacia")
        ph = next(c for c in checks.components_of(r["messages"]) if c["component"] == "PharmacyCard")
        return self.act(r, "retirar_aqui", {"pharmacyId": ph["pharmacyId"]})

    def test_confirm_required(self):
        r = self.onboard()
        x = self.act(r, "agregar_pedido", {"sku": "FV-1002"})
        self.assertEqual(x["error"]["code"], "confirmation_required")

    def test_cf_under_50_and_idempotent(self):
        r = self._to_resumen()
        self.assertEqual(r["state"], "resumen")
        r = self.act(r, "confirmar_reserva", {"confirm": True})
        self.assertEqual(r["state"], "facturacion")
        self.assertIn("consumidor_final", json.dumps(r))
        r = self.act(r, "facturacion_tipo", {"tipo": "consumidor_final"})
        self.assertIn("/factura/email", json.dumps(r))
        bad = self.act(r, "facturacion_dato", {"campo": "email", "valor": "nope"})
        self.assertEqual(bad["state"], "facturacion")
        r = self.act(bad, "facturacion_dato", {"campo": "email", "valor": "andrea@example.com"})
        self.assertIn("Confirmar y reservar", json.dumps(r, ensure_ascii=False))
        before = r
        r = self.act(before, "confirmar_reserva", {"confirm": True})
        self.assertEqual(r["state"], "confirmacion")
        t = types(r)
        for c in ("ConfirmacionPedido", "FacturaMock", "Cupon"):
            self.assertIn(c, t)
        self.assertIn("SIMULADA", json.dumps(r))
        self.assertIn("9999999999999", json.dumps(r))
        dup = self.act(before, "confirmar_reserva", {"confirm": True})  # doble toque
        self.assertEqual(dup["_status"], 409)
        sid = r["sessionId"]
        self.assertEqual(len(store.get_store().query("SBX#" + sid, "ORD#")), 1)
        self.assertEqual(len(store.get_store().query("SBX#" + sid, "FAC#")), 1)
        cpn = store.get_store().get("SBX#" + sid, "CPN#" + PRACTICO)
        self.assertEqual(cpn["status"], "usado")

    def test_reserve_function_idempotent(self):
        r = self._to_resumen()
        s = store.get_store().get("SES#" + r["sessionId"], "META")
        p = store.get_store().get("SBX#" + r["sessionId"], "CRM#" + PRACTICO)
        b = {"tipo": "consumidor_final", "email": "a@b.co"}
        put = lambda res: (dict(s, revision=s["revision"] + 1), None, {"rev": s["revision"] + 1})  # noqa: E731
        r1, c1 = mock.reserve(r["sessionId"], s, p, b, s["revision"], put)
        r2, c2 = mock.reserve(r["sessionId"], s, p, b, s["revision"], put)
        self.assertTrue(c1)
        self.assertFalse(c2)
        self.assertEqual(r1["order"]["orderNumber"], r2["order"]["orderNumber"])

    def test_over_50_asks_name_id_email(self):
        r = self._to_resumen("FV-2009", 1, CUIDADOR)  # tensiómetro $45 + IVA = $51,75
        r = self.act(r, "confirmar_reserva", {"confirm": True})
        self.assertIn("/factura/nombre", json.dumps(r))
        self.assertNotIn("consumidor_final", json.dumps(r))
        x = self.act(r, "facturacion_tipo", {"tipo": "consumidor_final"}) if False else None
        r = self.act(r, "facturacion_dato", {"campo": "nombre", "valor": "Luis Pérez"})
        self.assertIn("/factura/identificacion", json.dumps(r))
        r = call("POST /turn", {"sessionId": r["sessionId"], "text": CUIDADOR})
        self.assertIn("/factura/email", json.dumps(r))
        r = call("POST /turn", {"sessionId": r["sessionId"], "text": "luis arroba example punto com"})
        r = call("POST /turn", {"sessionId": r["sessionId"], "text": "sí, confirmo"})
        self.assertEqual(r["state"], "confirmacion")
        fx = next(c for c in checks.components_of(r["messages"]) if c["component"] == "FacturaMock")
        self.assertEqual(fx["customerId"], CUIDADOR)
        self.assertEqual(fx["email"], "luis@example.com")

    def test_reset_only_this_sandbox(self):
        a = self._to_resumen()
        b = self.onboard(CUIDADOR)
        call("POST /demo/reset", {"sessionId": a["sessionId"]})
        self.assertEqual(store.get_store().query("SBX#" + a["sessionId"]), [])
        self.assertTrue(store.get_store().query("SBX#" + b["sessionId"]))


if __name__ == "__main__":
    unittest.main()
