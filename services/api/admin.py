"""Admin de solo lectura (workstream C): registros de los 7 servicios mock + logs.

La Lambda de A lo usa así (GET /admin/{service}, GET /admin/logs):
    import admin
    status, body = admin.handle(service, event)   # body = {"service", "items", "count"}
    body = admin.list_service(service)            # lo que ya usa handler.py (sin chequeo de allowlist)

Nunca escribe. Lee con mock.py/store.py de A (tabla única `connect-atv-data`):
    CAT/P#<sku> · PHARM/PH#<id> (stock embebido) · SEED/CRM#<cedula> + SBX#<sid>/CRM#<cedula>
    PROMO/CPNDEF#|PROMO# + SBX#<sid>/CPN#<cedula> · SBX#<sid>/ORD#<n> · SBX#<sid>/FAC#<n> · LOG#<día>/<ms>#<rnd>
"""
from __future__ import annotations

import json
import os

SERVICES = ("crm", "catalogo", "inventario", "farmacias", "smartclub", "pedidos", "facturacion")
INTERNAL_KEY = "condiciones_probables_interno"  # la UI lo rotula "interno, no visible al cliente"
MAX_ITEMS = 500


def _mock():
    import mock  # de A; import tardío para tests offline
    return mock


def _show_internal() -> bool:
    return os.environ.get("FV_ADMIN_SHOW_INTERNAL") == "1"


def _crm_items():
    """CRM con condiciones probables: ocultas por defecto (CONTRACT), visibles rotuladas si FV_ADMIN_SHOW_INTERNAL=1."""
    m = _mock()
    if not _show_internal():
        return m.admin_list("crm")
    from store import get_store
    s = get_store()
    raw = [dict(x, _pk="SEED") for x in s.query("SEED", "CRM#")] + s.scan_prefix("CRM#")
    seen, out = set(), []
    for x in raw:
        k = (x.get("_pk"), x.get("cedula"))
        if k in seen:
            continue
        seen.add(k)
        x = dict(x)
        x[INTERNAL_KEY] = x.pop("condiciones_probables", None) or []
        out.append(x)
    return out


def _smartclub_items():
    # Evita store.query(pk, "") (DynamoDB rechaza begins_with con prefijo vacío).
    from store import get_store
    s = get_store()
    return s.query("PROMO", "CPNDEF#") + s.query("PROMO", "PROMO#") + s.scan_prefix("CPN#")


def service_items(service: str) -> list:
    if service not in SERVICES:
        raise KeyError(service)
    if service == "crm":
        items = _crm_items()
    elif service == "smartclub":
        items = _smartclub_items()
    else:
        items = _mock().admin_list(service)
    return _jsonable((items or [])[:MAX_ITEMS])


def list_service(service: str) -> dict:
    """Body completo para GET /admin/{service} (lo llama handler.py de A tal cual)."""
    items = service_items(service)
    return {"service": service, "items": items, "count": len(items)}


def list_logs(limit: int = 100) -> list:
    """Últimos logs (hoy y ayer, hora EC). sk = '<epoch_ms>#rnd' → prefijo '1' (evita begins_with vacío)."""
    from datetime import datetime, timedelta
    from store import get_store
    limit = max(1, min(int(limit or 100), 200))
    now = datetime.now(_mock().EC_TZ)
    out = []
    for d in (now, now - timedelta(days=1)):
        if len(out) >= limit:
            break
        out += get_store().query("LOG#" + d.strftime("%Y-%m-%d"), "1", desc=True, limit=limit - len(out))
    return _jsonable(out)


def logs_body(limit: int = 100) -> dict:
    items = list_logs(limit)
    return {"service": "logs", "items": items, "count": len(items)}


def _jsonable(x):
    # Decimal/sets → JSON plano
    return json.loads(json.dumps(x, default=lambda o: float(o) if hasattr(o, "as_tuple") else list(o) if isinstance(o, (set, tuple)) else str(o), ensure_ascii=False))


def allowed(event: dict | None) -> bool:
    """Stub de autorización admin. Con IAM + Identity Pool invitado no hay grupos Cognito:
    si FV_ADMIN_IDENTITIES (lista separada por comas de identityId) está definida, solo esas pasan."""
    allow = [x.strip() for x in os.environ.get("FV_ADMIN_IDENTITIES", "").split(",") if x.strip()]
    if not allow:
        return True
    ident = (((event or {}).get("requestContext") or {}).get("authorizer") or {}).get("iam", {})
    cid = (ident.get("cognitoIdentity") or {}).get("identityId") or ident.get("cognitoIdentityId")
    return cid in allow


def handle(service: str, event: dict | None = None, limit: int | None = None):
    """→ (status, body). service ∈ SERVICES | 'logs'."""
    if not allowed(event):
        return 403, {"error": {"code": "forbidden", "message": "Solo administradores"}}
    try:
        if service == "logs":
            items = list_logs(limit or 100)
        else:
            items = service_items(service)
    except KeyError:
        return 404, {"error": {"code": "not_found", "message": f"Servicio desconocido: {service}"},
                     "services": list(SERVICES) + ["logs"]}
    return 200, {"service": service, "items": items, "count": len(items)}
