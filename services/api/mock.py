"""Los 7 servicios mock (CRM, Catálogo, Inventario, Farmacias, SmartClub/Promociones, Pedidos, Facturación)
sobre la tabla única. Datos globales de solo lectura + sandbox por sesión (SBX#<sessionId>)."""
import copy
import hashlib
import json
import random
import time
from datetime import datetime, timedelta, timezone

import fixtures
from store import ConditionFailed, get_store

EC_TZ = timezone(timedelta(hours=-5))
_CACHE = {}


def money(x):
    return "$" + f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def r2(x):
    return round(x + 1e-9, 2)


# ---------- seed ----------
def seed(store=None):
    s = store or get_store()
    for p in fixtures.PRODUCTS:
        s.put("CAT", "P#" + p["sku"], p)
    for ph in fixtures.PHARMACIES:
        s.put("PHARM", "PH#" + ph["pharmacyId"], ph)
    for pr in fixtures.PROFILES:
        s.put("SEED", "CRM#" + pr["cedula"], pr)
    for k, c in fixtures.COUPONS.items():
        s.put("PROMO", "CPNDEF#" + k, dict(c, qr=k))
    for p in fixtures.PROMOS:
        s.put("PROMO", "PROMO#" + p["id"], p)
    _CACHE.clear()
    return {"products": len(fixtures.PRODUCTS), "pharmacies": len(fixtures.PHARMACIES), "profiles": len(fixtures.PROFILES)}


# ---------- Catálogo ----------
def catalog():
    if "cat" not in _CACHE:
        items = get_store().query("CAT", "P#") or copy.deepcopy(fixtures.PRODUCTS)
        _CACHE["cat"] = {p["sku"]: p for p in items}
    return _CACHE["cat"]


def product(sku):
    return catalog().get(str(sku or ""))


def _norm(t):
    import unicodedata
    t = unicodedata.normalize("NFD", str(t).lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def search_products(terms, include_rx=True, limit=6):
    """Búsqueda por tags/nombre. Devuelve productos ordenados por coincidencias."""
    words = set()
    for t in terms or []:
        for w in _norm(t).replace(",", " ").split():
            if len(w) >= 3:
                words.add(w)
                if w.endswith("s") and len(w) > 4:
                    words.add(w[:-1])
    scored = []
    for p in catalog().values():
        if p.get("requiere_receta") and not include_rx:
            continue
        hay = set(p["tags"]) | set(_norm(p["name"]).split())
        sc = sum(1 for w in words if w in hay or any(h.startswith(w) for h in hay if len(w) >= 4))
        if sc:
            scored.append((sc, p["sku"], p))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [copy.deepcopy(p) for _, _, p in scored[:limit]]


# ---------- Farmacias / Inventario ----------
def pharmacies():
    if "ph" not in _CACHE:
        items = get_store().query("PHARM", "PH#") or copy.deepcopy(fixtures.PHARMACIES)
        _CACHE["ph"] = sorted(items, key=lambda x: x["distance_m"])
    return _CACHE["ph"]


def pharmacy(pid):
    return next((p for p in pharmacies() if p["pharmacyId"] == pid), None)


def distance_label(m):
    return f"{m} m" if m < 1000 else f"{m / 1000:.1f} km".replace(".", ",")


def has_stock(ph, cart):
    return all(ph["stock"].get(i["sku"], 0) >= i["qty"] for i in cart)


def pharmacies_with_stock(cart, limit=3):
    return [p for p in pharmacies() if has_stock(p, cart)][:limit]


def nearest_with(skus):
    for p in pharmacies():
        if all(p["stock"].get(s, 0) > 0 for s in skus):
            return p
    return pharmacies()[0]


# ---------- CRM (sandbox por sesión) ----------
def sbx(sid):
    return "SBX#" + sid


def get_profile(sid, cedula):
    s = get_store()
    p = s.get(sbx(sid), "CRM#" + cedula)
    if p:
        return p, False
    seedp = s.get("SEED", "CRM#" + cedula)
    if not seedp:
        seedp = next((copy.deepcopy(x) for x in fixtures.PROFILES if x["cedula"] == cedula), None)
    created = seedp is None
    p = seedp or {"cedula": cedula, "name": None, "archetype": None, "ui_hints": {}, "frequent_products": [],
                  "condiciones_probables": [], "farmacia_habitual": None, "preferencias": {},
                  "consent": None, "billing": None, "smartclub": {"socio": True, "cashback_saldo": 0.0},
                  "nuevo": True}
    p["created_at"] = datetime.now(EC_TZ).isoformat(timespec="seconds")
    s.put(sbx(sid), "CRM#" + cedula, p)
    return p, created


def save_profile(sid, p):
    get_store().put(sbx(sid), "CRM#" + p["cedula"], p)


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
    s = get_store()
    cur = s.get(sbx(sid), "CPN#" + cedula)
    if cur:
        return cur
    d = s.get("PROMO", "CPNDEF#" + qr) or dict(fixtures.COUPONS["BIENVENIDA"], qr="BIENVENIDA")
    c = dict(d, cedula=cedula, status="disponible")
    s.put(sbx(sid), "CPN#" + cedula, c, attrs={"status": "disponible"})
    return c


def get_coupon(sid, cedula):
    return get_store().get(sbx(sid), "CPN#" + cedula) if cedula else None


# ---------- Pricing (siempre en servidor) ----------
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


# ---------- Pedidos + Facturación (transacción idempotente) ----------
def idem_key(sid, cart, pharmacy_id):
    raw = json.dumps([sorted((i["sku"], int(i.get("qty", 1)), bool(i.get("reposicion"))) for i in cart), pharmacy_id])
    return hashlib.sha256((sid + raw).encode()).hexdigest()[:16]


def reserve(sid, session, profile, billing, expected_rev, session_put):
    """Una transacción: pedido + factura mock + cupón usado + perfil (billing/cashback) + sesión (rev).

    Idempotente por (sesión, carrito, farmacia): un doble toque devuelve el mismo pedido.
    `session_put(session_doc)` -> (doc, cond, attrs) para la sesión.
    """
    s = get_store()
    key = idem_key(sid, session["cart"], session["pharmacyId"])
    prev = s.get(sbx(sid), "IDEM#" + key)
    if prev:
        return prev, False
    coupon = get_coupon(sid, profile["cedula"])
    pr = price_cart(session["cart"], coupon)
    ph = pharmacy(session["pharmacyId"])
    now = datetime.now(EC_TZ)
    order_no = "FV-" + str(random.randint(100000, 999999))
    inv_no = f"001-002-{random.randint(1, 999999):09d}"
    cf = billing.get("tipo") == "consumidor_final"
    invoice = {"number": inv_no, "label": "SIMULADA", "orderNumber": order_no,
               "customerName": "CONSUMIDOR FINAL" if cf else billing["nombre"],
               "customerId": "9999999999999" if cf else billing["identificacion"],
               "tipoIdentificacion": "07" if cf else billing.get("tipoId", "05"),
               "email": billing["email"],
               "items": [{"name": l["name"], "qty": l["qty"], "price": l["price"]} for l in pr["lines"]],
               "subtotal": money(pr["subtotal"]), "iva": money(pr["iva"]),
               "discount": money(pr["discount"]), "total": money(pr["total"]),
               "issuedAt": now.isoformat(timespec="seconds"), "sessionId": sid}
    order = {"orderNumber": order_no, "status": "reservado_pago_al_retirar", "pharmacyId": ph["pharmacyId"],
             "pharmacy": ph["name"], "pickupTime": "Hoy desde las " + (now + timedelta(minutes=30)).strftime("%H:%M"),
             "qrValue": f"FVPICKUP:{order_no}", "cedula": profile["cedula"], "lines": pr["lines"],
             "totals": {k: pr[k] for k in ("subtotal", "iva", "discount", "total", "cashback")},
             "coupon": pr["coupon_code"], "invoice": inv_no, "createdAt": now.isoformat(timespec="seconds"), "sessionId": sid}
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
    ops = [(sbx(sid), "IDEM#" + key, result, "not_exists", None),
           (sbx(sid), "ORD#" + order_no, order, "not_exists", None),
           (sbx(sid), "FAC#" + inv_no, invoice, "not_exists", None),
           (sbx(sid), "CRM#" + profile["cedula"], prof, None, None)]
    if pr["coupon_code"]:
        ops.append((sbx(sid), "CPN#" + profile["cedula"], dict(coupon, status="usado", order=order_no),
                    ("status", "disponible"), {"status": "usado"}))
    session_doc, cond, attrs = session_put(result)
    ops.append(("SES#" + sid, "META", session_doc, cond, attrs))
    try:
        s.transact(ops)
    except ConditionFailed:
        prev = s.get(sbx(sid), "IDEM#" + key)
        if prev:
            return prev, False
        raise
    return result, True


def reset_sandbox(sid):
    get_store().delete_pk(sbx(sid))


# ---------- Admin (solo lectura) ----------
def admin_list(service):
    s = get_store()
    if service == "catalogo":
        return list(catalog().values())
    if service == "farmacias":
        return [{k: v for k, v in p.items() if k != "stock"} for p in pharmacies()]
    if service == "inventario":
        return [{"pharmacyId": p["pharmacyId"], "sku": k, "stock": v} for p in pharmacies() for k, v in sorted(p["stock"].items())]
    if service == "crm":
        items = [dict(x, _pk="SEED") for x in s.query("SEED", "CRM#")] + s.scan_prefix("CRM#")
        seen, out = set(), []
        for x in items:
            k = (x.get("_pk"), x.get("cedula"))
            if k in seen:
                continue
            seen.add(k)
            x = dict(x)
            if x.pop("condiciones_probables", None) is not None:
                x["condiciones_probables"] = "[oculto: dato sensible, solo filtra sugerencias]"
            out.append(x)
        return out
    if service == "smartclub":
        return s.query("PROMO") + s.scan_prefix("CPN#")
    if service == "pedidos":
        return s.scan_prefix("ORD#")
    if service == "facturacion":
        return s.scan_prefix("FAC#")
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
