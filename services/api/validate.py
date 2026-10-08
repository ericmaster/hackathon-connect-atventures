"""Valida la salida del LLM con los chequeos de tests/llm/checks.py + reglas del servidor."""
import json
import sys
from pathlib import Path

try:
    import checks  # empaquetado junto al handler (deploy.sh lo copia)
except ImportError:  # local: usar tests/llm directamente
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests" / "llm"))
    import checks

import guardrails
import mock

COMMERCE_FORBIDDEN = {"ConfirmacionPedido", "FacturaMock", "Cupon", "ResumenPedido"}


def validate(text, surface_id, ctx_products, profile, red_flag=False):
    """→ (ok, msgs_normalizados | None, errores[])."""
    msgs, info = checks.parse_messages(text or "")
    if msgs is None:
        return False, None, [info.get("error") or "json"]
    errs = []
    for name, (ok, det) in {"shape": checks.check_shape(msgs, surface_id), "allowed": checks.check_allowed(msgs),
                            "no_condition": checks.check_no_condition(msgs)}.items():
        if ok is False:
            errs.append(f"{name}: {det}")
    comps = checks.components_of(msgs)
    types = [c.get("component") for c in comps]
    allowed_skus = {p["sku"] for p in ctx_products}
    for c in comps:
        t = c.get("component")
        if t in COMMERCE_FORBIDDEN:
            errs.append(f"{t} no permitido en turno libre")
        if t in ("ProductCard", "SugerenciaPersonalizada", "Reposicion"):
            sku = c.get("sku") or (c.get("product") or {}).get("sku")
            p = mock.product(sku)
            if sku not in allowed_skus or not p or p.get("requiere_receta"):
                errs.append(f"sku fuera de contexto o con receta: {sku}")
                continue
            # El servidor fija precio/acción (nunca confiar en el LLM)
            if t == "ProductCard":
                c["price"] = mock.money(p["price"])
                c["ventaLibre"] = True
                c["action"] = {"event": {"name": "agregar_pedido", "context": {"sku": sku, "confirm": True}}}
        if t == "AlertaRoja" and not red_flag:
            errs.append("AlertaRoja sin señal de alarma")
    hits = guardrails.leaks(checks.visible_text(msgs), profile)
    if hits:
        errs.append("filtra condición del CRM")
    if red_flag and any(t in types for t in ("ProductCard", "SugerenciaPersonalizada", "Reposicion")):
        errs.append("productos ante alarma")
    if errs:
        return False, None, errs
    # Aviso de salud obligatorio si hay productos.
    if "ProductCard" in types and "AvisoSalud" not in types:
        root = next(c for c in comps if c.get("id") == "root")
        if isinstance(root.get("children"), list):
            root["children"].append("aviso_srv")
            msgs.append({"version": "v0.9.1", "updateComponents": {"surfaceId": surface_id, "components": [
                {"id": "aviso_srv", "component": "AvisoSalud",
                 "text": "Si persiste, consulta a un médico. No reemplaza la consulta con un profesional de salud."}]}})
    return True, msgs, []


def spoken_from(msgs):
    for c in checks.components_of(msgs):
        if c.get("component") == "Text" and isinstance(c.get("text"), str) and len(c["text"]) > 8:
            s = c["text"][:220]
            if not checks.condition_hits(s):
                return s
    return "Aquí tienes lo que encontré."
