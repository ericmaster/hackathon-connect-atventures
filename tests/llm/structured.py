"""Modo "structured outputs" nativo de Bedrock (outputConfig.textFormat json_schema).

Un JSON Schema no puede describir JSONL, así que el modelo devuelve UN objeto
{"messages": [<mensaje A2UI>, ...]} y aquí lo convertimos a JSONL antes de puntuar.
El schema fija el sobre A2UI y una variante por tipo de componente (subset del catálogo).
"""
import json

import checks

S = {"type": "string"}
REF = {"type": "object", "properties": {"path": S}, "required": ["path"], "additionalProperties": False}
DYN = S  # anyOf(string, {path}) agranda demasiado la gramática; los bindings van como string
# Bedrock: máx. 24 parámetros opcionales en todo el schema y additionalProperties:false en todo
# objeto. Por eso cada tipo de componente es una variante con TODAS sus props requeridas y las
# acciones se reducen a {"event":{"name":...}} (sin context; el sku va en la tarjeta).
ACTION = {"type": "object", "properties": {"event": {"type": "object", "properties": {"name": S},
          "required": ["name"], "additionalProperties": False}}, "required": ["event"], "additionalProperties": False}
CHECK = {"type": "object", "properties": {"call": S, "message": S},
         "required": ["call", "message"], "additionalProperties": False}
LINE = {"type": "object", "properties": {"name": S, "qty": {"type": "number"}, "price": S},
        "required": ["name", "qty", "price"], "additionalProperties": False}
PRODUCT = {"type": "object", "properties": {"sku": S, "name": S, "price": S, "cashback": S},
           "required": ["sku", "name", "price", "cashback"], "additionalProperties": False}
IDS = {"type": "array", "items": S}
B = {"type": "boolean"}
OPTS = {"type": "array", "items": {"type": "object", "properties": {"label": S, "value": S},
        "required": ["label", "value"], "additionalProperties": False}}

VARIANTS = {
    "Text": {"text": DYN, "variant": S}, ("Column", "Row", "List"): {"children": IDS}, "Card": {"child": S},
    "Button": {"child": S, "variant": S, "action": ACTION},
    "TextField": {"label": S, "value": REF, "variant": S, "checks": {"type": "array", "items": CHECK}},
    "ProductCard": {"sku": S, "name": S, "detail": S, "price": S, "cashback": S, "stock": S, "ventaLibre": B, "note": S, "action": ACTION},
    "PharmacyCard": {"pharmacyId": S, "name": S, "distance": S, "hours": S, "stock": S, "phone": S, "mapsUrl": S},
    "SugerenciaPersonalizada": {"message": S, "product": PRODUCT, "why": S, "action": ACTION},
    "AvisoSalud": {"text": S},
    "ResumenPedido": {"items": {"type": "array", "items": LINE}, "total": S, "cashback": S, "pharmacy": S, "action": ACTION},
    "ConfirmacionPedido": {"orderNumber": S, "pharmacy": S, "pickupTime": S, "qrValue": S},
    "FacturaMock": {"number": S, "customerName": S, "customerId": S, "items": {"type": "array", "items": LINE},
                    "subtotal": S, "iva": S, "total": S, "label": S},
    "Cupon": {"title": S, "code": S, "until": S, "note": S},
    "HandoffCard": {"summary": S, "pharmacy": S, "phone": S},
    "AlertaRoja": {"text": S, "phone": S, "action": ACTION},
}


def _variant(name, props):
    p = {"id": S, "component": {"type": "string", "enum": list(name) if isinstance(name, tuple) else [name]}, **props}
    return {"type": "object", "properties": p, "required": list(p), "additionalProperties": False}


# Probado 8 oct 2026 con Haiku 4.5: una variante por tipo (15 tipos) → "compiled grammar is too
# large"; con 8 variantes también; solo entra con <= 5. Unión plana de props opcionales → "too many
# optional parameters (58), limit 24". Solución práctica: el schema fija sobre + id + tipo (enum del
# catálogo) y las props van en "props" como string JSON, que aquí se aplanan al formato A2UI.
COMPONENT_VARIANTS = {"anyOf": [_variant(k, v) for k, v in VARIANTS.items()]}  # referencia (no compila)
COMPONENT = {"type": "object", "properties": {
    "id": S, "component": {"type": "string", "enum": sorted(checks.ALLOWED)},
    "props": {"type": "string", "description": "Objeto JSON con las props del componente, p. ej. {\"text\":\"Hola\",\"variant\":\"h2\"}"}},
    "required": ["id", "component", "props"], "additionalProperties": False}


def _msg(key, body_props, required):
    body = {"type": "object", "properties": body_props, "required": required, "additionalProperties": False}
    return {"type": "object", "properties": {"version": {"type": "string", "enum": [checks.VERSION]}, key: body},
            "required": ["version", key], "additionalProperties": False}


SCHEMA = {
    "type": "object",
    "properties": {"messages": {"type": "array", "items": {"anyOf": [
        _msg("createSurface", {"surfaceId": S, "catalogId": S}, ["surfaceId", "catalogId"]),
        _msg("updateComponents", {"surfaceId": S, "components": {"type": "array", "items": COMPONENT}}, ["surfaceId", "components"]),
    ]}}},
    "required": ["messages"], "additionalProperties": False,
}

OUTPUT_CONFIG = {"textFormat": {"type": "json_schema", "structure": {"jsonSchema": {
    "schema": json.dumps(SCHEMA), "name": "a2ui_messages",
    "description": "Mensajes A2UI v0.9.1 en orden (equivale a las líneas del JSONL)"}}}}

USER_SUFFIX = ("\n\nMODO STRUCTURED OUTPUT: en vez de JSONL, devuelve un objeto {\"messages\": [...]} "
               "con los mismos mensajes A2UI en el mismo orden (uno por elemento). Cada componente va como "
               "{\"id\",\"component\",\"props\"} donde props es un string JSON con el resto de sus propiedades.")


def to_jsonl(text):
    """{"messages":[...]} → JSONL. Si no parsea, devuelve el texto tal cual (lo marcará el chequeo json)."""
    try:
        obj = json.loads(text)
        for m in obj["messages"]:
            for c in (m.get("updateComponents") or {}).get("components", []):
                props = c.pop("props", "{}")
                c.update(json.loads(props) if isinstance(props, str) else props)
        return "\n".join(json.dumps(m, ensure_ascii=False) for m in obj["messages"])
    except Exception:
        return text
