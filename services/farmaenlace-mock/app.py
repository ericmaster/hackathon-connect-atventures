"""Lambda `connect-atv-farmaenlace-mock`: simulación del backend de Farmaenlace (7 servicios) detrás de un
API Gateway HTTP API con auth AWS_IAM. Tabla propia `connect-atv-farmaenlace` (pk/sk, doc JSON).

Rutas: ver README.md / openapi.yaml. Datos por sesión de demo aislados con el header `X-Sandbox-Id`
(pk SBX#<id>); datos maestros (catálogo, farmacias, inventario, seeds CRM, promos) globales y de solo lectura.
Todo es sintético; precios referenciales (mock).
"""
import base64
import copy
import json
import math
import os
import random
import re
import time
import unicodedata
from datetime import datetime, timedelta, timezone

import data
from store import ConditionFailed, get_store

EC_TZ = timezone(timedelta(hours=-5))
ALLOWED_ROLES = [r for r in os.environ.get("FM_ALLOWED_ROLES", "connect-atv-orchestrator-role").split(",") if r]
_CACHE = {}


class HttpError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def r2(x):
    return round(x + 1e-9, 2)


def money(x):
    return "$" + f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def now_ec():
    return datetime.now(EC_TZ)


def sbx(sid):
    if not sid or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", sid):
        raise HttpError(400, "sandbox_required", "Header X-Sandbox-Id requerido")
    return "SBX#" + sid


# ---------------------------------------------------------------- seed
def seed():
    s = get_store()
    for p in data.PRODUCTS:
        s.put("CAT", "P#" + p["sku"], p)
    for ph in data.PHARMACIES:
        s.put("PHARM", "PH#" + ph["pharmacyId"], {k: v for k, v in ph.items() if k != "stock"})
        for sku, q in ph["stock"].items():
            s.put("INV#" + ph["pharmacyId"], "SKU#" + sku, {"pharmacyId": ph["pharmacyId"], "sku": sku, "stock": q})
    for pr in data.PROFILES:
        s.put("SEED", "CRM#" + pr["cedula"], pr)
    for k, c in data.COUPONS.items():
        s.put("PROMO", "CPNDEF#" + k, dict(c, qr=k))
    for p in data.PROMOS:
        s.put("PROMO", "PROMO#" + p["id"], p)
    _CACHE.clear()
    return {"products": len(data.PRODUCTS), "pharmacies": len(data.PHARMACIES), "profiles": len(data.PROFILES),
            "stock_rows": sum(len(p["stock"]) for p in data.PHARMACIES)}


def _cached(key, ttl, fn):
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    v = fn()
    _CACHE[key] = (time.time(), v)
    return v


# ---------------------------------------------------------------- Catálogo
def catalog():
    return _cached("cat", 60, lambda: {p["sku"]: p for p in get_store().query("CAT", "P#")})


def _norm(t):
    t = unicodedata.normalize("NFD", str(t).lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


STOP = set("para algo tienen tiene quiero necesito tengo como unos unas los las del con por mejor favor busco hay venden "
           "dame deme puede puedes ayuda ayudame que cual cuanto cuesta mucho poco estoy esta este esto eso alguna alguno "
           "buenas buenos dias tardes noches hola gracias sirve sirva tomar tomo".split())


def search_products(q, include_rx=True, limit=6):
    words = set()
    for w in _norm(q).replace(",", " ").split():
        if len(w) >= 3 and w not in STOP:
            words.add(w)
            if w.endswith("s") and len(w) > 4:
                words.add(w[:-1])
    scored = []
    for p in catalog().values():
        if p.get("requiere_receta") and not include_rx:
            continue
        hay = set(p["tags"]) | set(_norm(p["name"]).split())
        sc = sum(1 for w in words if w in hay or (len(w) >= 5 and any(h.startswith(w) for h in hay)))
        if sc:
            scored.append((sc, p["sku"], p))
    scored.sort(key=lambda x: (-x[0], -x[2].get("boost", 0), x[1]))
    return [dict(copy.deepcopy(p), score=sc) for sc, _, p in scored[:limit]]


# ---------------------------------------------------------------- Farmacias / Inventario
def _haversine_m(lat1, lng1, lat2, lng2):
    r = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return int(round(2 * r * math.asin(math.sqrt(a)), -1))


def pharmacies(lat=None, lng=None):
    base = _cached("ph", 60, lambda: get_store().query("PHARM", "PH#"))
    lat = data.DEMO_LAT if lat is None else lat
    lng = data.DEMO_LNG if lng is None else lng
    out = []
    for p in base:
        p = dict(p, distance_m=_haversine_m(lat, lng, p["lat"], p["lng"]),
                 mapsUrl=f"https://maps.google.com/?q={p['lat']},{p['lng']}")
        out.append(p)
    return sorted(out, key=lambda x: x["distance_m"])


def stock_matrix(pharmacy_ids=None, skus=None):
    def load():
        m = {}
        for p in get_store().query("PHARM", "PH#"):
            m[p["pharmacyId"]] = {r["sku"]: r["stock"] for r in get_store().query("INV#" + p["pharmacyId"], "SKU#")}
        return m
    m = _cached("inv", 15, load)
    out = {}
    for pid, st in m.items():
        if pharmacy_ids and pid not in pharmacy_ids:
            continue
        out[pid] = {k: v for k, v in st.items() if not skus or k in skus}
    return out


# ---------------------------------------------------------------- CRM
def get_customer(sid, cedula):
    s = get_store()
    p = s.get(sbx(sid), "CRM#" + cedula)
    if p:
        return p, "sandbox"
    seedp = s.get("SEED", "CRM#" + cedula)
    if not seedp:
        return None, None
    seedp["created_at"] = now_ec().isoformat(timespec="seconds")
    s.put(sbx(sid), "CRM#" + cedula, seedp)  # copia de trabajo por sesión de demo
    return seedp, "seed"


def create_customer(sid, body):
    ced = str(body.get("cedula") or "")
    if not re.fullmatch(r"\d{10}", ced):
        raise HttpError(400, "bad_request", "cedula inválida")
    if get_customer(sid, ced)[0]:
        raise HttpError(409, "conflict", "cliente ya existe")
    p = {"cedula": ced, "name": body.get("name"), "archetype": None, "ui_hints": {}, "frequent_products": [],
         "condiciones_probables": [], "farmacia_habitual": None, "preferencias": {},
         "consent": None, "billing": None, "smartclub": {"socio": True, "cashback_saldo": 0.0},
         "nuevo": True, "created_at": now_ec().isoformat(timespec="seconds")}
    get_store().put(sbx(sid), "CRM#" + ced, p)
    return p


def put_customer(sid, cedula, body):
    if str(body.get("cedula")) != cedula:
        raise HttpError(400, "bad_request", "cedula no coincide")
    get_store().put(sbx(sid), "CRM#" + cedula, body)
    return body


# ---------------------------------------------------------------- SmartClub
def get_coupon(sid, cedula):
    return get_store().get(sbx(sid), "CPN#" + cedula)


def ensure_coupon(sid, cedula, qr="BIENVENIDA"):
    s = get_store()
    cur = s.get(sbx(sid), "CPN#" + cedula)
    if cur:
        return cur
    d = s.get("PROMO", "CPNDEF#" + (qr or "BIENVENIDA")) or s.get("PROMO", "CPNDEF#BIENVENIDA") or \
        dict(data.COUPONS["BIENVENIDA"], qr="BIENVENIDA")
    c = dict(d, cedula=cedula, status="disponible")
    s.put(sbx(sid), "CPN#" + cedula, c, attrs={"status": "disponible"})
    return c


def smartclub(sid, cedula):
    p, _ = get_customer(sid, cedula)
    if not p:
        raise HttpError(404, "not_found", "cliente no existe")
    sc = p.get("smartclub") or {}
    return {"cedula": cedula, "socio": bool(sc.get("socio")), "cashback_saldo": sc.get("cashback_saldo", 0.0),
            "cupon": get_coupon(sid, cedula), "promociones": get_store().query("PROMO", "PROMO#")}


# ---------------------------------------------------------------- Pricing (servidor de Farmaenlace)
def price_cart(cart, coupon=None):
    lines, sub, iva, cb, has_repo = [], 0.0, 0.0, 0.0, False
    cat = catalog()
    for it in cart:
        p = cat.get(str(it.get("sku") or ""))
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
            "cashback": r2(cb), "double_cashback": has_repo, "coupon_code": coupon["code"] if disc else None}


# ---------------------------------------------------------------- Facturación (forma SRI, MOCK)
def _mod11(digits):
    f, s = 2, 0
    for d in reversed(digits):
        s += int(d) * f
        f = 2 if f == 7 else f + 1
    v = 11 - s % 11
    return "0" if v == 11 else "1" if v == 10 else str(v)


def build_invoice(sid, order_no, pr, billing, now):
    e = data.EMISOR
    sec = f"{random.randint(1, 999999999):09d}"
    inv_no = f"{e['estab']}-{e['ptoEmi']}-{sec}"
    cf = billing.get("tipo") == "consumidor_final"
    tipo_id = "07" if cf else billing.get("tipoId", "05")
    base = now.strftime("%d%m%Y") + "01" + e["ruc"] + "1" + e["estab"] + e["ptoEmi"] + sec + f"{random.randint(0, 99999999):08d}" + "1"
    clave = base + _mod11(base)
    base0 = r2(sum(l["line"] for l in pr["lines"] if not l["ivaRate"]))
    base15 = r2(sum(l["line"] for l in pr["lines"] if l["ivaRate"]))
    impuestos = [x for x in (
        {"codigo": "2", "codigoPorcentaje": "0", "tarifa": 0, "baseImponible": base0, "valor": 0.0} if base0 else None,
        {"codigo": "2", "codigoPorcentaje": "4", "tarifa": 15, "baseImponible": base15, "valor": pr["iva"]} if base15 else None) if x]
    return {
        # Forma usada por la PWA (CONTRACT.md, sin cambios)
        "number": inv_no, "label": "SIMULADA", "orderNumber": order_no,
        "customerName": "CONSUMIDOR FINAL" if cf else billing["nombre"],
        "customerId": "9999999999999" if cf else billing["identificacion"],
        "tipoIdentificacion": tipo_id, "email": billing["email"],
        "items": [{"name": l["name"], "qty": l["qty"], "price": l["price"]} for l in pr["lines"]],
        "subtotal": money(pr["subtotal"]), "iva": money(pr["iva"]),
        "discount": money(pr["discount"]), "total": money(pr["total"]),
        "issuedAt": now.isoformat(timespec="seconds"), "sessionId": sid,
        # Campos con forma SRI (ficha técnica offline v2.34 / XSD factura v2.1.0) — MOCK, NO transmitida al SRI
        "sri": {
            "estado": "SIMULADA_NO_TRANSMITIDA", "ambiente": "1", "tipoEmision": "1", "codDoc": "01",
            "infoTributaria": {"ruc": e["ruc"], "razonSocial": e["razonSocial"], "estab": e["estab"],
                               "ptoEmi": e["ptoEmi"], "secuencial": sec, "claveAcceso": clave},
            "infoFactura": {"fechaEmision": now.strftime("%d/%m/%Y"), "tipoIdentificacionComprador": tipo_id,
                            "razonSocialComprador": "CONSUMIDOR FINAL" if cf else billing["nombre"],
                            "identificacionComprador": "9999999999999" if cf else billing["identificacion"],
                            "totalSinImpuestos": pr["subtotal"], "totalDescuento": pr["discount"],
                            "totalConImpuestos": impuestos, "importeTotal": pr["total"], "moneda": "DOLAR",
                            "pagos": [{"formaPago": "01", "total": pr["total"]}]},
            "detalles": [{"codigoPrincipal": l["sku"], "descripcion": l["name"], "cantidad": l["qty"],
                          "precioUnitario": l["unit"], "descuento": 0.0, "precioTotalSinImpuesto": l["line"],
                          "impuestos": [{"codigo": "2", "codigoPorcentaje": "4" if l["ivaRate"] else "0",
                                         "tarifa": 15 if l["ivaRate"] else 0, "baseImponible": l["line"],
                                         "valor": r2(l["line"] * l["ivaRate"])}]} for l in pr["lines"]],
            "infoAdicional": [{"nombre": "Email", "valor": billing["email"]}],
        },
    }


def issue_invoice(sid, body):
    """POST /facturacion/comprobantes (independiente): body {orderNumber?, items[{sku,qty}], billing}."""
    billing = body.get("billing") or {}
    if not billing.get("email"):
        raise HttpError(400, "bad_request", "billing.email obligatorio")
    pr = price_cart(body.get("items") or [])
    if not pr["lines"]:
        raise HttpError(400, "bad_request", "items vacíos")
    if billing.get("tipo") == "consumidor_final" and pr["total"] > 50:
        raise HttpError(422, "consumidor_final_tope", "Consumidor final solo hasta USD 50")
    inv = build_invoice(sid, body.get("orderNumber") or "", pr, billing, now_ec())
    get_store().put(sbx(sid), "FAC#" + inv["number"], inv, cond="not_exists")
    return inv


# ---------------------------------------------------------------- Pedidos (reserva idempotente)
def create_order(sid, body, idem):
    if not idem or not re.fullmatch(r"[A-Za-z0-9_-]{8,64}", idem):
        raise HttpError(400, "idempotency_key_required", "Header Idempotency-Key requerido")
    s = get_store()
    prev = s.get(sbx(sid), "IDEM#" + idem)
    if prev:
        return prev, False
    ced = str(body.get("cedula") or "")
    profile, _ = get_customer(sid, ced)
    if not profile:
        raise HttpError(404, "not_found", "cliente no existe")
    billing = body.get("billing") or {}
    if not billing.get("email"):
        raise HttpError(400, "bad_request", "billing.email obligatorio")
    ph = next((p for p in pharmacies() if p["pharmacyId"] == body.get("pharmacyId")), None)
    if not ph:
        raise HttpError(404, "not_found", "farmacia no existe")
    coupon = get_coupon(sid, ced)
    pr = price_cart(body.get("items") or [], coupon)
    if not pr["lines"]:
        raise HttpError(400, "bad_request", "carrito vacío")
    now = now_ec()
    order_no = "FV-" + str(random.randint(100000, 999999))
    invoice = build_invoice(sid, order_no, pr, billing, now)
    inv_no = invoice["number"]
    order = {"orderNumber": order_no, "status": "reservado_pago_al_retirar", "pharmacyId": ph["pharmacyId"],
             "pharmacy": ph["name"], "pickupTime": "Hoy desde las " + (now + timedelta(minutes=30)).strftime("%H:%M"),
             "qrValue": f"FVPICKUP:{order_no}", "cedula": ced, "lines": pr["lines"],
             "totals": {k: pr[k] for k in ("subtotal", "iva", "discount", "total", "cashback")},
             "coupon": pr["coupon_code"], "invoice": inv_no, "createdAt": now.isoformat(timespec="seconds"),
             "sessionId": sid, "idempotencyKey": idem}
    result = {"order": order, "invoice": invoice, "pricing": pr,
              "coupon": (dict(coupon, status="usado") if pr["coupon_code"] else None)}
    prof = copy.deepcopy(profile)
    prof["billing"] = {k: billing.get(k) for k in ("tipo", "nombre", "identificacion", "tipoId", "email")}
    sc = prof.setdefault("smartclub", {"socio": True, "cashback_saldo": 0.0})
    sc["cashback_saldo"] = r2(float(sc.get("cashback_saldo", 0)) + pr["cashback"])
    for l in pr["lines"]:
        for f in prof.get("frequent_products", []):
            if f["sku"] == l["sku"]:
                f["ultima_compra_hace_dias"] = 0
    ops = [(sbx(sid), "IDEM#" + idem, result, "not_exists", None),
           (sbx(sid), "ORD#" + order_no, order, "not_exists", None),
           (sbx(sid), "FAC#" + inv_no, invoice, "not_exists", None),
           (sbx(sid), "CRM#" + ced, prof, None, None)]
    if pr["coupon_code"]:
        ops.append((sbx(sid), "CPN#" + ced, dict(coupon, status="usado", order=order_no),
                    ("status", "disponible"), {"status": "usado"}))
    try:
        s.transact(ops)
    except ConditionFailed:
        prev = s.get(sbx(sid), "IDEM#" + idem)
        if prev:
            return prev, False
        raise HttpError(409, "conflict", "conflicto al reservar (cupón ya usado o pedido duplicado)")
    return result, True


# ---------------------------------------------------------------- Admin (solo lectura)
def admin_list(service, show_internal=False):
    s = get_store()
    if service == "catalogo":
        return list(catalog().values())
    if service == "farmacias":
        return pharmacies()
    if service == "inventario":
        return [{"pharmacyId": pid, "sku": k, "stock": v} for pid, st in stock_matrix().items() for k, v in sorted(st.items())]
    if service == "crm":
        items = [dict(x, _pk="SEED") for x in s.query("SEED", "CRM#")] + s.scan_prefix("CRM#")
        seen, out = set(), []
        for x in items:
            k = (x.get("_pk"), x.get("cedula"))
            if k in seen:
                continue
            seen.add(k)
            x = dict(x)
            cond = x.pop("condiciones_probables", None)
            if show_internal:
                x["condiciones_probables_interno"] = cond or []
            elif cond is not None:
                x["condiciones_probables"] = "[oculto: dato sensible, solo filtra sugerencias]"
            out.append(x)
        return out
    if service == "smartclub":
        return s.query("PROMO", "CPNDEF#") + s.query("PROMO", "PROMO#") + s.scan_prefix("CPN#")
    if service == "pedidos":
        return s.scan_prefix("ORD#")
    if service == "facturacion":
        return s.scan_prefix("FAC#")
    raise HttpError(404, "not_found", "servicio desconocido")


# ---------------------------------------------------------------- router
def _f(q, k):
    try:
        return float(q[k]) if q.get(k) not in (None, "") else None
    except ValueError:
        raise HttpError(400, "bad_request", f"{k} inválido")


def route(method, path, q, body, headers):
    sid = headers.get("x-sandbox-id")
    parts = [p for p in path.split("/") if p]
    if method == "GET" and parts == ["health"]:
        return 200, {"ok": True, "service": "farmaenlace-mock", "products": len(catalog())}
    # Catálogo
    if method == "GET" and parts == ["catalogo", "productos"]:
        rx = str(q.get("incluir_receta", "true")).lower() != "false"
        if q.get("q"):
            items = search_products(q["q"], include_rx=rx, limit=max(1, min(int(q.get("limit") or 6), 50)))
        else:
            items = [p for p in catalog().values() if rx or not p.get("requiere_receta")]
        return 200, {"items": items, "count": len(items)}
    if method == "GET" and len(parts) == 3 and parts[:2] == ["catalogo", "productos"]:
        p = catalog().get(parts[2])
        return (200, p) if p else (404, {"error": {"code": "not_found", "message": "producto no existe"}})
    # Farmacias
    if method == "GET" and parts == ["farmacias"]:
        items = pharmacies(_f(q, "lat"), _f(q, "lng"))
        return 200, {"items": items, "count": len(items)}
    if method == "GET" and len(parts) == 2 and parts[0] == "farmacias":
        p = next((x for x in pharmacies(_f(q, "lat"), _f(q, "lng")) if x["pharmacyId"] == parts[1]), None)
        return (200, p) if p else (404, {"error": {"code": "not_found", "message": "farmacia no existe"}})
    # Inventario
    if method == "GET" and parts == ["inventario"]:
        skus = [x for x in (q.get("skus") or "").split(",") if x]
        return 200, {"stock": stock_matrix(skus=skus or None)}
    if method == "GET" and len(parts) in (2, 3) and parts[0] == "inventario":
        m = stock_matrix([parts[1]])
        if parts[1] not in m:
            return 404, {"error": {"code": "not_found", "message": "farmacia no existe"}}
        if len(parts) == 2:
            return 200, {"pharmacyId": parts[1], "stock": m[parts[1]]}
        return 200, {"pharmacyId": parts[1], "sku": parts[2], "stock": m[parts[1]].get(parts[2], 0)}
    # CRM
    if parts[:2] == ["crm", "clientes"]:
        if method == "POST" and len(parts) == 2:
            return 201, create_customer(sid, body)
        if len(parts) == 3:
            if method == "GET":
                p, origen = get_customer(sid, parts[2])
                return (200, {"cliente": p, "origen": origen}) if p else \
                    (404, {"error": {"code": "not_found", "message": "cliente no existe"}})
            if method == "PUT":
                return 200, put_customer(sid, parts[2], body)
    # SmartClub
    if parts[:1] == ["smartclub"] and len(parts) >= 2:
        if method == "GET" and len(parts) == 2:
            return 200, smartclub(sid, parts[1])
        if method == "POST" and len(parts) == 3 and parts[2] == "cupones":
            return 200, ensure_coupon(sid, parts[1], body.get("qr") or "BIENVENIDA")
    # Pedidos
    if method == "POST" and parts == ["pedidos"]:
        res, created = create_order(sid, body, headers.get("idempotency-key"))
        return (201 if created else 200), dict(res, replay=not created)
    if method == "GET" and len(parts) == 2 and parts[0] == "pedidos":
        o = get_store().get(sbx(sid), "ORD#" + parts[1])
        return (200, o) if o else (404, {"error": {"code": "not_found", "message": "pedido no existe"}})
    # Facturación
    if method == "POST" and parts == ["facturacion", "comprobantes"]:
        return 201, issue_invoice(sid, body)
    if method == "GET" and len(parts) == 3 and parts[:2] == ["facturacion", "comprobantes"]:
        f = get_store().get(sbx(sid), "FAC#" + parts[2])
        return (200, f) if f else (404, {"error": {"code": "not_found", "message": "comprobante no existe"}})
    # Sandbox de demo
    if method == "DELETE" and parts == ["sandbox"]:
        get_store().delete_pk(sbx(sid))
        return 200, {"ok": True}
    # Admin
    if method == "GET" and len(parts) == 2 and parts[0] == "admin":
        items = admin_list(parts[1], str(q.get("interno")) == "1")
        return 200, {"service": parts[1], "items": items, "count": len(items)}
    return 404, {"error": {"code": "not_found", "message": f"{method} /{'/'.join(parts)}"}}


def _authorized(event):
    """Defensa en profundidad además de AWS_IAM: solo roles permitidos (el del orquestador)."""
    iam = ((event.get("requestContext") or {}).get("authorizer") or {}).get("iam") or {}
    arn = iam.get("userArn") or ""
    m = re.search(r":assumed-role/([^/]+)/", arn)
    return bool(m and m.group(1) in ALLOWED_ROLES)


def handler(event, context=None):
    t0 = time.time()
    if "requestContext" not in event:  # invocación directa (solo operador): seed / health
        if event.get("route") == "POST /internal/seed":
            return seed()
        method, path = (event.get("route") or "GET /health").split(" ", 1)
        st, b = route(method, path, event.get("query") or {}, event.get("body") or {},
                      {k.lower(): v for k, v in (event.get("headers") or {}).items()})
        return dict(b, _status=st)
    if not _authorized(event):
        st, b = 403, {"error": {"code": "forbidden", "message": "rol no autorizado"}}
    else:
        try:
            method = event["requestContext"]["http"]["method"].upper()
            raw = event.get("body") or ""
            if event.get("isBase64Encoded"):
                raw = base64.b64decode(raw).decode()
            body = json.loads(raw) if raw else {}
            headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
            st, b = route(method, event.get("rawPath") or "/", event.get("queryStringParameters") or {}, body, headers)
        except HttpError as e:
            st, b = e.status, {"error": {"code": e.code, "message": e.message}}
        except json.JSONDecodeError:
            st, b = 400, {"error": {"code": "bad_request", "message": "JSON inválido"}}
        except Exception as e:  # noqa: BLE001
            print("ERROR", type(e).__name__, repr(e)[:500])
            st, b = 500, {"error": {"code": "internal", "message": type(e).__name__}}
    ms = int((time.time() - t0) * 1000)
    print(json.dumps({"path": event.get("rawPath"), "method": (event.get("requestContext", {}).get("http") or {}).get("method"),
                      "status": st, "ms": ms}))
    return {"statusCode": st, "headers": {"Content-Type": "application/json", "Cache-Control": "no-store",
                                          "X-Mock": "farmaenlace", "Server-Timing": f"app;dur={ms}"},
            "body": json.dumps(b, ensure_ascii=False)}
