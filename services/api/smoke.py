"""Smoke contra la Lambda desplegada (invoke directo, sin endpoint público).

python3 services/api/smoke.py            # flujo completo + alarma
Imprime estado, componentes, modo y latencia por paso. Nunca imprime credenciales.
"""
import json
import sys
import time

import boto3
from botocore.config import Config

FN = "connect-atv-orchestrator"
lam = boto3.client("lambda", region_name="us-east-1", config=Config(read_timeout=40, retries={"max_attempts": 1}))
ROWS, FAIL = [], []


def inv(route, body=None, label=None):
    t0 = time.time()
    r = lam.invoke(FunctionName=FN, Payload=json.dumps({"route": route, "body": body or {}}).encode())
    out = json.loads(r["Payload"].read())
    wall = int((time.time() - t0) * 1000)
    comps = []
    for m in out.get("messages") or []:
        for c in (m.get("updateComponents") or {}).get("components") or []:
            if c["component"] not in ("Text", "Column", "Row", "Button", "Card"):
                comps.append(c["component"])
    tr = out.get("_trace") or {}
    ROWS.append((label or route, out.get("_status"), out.get("state"), out.get("mode"), wall, out.get("_ms"),
                 tr.get("nlu"), (tr.get("llm") or {}).get("ms"), ",".join(dict.fromkeys(comps))))
    return out


def comp(out, name):
    for m in out.get("messages") or []:
        for c in (m.get("updateComponents") or {}).get("components") or []:
            if c["component"] == name:
                return c
    return None


def act(r, name, ctx=None, label=None):
    return inv("POST /action", {"sessionId": r["sessionId"], "revision": r["revision"],
                                "action": {"name": name, "context": ctx or {}}}, label or name)


def expect(cond, msg):
    if not cond:
        FAIL.append(msg)


def main():
    r = inv("POST /session", {"qr": "BIENVENIDA"}, "session")
    expect(r["state"] == "cedula", "session→cedula")
    r = inv("POST /turn", {"sessionId": r["sessionId"], "text": "mi cédula es 1712456787"}, "turn cédula")
    expect(r["state"] == "consentimiento", "cedula→consentimiento")
    r = act(r, "consentimiento", {"acepta": True})
    expect(r["state"] == "consulta", "consent→consulta")
    r = inv("POST /turn", {"sessionId": r["sessionId"], "text": "algo para la gripe"}, "turn 'algo para la gripe'")
    expect('"seguridad"' in json.dumps(r) and not comp(r, "ProductCard"), "pregunta de seguridad antes de productos")
    r = act(r, "seguridad", {"ok": True}, "seguridad: No, ninguno (LLM)")
    pc = comp(r, "ProductCard")
    expect(pc is not None, "gripe → ProductCard")
    blob = json.dumps(r, ensure_ascii=False).lower()
    expect("rinitis" not in blob, "no condition leak")
    sku = pc["sku"] if pc else "FV-1002"
    r = act(r, "agregar_pedido", {"sku": sku, "confirm": True})
    expect(r["state"] == "farmacia", "agregar→farmacia")
    ph = comp(r, "PharmacyCard")
    r = act(r, "retirar_aqui", {"pharmacyId": ph["pharmacyId"]})
    expect(r["state"] == "resumen" and comp(r, "ResumenPedido"), "→resumen")
    r = act(r, "confirmar_reserva", {"confirm": True})
    expect(r["state"] == "facturacion", "→facturacion")
    r = act(r, "facturacion_tipo", {"tipo": "consumidor_final"})
    r = inv("POST /turn", {"sessionId": r["sessionId"], "text": "andrea arroba example punto com"}, "turn email")
    before = r
    r = act(r, "confirmar_reserva", {"confirm": True}, "confirmar_reserva")
    expect(r["state"] == "confirmacion" and comp(r, "FacturaMock") and comp(r, "ConfirmacionPedido"), "→confirmacion")
    dup = act(before, "confirmar_reserva", {"confirm": True}, "double tap (expect 409)")
    expect(dup.get("_status") == 409, "double tap no duplica")
    sid = r["sessionId"]
    # alarma
    r2 = inv("POST /turn", {"sessionId": sid, "text": "me duele mucho el pecho y no puedo respirar"}, "turn red flag")
    expect(comp(r2, "AlertaRoja") and not comp(r2, "ProductCard"), "red flag → AlertaRoja sin productos")
    r2 = inv("POST /turn", {"sessionId": sid, "text": "algo para la tos"}, "free turn after red flag")
    expect(comp(r2, "AlertaRoja") and not comp(r2, "ProductCard"), "alarma persiste en turno libre")
    x = act(r2, "agregar_pedido", {"sku": "FV-1002", "confirm": True}, "commerce after red flag")
    expect((x.get("error") or {}).get("code") == "blocked_red_flag", "comercio bloqueado tras alarma")
    r3 = inv("POST /demo/reset", {"sessionId": sid}, "demo/reset")
    expect(r3["state"] == "cedula", "reset→cedula")
    print(f"{'step':34} {'st':>4} {'state':14} {'mode':9} {'wall':>6} {'lambda':>6} {'nlu':9} {'llm':>5}  components")
    for row in ROWS:
        print(f"{row[0][:34]:34} {row[1]!s:>4} {row[2]!s:14} {row[3]!s:9} {row[4]:>6} {row[5]!s:>6} {row[6]!s:9} {row[7]!s:>5}  {row[8]}")
    print("FAIL:" if FAIL else "ALL OK", FAIL or "")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
