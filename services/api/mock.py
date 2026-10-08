"""Cliente de los 7 servicios de Farmaenlace (CRM, Catálogo, Inventario, Farmacias, SmartClub/Promociones,
Pedidos, Facturación). Ya NO lee la tabla del orquestador: llama por HTTP + SigV4 a la API mock separada
`connect-atv-farmaenlace-api` (Lambda `connect-atv-farmaenlace-mock`, tabla `connect-atv-farmaenlace`),
como lo haría en producción contra los sistemas de Farmaenlace. Ver services/farmaenlace-mock/README.md.

Misma interfaz de funciones que antes (fsm/admin no cambian de forma). Fail-closed: si la API no responde
(timeout corto) se lanza BackendUnavailable → el turno devuelve error, nunca datos inventados. Solo catálogo
y farmacias (datos maestros) se sirven desde caché si un refresco falla.

Transporte (FV_FARMAENLACE_URL):
  https://<api>.execute-api...  → HTTPS + SigV4 (execute-api) con el rol de la Lambda
  http://127.0.0.1:8765         → HTTP local sin firma (services/farmaenlace-mock/local_server.py)
  (vacío) + FV_STORE=memory     → "inproc": invoca el handler de la mock en el mismo proceso (tests offline)
Los logs del orquestador (LOG#) siguen en su propia tabla vía store.py.
"""
import copy
import hashlib
import json
import os
import random
import threading
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlsplit

import fixtures  # noqa: F401  (COUPONS/CATALOG_ID siguen usándose en fsm)
from store import ConditionFailed, get_store

EC_TZ = timezone(timedelta(hours=-5))
_CACHE = {}
STATS = {}  # por request: llamadas y ms a la API de Farmaenlace (handler lo agrega al trace)
TIMEOUT_S = float(os.environ.get("FV_FARMAENLACE_TIMEOUT_S", "2.5"))
REGION = os.environ.get("AWS_REGION", "us-east-1")
TTL_MASTER = 300   # catálogo / farmacias
TTL_STOCK = 20     # inventario


class BackendUnavailable(Exception):
    """La API de Farmaenlace no respondió bien (fail-closed)."""


class NotFound(Exception):
    pass


def money(x):
    return "$" + f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def r2(x):
    return round(x + 1e-9, 2)


# ---------- transporte ----------
_tls = threading.local()
_INPROC = {}


def _base():
    return os.environ.get("FV_FARMAENLACE_URL", "").rstrip("/")


def _inproc():
    if "app" not in _INPROC:
        import importlib.util
        import sys
        here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "farmaenlace-mock")
        spec = importlib.util.spec_from_file_location("fe_data", os.path.join(here, "data.py"))
        d = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(d)
        sys.modules.setdefault("data", d)
        spec = importlib.util.spec_from_file_location("fe_app", os.path.join(here, "app.py"))
        a = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(a)
        _INPROC["app"] = a
        if not get_store().query("CAT", "P#"):  # el "sistema externo" siempre está sembrado
            a.seed()
    return _INPROC["app"]


def _sign(method, url, body, headers):
    import boto3
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest
    if "sess" not in _INPROC:
        _INPROC["sess"] = boto3.Session()
    creds = _INPROC["sess"].get_credentials().get_frozen_credentials()
    req = AWSRequest(method=method, url=url, data=body, headers=headers)
    SigV4Auth(creds, "execute-api", REGION).add_auth(req)
    return dict(req.headers.items())


def _conn(u, fresh=False):
    import http.client
    key = (u.scheme, u.netloc)
    pool = getattr(_tls, "pool", None)
    if pool is None:
        pool = _tls.pool = {}
    c = pool.get(key)
    if c is None or fresh:
        if c is not None:
            try:
                c.close()
            except Exception:  # noqa: BLE001
                pass
        cls = http.client.HTTPSConnection if u.scheme == "https" else http.client.HTTPConnection
        c = pool[key] = cls(u.netloc, timeout=TIMEOUT_S)
    return c


def _http(method, path, query, payload, headers):
    base = _base()
    url = base + path + ("?" + urlencode(query) if query else "")
    u = urlsplit(url)
    body = json.dumps(payload, ensure_ascii=False).encode() if payload is not None else None
    h = dict(headers, Host=u.netloc, Accept="application/json")
    if body is not None:
        h["Content-Type"] = "application/json"
    if u.scheme == "https":
        h = _sign(method, url, body, h)
    target = u.path + ("?" + u.query if u.query else "")
    last = None
    for attempt in range(2):  # 1 reintento por conexión keep-alive caída (todas las escrituras son idempotentes)
        c = _conn(u, fresh=attempt > 0)
        try:
            c.request(method, target, body=body, headers=h)
            r = c.getresponse()
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
        except (OSError, ValueError, Exception) as e:  # noqa: BLE001
            last = e
            if isinstance(e, TimeoutError) or "timed out" in str(e):
                break
    raise BackendUnavailable(f"{method} {path}: {type(last).__name__}")


def _inproc_call(method, path, query, payload, headers):
    ev = {"rawPath": path, "queryStringParameters": {k: str(v) for k, v in (query or {}).items()} or None,
          "headers": headers, "body": json.dumps(payload) if payload is not None else None,
          "requestContext": {"http": {"method": method}, "authorizer": {"iam": {
              "userArn": "arn:aws:sts::000000000000:assumed-role/connect-atv-orchestrator-role/inproc"}}}}
    r = _inproc().handler(ev)
    return r["statusCode"], json.loads(r["body"])


def call(method, path, query=None, body=None, sid=None, idem=None, ok=(200,)):
    headers = {}
    if sid:
        headers["x-sandbox-id"] = sid
    if idem:
        headers["idempotency-key"] = idem
    t0 = time.time()
    try:
        if _base():
            st, js = _http(method, path, query, body, headers)
        elif os.environ.get("FV_STORE") == "memory":
            st, js = _inproc_call(method, path, query, body, headers)
        else:
            raise BackendUnavailable("FV_FARMAENLACE_URL no configurada")
    finally:
        ms = int((time.time() - t0) * 1000)
        STATS["fe_calls"] = STATS.get("fe_calls", 0) + 1
        STATS["fe_ms"] = STATS.get("fe_ms", 0) + ms
    if st == 404 and 404 not in ok:
        raise NotFound(path)
    if st not in ok:
        raise BackendUnavailable(f"{method} {path} -> {st} {(js.get('error') or {}).get('code', '')}")
    return st, js


def _cached(key, ttl, fn):
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    try:
        v = fn()
    except BackendUnavailable:
        if hit:  # datos maestros: caché vencida mejor que nada
            return hit[1]
        raise
    _CACHE[key] = (time.time(), v)
    return v


# ---------- seed (la mock se siembra sola en su deploy; aquí solo en tests/local) ----------
def seed(store=None):
    _CACHE.clear()
    if not _base() and os.environ.get("FV_STORE") == "memory":
        return _inproc().seed()
    return call("GET", "/health")[1]


# ---------- Catálogo ----------
def catalog():
    return _cached("cat", TTL_MASTER, lambda: {p["sku"]: p for p in call("GET", "/catalogo/productos")[1]["items"]})


def product(sku):
    return catalog().get(str(sku or ""))


def search_products(terms, include_rx=True, limit=6):
    """Búsqueda en el catálogo de Farmaenlace (GET /catalogo/productos?q=)."""
    q = " ".join(str(t) for t in (terms or []) if t)
    if not q.strip():
        return []
    items = call("GET", "/catalogo/productos", {"q": q, "incluir_receta": str(bool(include_rx)).lower(),
                                                 "limit": limit})[1]["items"]
    for p in items:
        p.pop("score", None)
    return items


# ---------- Farmacias / Inventario ----------
def pharmacies():
    phs = _cached("ph", TTL_MASTER, lambda: call("GET", "/farmacias")[1]["items"])
    inv = _cached("inv", TTL_STOCK, lambda: call("GET", "/inventario")[1]["stock"])
    return [dict(p, stock=inv.get(p["pharmacyId"], {})) for p in phs]


def pharmacy(pid):
    return next((p for p in pharmacies() if p["pharmacyId"] == pid), None)


def distance_label(m):
    return f"{m} m" if m < 1000 else f"{m / 1000:.1f} km".replace(".", ",")


def has_stock(ph, cart):
    return all(ph["stock"].get(i["sku"], 0) >= i["qty"] for i in cart)


def pharmacies_with_stock(cart, limit=3):
    return [p for p in pharmacies() if has_stock(p, cart)][:limit]


def nearest_with(skus):
    phs = pharmacies()
    for p in phs:
        if all(p["stock"].get(s, 0) > 0 for s in skus):
            return p
    return phs[0]


# ---------- CRM (sandbox por sesión de demo: header X-Sandbox-Id) ----------
def get_profile(sid, cedula):
    try:
        return call("GET", f"/crm/clientes/{cedula}", sid=sid)[1]["cliente"], False
    except NotFound:
        pass
    st, js = call("POST", "/crm/clientes", body={"cedula": cedula}, sid=sid, ok=(201, 409))
    if st == 409:  # carrera / reintento: ya existe
        return call("GET", f"/crm/clientes/{cedula}", sid=sid)[1]["cliente"], False
    return js, True


def save_profile(sid, p):
    call("PUT", f"/crm/clientes/{p['cedula']}", body=p, sid=sid)


def public_customer(p):
    """Lo único del CRM que puede ver el cliente o el LLM. Sin condiciones probables, jamás."""
    if not p:
        return {"consent": False}
    consent = bool((p.get("consent") or {}).get("value"))
    out = {"name": p.get("name") or "", "consent": consent}
    if consent:
        out["archetype"] = p.get("archetype")
        out["frequent_products"] = [{"name": f["name"], "ritmo": f["ritmo"]} for f in p.get("frequent_products", [])]
    return out


def ui_hints(p):
    if p and (p.get("consent") or {}).get("value"):
        return p.get("ui_hints") or {}
    return {}


def due_reposicion(p):
    if not p or not (p.get("consent") or {}).get("value"):
        return None
    for f in p.get("frequent_products", []):
        if f["ritmo_dias"] - f["ultima_compra_hace_dias"] <= 3:
            return f
    return None


def personalized_filter(products, p):
    """Las condiciones probables SOLO filtran sugerencias (server-side, con consentimiento)."""
    if not p or not (p.get("consent") or {}).get("value"):
        return products
    cond = set(p.get("condiciones_probables") or [])
    return [x for x in products if not cond & set(x.get("contraindica") or [])]


# ---------- SmartClub / Promociones ----------
def ensure_coupon(sid, cedula, qr="BIENVENIDA"):
    return call("POST", f"/smartclub/{cedula}/cupones", body={"qr": qr or "BIENVENIDA"}, sid=sid)[1]


def get_coupon(sid, cedula):
    if not cedula:
        return None
    try:
        return call("GET", f"/smartclub/{cedula}", sid=sid)[1].get("cupon")
    except NotFound:
        return None


# ---------- Pricing (vista del carrito; el precio que vale es el que calcula POST /pedidos) ----------
def price_cart(cart, coupon=None):
    lines, sub, iva, cb, has_repo = [], 0.0, 0.0, 0.0, False
    for it in cart:
        p = product(it["sku"])
        if not p:
            continue
        qty = max(1, min(int(it.get("qty", 1)), 10))
        line = r2(p["price"] * qty)
        pct = p["cashback_pct"] * (2 if it.get("reposicion") else 1)
        has_repo = has_repo or bool(it.get("reposicion"))
        sub += line
        iva += line * p["iva"]
        cb += line * pct / 100
        lines.append({"sku": p["sku"], "name": p["name"], "qty": qty, "unit": p["price"], "line": line,
                      "price": money(line), "ivaRate": p["iva"], "cashbackPct": pct, "reposicion": bool(it.get("reposicion"))})
    sub, iva = r2(sub), r2(iva)
    gross = r2(sub + iva)
    disc = 0.0
    if coupon and coupon.get("status") == "disponible" and lines:
        disc = min(coupon["amount"], gross)
    total = r2(gross - disc)
    return {"lines": lines, "subtotal": sub, "iva": iva, "gross": gross, "discount": r2(disc), "total": total,
            "cashback": r2(cb), "double_cashback": has_repo,
            "coupon_code": coupon["code"] if disc else None}


def cart_view(pr):
    return {"items": [{"name": l["name"], "qty": l["qty"], "price": l["price"]} for l in pr["lines"]],
            "subtotal": money(pr["subtotal"]), "iva": money(pr["iva"]), "total": money(pr["total"]),
            "cashback": money(pr["cashback"]) + (" (doble por reposición)" if pr["double_cashback"] else ""),
            "coupon": (f"{pr['coupon_code']} −{money(pr['discount'])}" if pr["coupon_code"] else None)}


# ---------- Pedidos + Facturación ----------
def idem_key(sid, cart, pharmacy_id, last_order=None):
    raw = json.dumps([sorted((i["sku"], int(i.get("qty", 1)), bool(i.get("reposicion"))) for i in cart), pharmacy_id, last_order])
    return hashlib.sha256((sid + raw).encode()).hexdigest()[:16]


def reserve(sid, session, profile, billing, expected_rev, session_put):
    """POST /pedidos (Idempotency-Key) → Farmaenlace crea pedido + factura mock + cupón usado + CRM (su transacción).
    Luego el orquestador avanza su sesión con escritura condicional por revisión.
    Idempotente por (sesión, carrito, farmacia, último pedido): un doble toque devuelve el mismo pedido.
    """
    key = idem_key(sid, session["cart"], session["pharmacyId"], session.get("lastOrder"))
    body = {"cedula": profile["cedula"], "pharmacyId": session["pharmacyId"],
            "items": [{"sku": i["sku"], "qty": int(i.get("qty", 1)), "reposicion": bool(i.get("reposicion"))}
                      for i in session["cart"]],
            "billing": {k: billing.get(k) for k in ("tipo", "nombre", "identificacion", "tipoId", "email")}}
    st, res = call("POST", "/pedidos", body=body, sid=sid, idem=key, ok=(200, 201))
    res.pop("replay", None)
    if st == 200:
        return res, False
    session_doc, cond, attrs = session_put(res)
    try:
        get_store().put("SES#" + sid, "META", session_doc, cond=cond, attrs=attrs)
    except ConditionFailed:
        return res, False  # otra petición ya avanzó la sesión; el pedido es el mismo (idempotente)
    return res, True


def reset_sandbox(sid):
    call("DELETE", "/sandbox", sid=sid)


# ---------- Admin (solo lectura) ----------
def admin_list(service, show_internal=False):
    if service == "catalogo":
        return list(catalog().values())
    if service == "farmacias":
        return [{k: v for k, v in p.items() if k != "stock"} for p in pharmacies()]
    if service == "inventario":
        return [{"pharmacyId": p["pharmacyId"], "sku": k, "stock": v} for p in pharmacies() for k, v in sorted(p["stock"].items())]
    if service in ("crm", "smartclub", "pedidos", "facturacion"):
        q = {"interno": "1"} if show_internal else None
        return call("GET", f"/admin/{service}", q)[1]["items"]
    return None


def log(entry):
    now = time.time()
    day = datetime.now(EC_TZ).strftime("%Y-%m-%d")
    try:
        get_store().put("LOG#" + day, f"{int(now * 1000)}#{random.randint(0, 9999):04d}",
                        dict(entry, ts=datetime.now(EC_TZ).isoformat(timespec="seconds")), attrs={"ttl": int(now) + 3 * 86400})
    except Exception:  # noqa: BLE001 — log nunca rompe un turno
        pass


def recent_logs(limit=100):
    day = datetime.now(EC_TZ).strftime("%Y-%m-%d")
    return get_store().query("LOG#" + day, "", desc=True, limit=limit)
