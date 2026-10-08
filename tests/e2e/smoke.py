#!/usr/bin/env python3
"""Smoke e2e del contrato (services/api/CONTRACT.md) por invocación directa de la Lambda.

  python3 tests/e2e/smoke.py                      # Lambda connect-atv-orchestrator (us-east-1)
  python3 tests/e2e/smoke.py --only billing_gt50  # un caso
  python3 tests/e2e/smoke.py --local handler      # importa services/api/<módulo>.handler con FV_STORE=memory
  python3 tests/e2e/smoke.py --cli                # usa `aws lambda invoke` en vez de boto3

Serial (nunca en paralelo con la demo: Bedrock ≤1 RPS). Imprime tabla pass/fail con latencias.
Nunca imprime credenciales. Solo datos sintéticos.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import time
import traceback
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FN = os.environ.get("FV_LAMBDA", "connect-atv-orchestrator")
REGION = os.environ.get("AWS_REGION", "us-east-1")

CUIDADOR, PRACTICO, NUEVA, INVALIDA = "1710034065", "1712456787", "1729876548", "1710034066"


# ----------------------------------------------------------------------------- transporte
class Invoker:
    def __init__(self, mode, local_module=None):
        self.mode = mode
        if mode == "boto3":
            import boto3
            from botocore.config import Config
            self.client = boto3.client("lambda", region_name=REGION,
                                       config=Config(read_timeout=300, connect_timeout=10, retries={"max_attempts": 1}))
        elif mode == "local":
            os.environ.setdefault("FV_STORE", "memory")
            sys.path.insert(0, os.path.join(ROOT, "services", "api"))
            mod = __import__(local_module)
            self.fn = getattr(mod, "handler", None) or getattr(mod, "lambda_handler")

    def __call__(self, event):
        t0 = time.perf_counter()
        if self.mode == "boto3":
            r = self.client.invoke(FunctionName=FN, Payload=json.dumps(event).encode())
            raw = r["Payload"].read()
            if r.get("FunctionError"):
                raise RuntimeError(f"FunctionError: {raw[:300]!r}")
            out = json.loads(raw)
        elif self.mode == "cli":
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
                json.dump(event, f)
            outp = f.name + ".out"
            env = dict(os.environ, AWS_MAX_ATTEMPTS="1")
            p = subprocess.run(["aws", "lambda", "invoke", "--region", REGION, "--function-name", FN,
                                "--cli-binary-format", "raw-in-base64-out", "--cli-read-timeout", "300",
                                "--payload", f"file://{f.name}", outp], capture_output=True, text=True, env=env)
            if p.returncode:
                raise RuntimeError(p.stderr.strip()[-300:])
            out = json.load(open(outp))
            os.unlink(f.name); os.unlink(outp)
        else:
            out = self.fn(event, None)
        ms = (time.perf_counter() - t0) * 1000
        status = out.get("statusCode", 200)
        body = out.get("body")
        if isinstance(body, str):
            if out.get("isBase64Encoded"):
                body = base64.b64decode(body).decode()
            body = json.loads(body) if body else {}
        return status, (body if body is not None else out), ms


def event(method, path, body=None, identity="e2e"):
    return {
        "version": "2.0",
        "routeKey": f"{method} {path if not path.startswith('/admin/') or path == '/admin/logs' else '/admin/{service}'}",
        "rawPath": path,
        "rawQueryString": "",
        "headers": {"content-type": "application/json"},
        "pathParameters": ({"service": path.split("/")[2]} if path.startswith("/admin/") else {}),
        "requestContext": {
            "http": {"method": method, "path": path, "sourceIp": "127.0.0.1", "userAgent": "fv-e2e"},
            "authorizer": {"iam": {"cognitoIdentity": {"identityId": identity, "amr": ["unauthenticated"]},
                                   "cognitoIdentityId": identity}},
            "requestId": str(uuid.uuid4()),
        },
        "body": json.dumps(body) if body is not None else None,
        "isBase64Encoded": False,
    }


# ----------------------------------------------------------------------------- helpers A2UI
def components(resp):
    out = []
    for m in (resp or {}).get("messages", []) or []:
        uc = m.get("updateComponents")
        if uc:
            out += uc.get("components", [])
    return out


def find(resp, kind):
    return [c for c in components(resp) if c.get("component") == kind]


def has(resp, kind):
    return bool(find(resp, kind))


def action_names(resp):
    names = []
    for c in components(resp):
        ev = (c.get("action") or {}).get("event") or {}
        if ev.get("name"):
            names.append(ev["name"])
    return names


class Fail(AssertionError):
    pass


def check(cond, msg):
    if not cond:
        raise Fail(msg)


class Client:
    """Una sesión del contrato con su identidad sintética."""

    def __init__(self, inv, identity=None):
        self.inv = inv
        self.identity = identity or f"us-east-1:e2e-{uuid.uuid4().hex[:12]}"
        self.sid = None
        self.rev = None
        self.state = None
        self.last = None
        self.calls = []  # (label, status, ms)

    def _call(self, method, path, body=None, label=None, identity=None):
        st, b, ms = self.inv(event(method, path, body, identity or self.identity))
        self.calls.append((label or path, st, round(ms)))
        if isinstance(b, dict) and b.get("sessionId") and st < 500 and (identity is None):
            self.sid = b["sessionId"]
            self.rev = b.get("revision", self.rev)
            self.state = b.get("state", self.state)
            self.last = b
        return st, b

    def session(self, qr="BIENVENIDA"):
        return self._call("POST", "/session", {"qr": qr}, "session")

    def turn(self, text):
        return self._call("POST", "/turn", {"sessionId": self.sid, "text": text}, "turn")

    def act(self, name, context=None, revision=None, label=None):
        return self._call("POST", "/action", {
            "sessionId": self.sid, "revision": self.rev if revision is None else revision,
            "action": {"name": name, "surfaceId": f"fv-{self.rev}", "sourceComponentId": "e2e",
                       "context": context or {}, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}},
            label or name)

    def reset(self):
        return self._call("POST", "/demo/reset", {"sessionId": self.sid}, "reset")

    def admin(self, service):
        return self._call("GET", f"/admin/{service}", None, f"admin/{service}")

    # --- pasos compuestos
    def onboard(self, cedula, consent=True):
        st, b = self.session()
        check(st == 200 and b.get("state") == "cedula", f"/session → {st} {b.get('state')}")
        st, b = self.act("enviar_cedula", {"cedula": cedula})
        check(st == 200 and b.get("state") == "consentimiento", f"cédula → {st} {b.get('state')}")
        st, b = self.act("consentimiento", {"acepta": consent})
        check(st == 200 and b.get("state") == "consulta", f"consentimiento → {st} {b.get('state')}")
        return b

    def add(self, sku, qty=1):
        st, b = self.act("agregar_pedido", {"sku": sku, "qty": qty, "confirm": True})
        check(st == 200 and b.get("state") == "farmacia", f"agregar {sku} → {st} {b.get('state')} {err(b)}")
        return b

    def pick_pharmacy(self):
        cards = find(self.last, "PharmacyCard")
        check(cards, "sin PharmacyCard")
        st, b = self.act("retirar_aqui", {"pharmacyId": cards[0]["pharmacyId"]})
        check(st == 200 and b.get("state") == "resumen", f"retirar_aqui → {st} {b.get('state')} {err(b)}")
        return b

    def billing(self, prefer_cf):
        """Responde la facturación pregunta a pregunta. Devuelve (respuesta_confirmacion, offered_cf)."""
        st, b = self.act("confirmar_reserva", {"confirm": True})
        check(st == 200, f"confirmar_reserva → {st} {err(b)}")
        offered_cf = False
        values = {"email": "comprador.demo@example.com", "nombre": "María Demo Sintética",
                  "identificacion": NUEVA}
        for _ in range(8):
            if self.state == "confirmacion":
                return self.last, offered_cf
            check(self.state == "facturacion", f"estado inesperado {self.state}")
            names = action_names(self.last)
            ctxs = [((c.get("action") or {}).get("event") or {}).get("context") or {} for c in components(self.last)]
            if "facturacion_tipo" in names and any(x.get("tipo") == "consumidor_final" for x in ctxs):
                offered_cf = True
                if prefer_cf and not getattr(self, "_cf_sent", False):
                    self._cf_sent = True
                    st, b = self.act("facturacion_tipo", {"tipo": "consumidor_final"})
                    check(st == 200, f"consumidor_final → {st} {err(b)}")
                    continue
            campo = next((x.get("campo") for x in ctxs if x.get("campo")), None)
            if "facturacion_dato" in names and campo:
                st, b = self.act("facturacion_dato", {"campo": campo, "valor": values.get(campo, "x")})
                check(st == 200, f"dato {campo} → {st} {err(b)}")
                continue
            if "facturacion_tipo" in names and not prefer_cf:
                st, b = self.act("facturacion_tipo", {"tipo": "datos"})
                check(st == 200, f"tipo datos → {st} {err(b)}")
                continue
            if "confirmar_reserva" in names:
                st, b = self.act("confirmar_reserva", {"confirm": True})
                check(st == 200, f"confirmar_reserva final → {st} {err(b)}")
                continue
            raise Fail(f"facturación sin acción reconocible: {names}")
        raise Fail("facturación no terminó en 8 pasos")


def err(b):
    e = (b or {}).get("error") if isinstance(b, dict) else None
    return f"[{e.get('code')}]" if e else ""


# ----------------------------------------------------------------------------- casos
def case_happy_path(inv):
    """QR → cédula (Práctico) → consentimiento → consulta → producto → farmacia → resumen → factura → confirmación."""
    c = Client(inv)
    c.onboard(PRACTICO, True)
    st, b = c.turn("algo para la gripe")
    check(st == 200, f"/turn → {st} {err(b)}")
    prods = find(b, "ProductCard")
    check(prods, f"sin ProductCard (state={b.get('state')}, mode={b.get('mode')})")
    check(all(p.get("ventaLibre", True) for p in prods), "ProductCard con receta")
    check(not any(p.get("sku", "").startswith("FV-9") for p in prods), "señuelo Rx sugerido")
    c.add(prods[0]["sku"])
    c.pick_pharmacy()
    conf, _ = c.billing(prefer_cf=True)
    check(has(conf, "ConfirmacionPedido") and has(conf, "FacturaMock"), "sin ConfirmacionPedido/FacturaMock")
    fac = find(conf, "FacturaMock")[0]
    check("SIMULADA" in json.dumps(fac, ensure_ascii=False), "factura sin etiqueta SIMULADA")
    return c, f"mode={b.get('mode')} sku={prods[0]['sku']}"


def case_invalid_cedula_x3(inv):
    c = Client(inv)
    c.session()
    for i in range(3):
        st, b = c.act("enviar_cedula", {"cedula": INVALIDA})
        check(st in (200, 400), f"intento {i + 1} → {st}")
        check(b.get("state") == "cedula", f"intento {i + 1} avanzó a {b.get('state')}")
        if i < 2:
            check(not has(b, "HandoffCard"), f"handoff prematuro en intento {i + 1}")
    check(has(b, "HandoffCard"), "3er intento sin HandoffCard")
    return c, ""


def case_new_cedula(inv):
    c = Client(inv)
    c.session()
    st, b = c.act("enviar_cedula", {"cedula": NUEVA})
    check(st == 200 and b.get("state") == "consentimiento", f"→ {st} {b.get('state')}")
    note = ""
    st2, a = c.admin("crm")
    if st2 == 200:
        mine = [x for x in a.get("items", []) if x.get("cedula") == NUEVA and c.sid in str(x.get("_pk", ""))]
        check(mine, "perfil nuevo no aparece en CRM (sandbox)")
        check(not isinstance(mine[0].get("condiciones_probables"), list) or not mine[0]["condiciones_probables"],
              "condiciones expuestas")
        note = "perfil en CRM"
    else:
        note = f"admin {st2} (no verificado en CRM)"
    return c, note


def case_consent_no(inv):
    c = Client(inv)
    b = c.onboard(CUIDADOR, consent=False)
    check(not has(b, "Reposicion") and not has(b, "SugerenciaPersonalizada"), "personalización sin consentimiento")
    st, t = c.turn("algo para la gripe")
    check(st == 200, f"/turn → {st}")
    check(not has(t, "Reposicion") and not has(t, "SugerenciaPersonalizada"), "sugerencia personalizada sin consentimiento")
    txt = json.dumps(t, ensure_ascii=False).lower()
    check("don luis" not in txt and "multivitam" not in txt, "usa historial/nombre sin consentimiento")
    # contraste (informativo): con consentimiento debería aparecer reposición
    c2 = Client(inv)
    b2 = c2.onboard(CUIDADOR, consent=True)
    c.calls += c2.calls
    return c, ("con consentimiento: Reposicion ✓" if (has(b2, "Reposicion") or has(b2, "SugerenciaPersonalizada"))
               else "con consentimiento: sin Reposicion (revisar)")


def case_red_flag(inv):
    c = Client(inv)
    c.onboard(PRACTICO, True)
    st, b = c.turn("tengo dolor de pecho fuerte y me cuesta respirar")
    check(st == 200, f"/turn → {st}")
    check(has(b, "AlertaRoja"), f"sin AlertaRoja (mode={b.get('mode')})")
    check(not has(b, "ProductCard"), "AlertaRoja con productos")
    st, b = c.act("agregar_pedido", {"sku": "FV-1002", "qty": 1, "confirm": True})
    check(st == 409 and err(b) == "[blocked_red_flag]", f"comercio no bloqueado: {st} {err(b)}")
    return c, ""


def case_double_confirm(inv):
    c = Client(inv)
    c.onboard(PRACTICO, True)
    c.add("FV-1002")
    c.pick_pharmacy()
    conf, _ = c.billing(prefer_cf=True)
    order = (find(conf, "ConfirmacionPedido") or [{}])[0].get("orderNumber")
    check(order, "sin orderNumber")
    # doble toque: misma acción, misma revisión que el primer confirmar (ya vieja) y con la actual
    st1, b1 = c.act("confirmar_reserva", {"confirm": True}, revision=c.rev - 1, label="confirm dup (rev vieja)")
    check(st1 in (200, 409), f"dup rev vieja → {st1}")
    st2, b2 = c.act("confirmar_reserva", {"confirm": True}, label="confirm dup (rev actual)")
    check(st2 in (200, 409), f"dup rev actual → {st2}")
    for st_, b_ in ((st1, b1), (st2, b2)):
        o = (find(b_, "ConfirmacionPedido") or [{}])[0].get("orderNumber")
        check(o in (None, order), f"pedido duplicado {o} ≠ {order}")
    st, a = c.admin("pedidos")
    note = f"order={order}"
    if st == 200:
        mine = [x for x in a.get("items", []) if x.get("sessionId") == c.sid]
        check(len(mine) == 1, f"{len(mine)} pedidos para la sesión")
        st, f = c.admin("facturacion")
        if st == 200:
            check(len([x for x in f.get("items", []) if x.get("sessionId") == c.sid]) == 1, "facturas duplicadas")
        note += " 1 pedido/1 factura"
    return c, note


def case_billing_le50(inv):
    c = Client(inv)
    c.onboard(NUEVA, True)
    c.add("FV-1002", 1)  # $2,40 - cupón
    c.pick_pharmacy()
    conf, offered = c.billing(prefer_cf=True)
    check(offered, "≤$50 no ofreció consumidor final")
    fac = find(conf, "FacturaMock")[0]
    s = json.dumps(fac, ensure_ascii=False)
    check("9999999999999" in s or "CONSUMIDOR FINAL" in s.upper(), "factura no es consumidor final")
    check("@" in s, "factura sin email")
    return c, ""


def case_billing_gt50(inv):
    c = Client(inv)
    c.onboard(NUEVA, True)
    c.add("FV-2001", 5)  # 5 × $12,80 = $64 - $3 cupón = $61 > $50
    c.pick_pharmacy()
    # intentar consumidor final debe fallar
    st, b = c.act("confirmar_reserva", {"confirm": True})
    check(st == 200 and c.state == "facturacion", f"→ {st} {c.state}")
    check(not any((((x.get("action") or {}).get("event") or {}).get("context") or {}).get("tipo") == "consumidor_final"
                  for x in components(b)), ">$50 ofreció consumidor final")
    st, bad = c.act("facturacion_tipo", {"tipo": "consumidor_final"}, label="cf forzado")
    check(st >= 400 or c.state == "facturacion", f"consumidor final aceptado >$50 ({st})")
    c._cf_sent = True
    # sigue con datos completos (billing() vuelve a confirmar)
    conf, _ = c.billing(prefer_cf=False)
    s = json.dumps(find(conf, "FacturaMock")[0], ensure_ascii=False)
    check("9999999999999" not in s and NUEVA in s and "@" in s, "factura >$50 sin nombre/ID/email")
    return c, ""


def case_reset(inv):
    c = Client(inv)
    c.onboard(PRACTICO, True)
    c.add("FV-1002")
    rev = c.rev
    st, b = c.reset()
    check(st == 200 and b.get("state") == "cedula", f"reset → {st} {b.get('state')}")
    check(b.get("revision", 0) > rev, "revision no aumentó")
    st, b = c.act("enviar_cedula", {"cedula": PRACTICO})
    check(st == 200 and b.get("state") == "consentimiento", "tras reset no reinicia onboarding")
    return c, ""


def case_other_identity(inv):
    c = Client(inv)
    c.session()
    st, b = c._call("POST", "/turn", {"sessionId": c.sid, "text": "hola"}, "turn otra identidad",
                    identity="us-east-1:e2e-intruso")
    check(st == 403, f"otra identidad → {st}")
    return c, ""


def case_admin_readonly(inv):
    c = Client(inv)
    notes = []
    for s in ("crm", "catalogo", "inventario", "farmacias", "smartclub", "pedidos", "facturacion", "logs"):
        st, b = c.admin(s)
        check(st == 200 and isinstance(b.get("items"), list), f"admin/{s} → {st}")
        notes.append(f"{s}:{len(b['items'])}")
    crm = c.admin("crm")[1]["items"]
    check(not any(isinstance(x.get("condiciones_probables"), list) and x["condiciones_probables"] for x in crm),
          "condiciones probables crudas en /admin/crm")
    return c, " ".join(notes)


CASES = [
    ("happy_path", case_happy_path),
    ("invalid_cedula_x3", case_invalid_cedula_x3),
    ("new_cedula", case_new_cedula),
    ("consent_no", case_consent_no),
    ("red_flag", case_red_flag),
    ("double_confirm", case_double_confirm),
    ("billing_le50", case_billing_le50),
    ("billing_gt50", case_billing_gt50),
    ("reset", case_reset),
    ("other_identity_403", case_other_identity),
    ("admin_readonly", case_admin_readonly),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--local", metavar="MODULE")
    ap.add_argument("--cli", action="store_true")
    ap.add_argument("--json", metavar="FILE")
    a = ap.parse_args()
    inv = Invoker("local", a.local) if a.local else Invoker("cli" if a.cli else "boto3")
    rows = []
    for name, fn in CASES:
        if a.only and name not in a.only:
            continue
        t0 = time.perf_counter()
        c, ok, note = None, False, ""
        try:
            c, note = fn(inv)
            ok = True
        except Fail as e:
            note = f"FAIL: {e}"
        except Exception as e:  # noqa: BLE001
            note = f"ERROR: {type(e).__name__}: {str(e)[:200]}"
            if os.environ.get("FV_E2E_DEBUG"):
                traceback.print_exc()
        calls = getattr(c, "calls", []) if c else []
        ms = [x[2] for x in calls]
        rows.append({"case": name, "ok": ok, "calls": len(calls), "total_ms": round((time.perf_counter() - t0) * 1000),
                     "max_ms": max(ms) if ms else 0, "slowest": max(calls, key=lambda x: x[2])[0] if calls else "",
                     "note": note})
        print(f"{'PASS' if ok else 'FAIL'}  {name}", flush=True)
    print()
    print(f"{'case':<20} {'res':<5} {'calls':>5} {'total ms':>9} {'max ms':>7}  {'slowest':<22} note")
    print("-" * 110)
    for r in rows:
        print(f"{r['case']:<20} {'PASS' if r['ok'] else 'FAIL':<5} {r['calls']:>5} {r['total_ms']:>9} {r['max_ms']:>7}  "
              f"{r['slowest'][:22]:<22} {r['note'][:120]}")
    passed = sum(r["ok"] for r in rows)
    print(f"\n{passed}/{len(rows)} PASS")
    if a.json:
        json.dump(rows, open(a.json, "w"), ensure_ascii=False, indent=1)
    sys.exit(0 if passed == len(rows) else 1)


if __name__ == "__main__":
    main()
