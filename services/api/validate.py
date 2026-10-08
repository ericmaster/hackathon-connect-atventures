"""Valida la salida del LLM con los chequeos de tests/llm/checks.py + reglas del servidor."""
import json
import re
import sys
from pathlib import Path

try:
    import checks  # empaquetado junto al handler (deploy.sh lo copia)
except ImportError:  # local: usar tests/llm directamente
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests" / "llm"))
    import checks

import fsm
import guardrails
import mock

COMMERCE_FORBIDDEN = {"ConfirmacionPedido", "FacturaMock", "Cupon", "ResumenPedido"}
HOME_RE = re.compile(r"inicio|reinici|empezar|nueva consulta|nueva_consulta|volver|home|menu", re.I)


def _label(comps, c):
    ch = next((x for x in comps if x.get("id") == c.get("child")), {})
    return ch.get("text") if isinstance(ch.get("text"), str) else ""


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
    drop = set()
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
        ev = (c.get("action") or {}).get("event") if isinstance(c.get("action"), dict) else None
        if t == "Button" and isinstance(ev, dict) and ev.get("name") not in fsm.ACTIONS:
            # Evento inventado por el LLM (p. ej. "volver_inicio") → 400 al tocarlo. "Inicio" = Nueva consulta
            # (seguir_comprando, como en confirmación); cualquier otro se descarta.
            if HOME_RE.search(f"{ev.get('name')} {_label(comps, c)}"):
                c["action"] = {"event": {"name": "seguir_comprando", "context": {}}}
            else:
                drop.add(c.get("id"))
    hits = guardrails.leaks(checks.visible_text(msgs), profile)
    if hits:
        errs.append("filtra condición del CRM")
    if red_flag and any(t in types for t in ("ProductCard", "SugerenciaPersonalizada", "Reposicion")):
        errs.append("productos ante alarma")
    if errs:
        return False, None, errs
    for c in comps:
        if isinstance(c.get("children"), list):
            c["children"] = [k for k in c["children"] if k not in drop]
        if c.get("child") in drop:
            c.pop("child")
    for m in msgs:
        uc = m.get("updateComponents")
        if uc and isinstance(uc.get("components"), list):
            uc["components"] = [c for c in uc["components"] if c.get("id") not in drop]
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
