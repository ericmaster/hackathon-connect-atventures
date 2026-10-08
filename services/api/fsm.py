"""Orquestador: FSM del servidor + pipeline de turno libre + acciones confirmadas."""
import copy
import re
import time
import uuid
from datetime import datetime

import fixtures
import guardrails
import llm
import mock
import nlu
import templates as T
import validate
from cedula import extract_cedula, valid_cedula, valid_id
from store import ConditionFailed, get_store

STATES = ["saludo", "cedula", "consentimiento", "consulta", "productos", "farmacia", "resumen", "facturacion", "confirmacion"]
POST_ONBOARD = {"consulta", "productos", "farmacia", "resumen", "facturacion", "confirmacion"}
ACTIONS = {
    "enviar_cedula": {"cedula"},
    "consentimiento": {"consentimiento"},
    "agregar_pedido": {"consulta", "productos", "farmacia", "resumen", "confirmacion"},
    "reservar": {"consulta", "productos", "farmacia", "confirmacion"},
    "por_que": POST_ONBOARD,
    "seguir_comprando": POST_ONBOARD,
    "retirar_aqui": {"consulta", "productos", "farmacia", "resumen"},
    "confirmar_reserva": {"resumen", "facturacion"},
    "facturacion_tipo": {"facturacion"},
    "facturacion_dato": {"facturacion"},
    "handoff": set(STATES),
    "seguridad": {"consulta"},
}
NEEDS_CONFIRM = {"agregar_pedido", "reservar", "confirmar_reserva"}
COMMERCE = NEEDS_CONFIRM | {"retirar_aqui", "facturacion_tipo", "facturacion_dato"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$")
CF_LIMIT = 50.0
TURN_BUDGET_S = 25.0
TRACE = {}
SAFETY_NOTE = "Como mencionaste alergias u otros medicamentos, confírmalo con el farmacéutico antes de tomarlo."


class ApiError(Exception):
    def __init__(self, status, code, message, session=None):
        super().__init__(message)
        self.status, self.code, self.message, self.session = status, code, message, session


# ---------- sesión ----------
def load(sid, caller):
    s = get_store().get("SES#" + str(sid or ""), "META")
    if not s:
        raise ApiError(404, "not_found", "Sesión no encontrada")
    if caller != "direct" and s.get("owner") not in (caller, "direct"):
        raise ApiError(403, "forbidden", "La sesión pertenece a otra identidad")
    return s


def save(s, old_rev):
    try:
        get_store().put("SES#" + s["sessionId"], "META", s, cond=("rev", old_rev) if old_rev else "not_exists",
                        attrs={"rev": s["revision"]})
    except ConditionFailed as e:
        raise ApiError(409, "stale_revision", "La sesión cambió; vuelve a intentar", s) from e


def out(s, messages, spoken, mode="real"):
    if s.get("senior") and messages and isinstance(messages[0].get("createSurface"), dict):
        messages[0]["createSurface"]["theme"] = dict(messages[0]["createSurface"].get("theme") or {}, senior=True)
    return {"sessionId": s["sessionId"], "state": s["state"], "revision": s["revision"],
            "messages": messages, "spokenText": spoken, "mode": mode}


def step(s, state, builder, spoken, mode="real"):
    """Avanza revisión, construye la surface con la nueva revisión y guarda (lock optimista)."""
    old = s["revision"]
    s["revision"] = old + 1
    s["state"] = state
    msgs = builder(s["revision"])
    save(s, old)
    return out(s, msgs, spoken, mode)


def profile_of(s):
    return mock.get_profile(s["sessionId"], s["cedula"])[0] if s.get("cedula") else None


def coupon_def(qr):
    return fixtures.COUPONS.get(qr or "BIENVENIDA") or fixtures.COUPONS["BIENVENIDA"]


def fresh(sid, owner, qr, rev=0):
    return {"sessionId": sid, "owner": owner, "state": "saludo", "revision": rev, "qr": qr or "BIENVENIDA",
            "cedula": None, "attempts": 0, "cart": [], "pharmacyId": None, "billing": {}, "billing_pending": None,
            "billing_card": False, "blocked": False, "lastText": "", "lastProducts": [],
            "createdAt": datetime.now(mock.EC_TZ).isoformat(timespec="seconds")}


def create_session(caller, body):
    qr = (body or {}).get("qr") or "BIENVENIDA"
    if qr not in fixtures.COUPONS:
        qr = "BIENVENIDA"
    s = fresh("s_" + uuid.uuid4().hex[:16], caller, qr)
    s["state"], s["revision"] = "cedula", 1
    save(s, None)
    return out(s, T.cedula(1, coupon_def(qr)), "¡Hola! Soy tu Farmacéutico Virtual. ¿Me ayudas con tu número de cédula?")


def reset(caller, body):
    s = load(body.get("sessionId"), caller)
    mock.reset_sandbox(s["sessionId"])
    old = s["revision"]
    n = fresh(s["sessionId"], s["owner"], s.get("qr"), rev=old + 1)
    n["state"] = "cedula"
    save(n, old)
    return out(n, T.cedula(n["revision"], coupon_def(n["qr"])), "Empecemos de nuevo. ¿Me ayudas con tu número de cédula?")


# ---------- onboarding ----------
def do_cedula(s, ced):
    if not valid_cedula(ced):
        s["attempts"] = s.get("attempts", 0) + 1
        ph = mock.pharmacies()[0] if s["attempts"] >= 3 else None
        return step(s, "cedula", lambda r: T.cedula(r, None, "¿Me la repites? Revisa que tenga los 10 dígitos.", ph, greet=False),
                    "¿Me la repites? Revisa que tenga los 10 dígitos." + (" Si prefieres, te comunico con un farmacéutico." if ph else ""))
    s["cedula"], s["attempts"] = re.sub(r"\D", "", ced), 0
    p, created = mock.get_profile(s["sessionId"], s["cedula"])
    mock.ensure_coupon(s["sessionId"], s["cedula"], s.get("qr", "BIENVENIDA"))
    s["profileCreated"] = created
    if p.get("billing"):
        s["billing"] = copy.deepcopy(p["billing"])
    return step(s, "consentimiento", lambda r: T.consent(r, p.get("name")),
                "Gracias. ¿Aceptas que usemos tu historial de compras para darte sugerencias personalizadas?")


def do_consent(s, acepta):
    p = profile_of(s)
    p["consent"] = {"value": bool(acepta), "ts": datetime.now(mock.EC_TZ).isoformat(timespec="seconds")}
    mock.save_profile(s["sessionId"], p)
    s["senior"] = bool(acepta) and p.get("archetype") == "Cuidador"  # UI por arquetipo solo con consentimiento
    cust = mock.public_customer(p)
    coupon = mock.get_coupon(s["sessionId"], s["cedula"])
    repo = mock.due_reposicion(p)
    rp = mock.product(repo["sku"]) if repo else None
    ph = mock.pharmacy(p.get("farmacia_habitual")) if repo else None
    spoken = "¡Listo! Ya tienes tu beneficio."
    if rp:
        spoken += f" Sueles llevar tu {rp['name']} cada mes, ¿te lo reservo?"
    else:
        spoken += " ¿En qué te ayudo hoy?"
    return step(s, "consulta", lambda r: T.listo(r, cust, coupon, repo, rp, ph), spoken)


# ---------- turno libre ----------
def fmt_product(p, ph):
    st = ph["stock"].get(p["sku"], 0) if ph else 0
    return {"sku": p["sku"], "name": p["name"], "detail": p["detail"], "price": mock.money(p["price"]),
            "cashback": f"{p['cashback_pct']}% cashback · {mock.money(p['price'] * p['cashback_pct'] / 100)}",
            "stock": f"Hay stock a {mock.distance_label(ph['distance_m'])}" if st else "Consultar stock", "ventaLibre": True}


def fmt_pharmacy(ph, label="Tiene estos productos"):
    return {"pharmacyId": ph["pharmacyId"], "name": ph["name"], "distance": mock.distance_label(ph["distance_m"]),
            "hours": ph["hours"], "stock": label, "phone": ph["phone"], "mapsUrl": ph["mapsUrl"]}


def red_flag(s, mode):
    s["blocked"] = True
    ph = mock.pharmacies()[0]
    return step(s, "consulta", lambda r: T.alerta(r, ph),
                "Lo que describes puede ser una emergencia. Llama ahora al ECU 911 o acude a emergencias.", mode)


def handoff_resp(s, intro, mode="real"):
    p = profile_of(s)
    ph = mock.pharmacy((p or {}).get("farmacia_habitual")) or mock.pharmacies()[0]
    items = ", ".join(mock.product(i["sku"])["name"] for i in s.get("cart", []) if mock.product(i["sku"]))
    summary = f"Consulta: \"{s.get('lastText', '')[:120]}\"" + (f" · Pedido: {items}" if items else "")
    return step(s, s["state"] if s["state"] in POST_ONBOARD or s["state"] == "cedula" else "consulta",
                lambda r: T.handoff(r, ph, summary, intro), intro, mode)


def free_turn(s, text, deadline):
    n, info = nlu.gliner(text)
    mode = "real" if info["source"] == "gliner" else "simulado"
    g = guardrails.check_text(text, n)
    TRACE.update({"intent": n["intent"]["label"], "nlu": info["source"], "nlu_ms": info.get("ms"), "nlu_reason": info.get("reason"), "gliner_cold": info.get("cold")})
    if g["redFlag"]:
        return red_flag(s, mode)
    if g["handoff"]:
        return handoff_resp(s, "Te comunico con un farmacéutico de verdad.", mode)
    if g["diagnosis"]:
        return handoff_resp(s, "No puedo darte un diagnóstico, eso lo hace un médico. Sí puedo ayudarte con productos de venta libre "
                               "o comunicarte con un farmacéutico.", mode)
    if s.get("blocked"):  # tras una alarma no se vuelve a sugerir ni vender hasta Reiniciar
        return red_flag(s, mode)
    intent = n["intent"]["label"]
    p = profile_of(s)
    if intent == "checkout" and s.get("cart"):
        if s.get("pharmacyId"):
            return to_resumen(s)
        return to_pharmacies(s, None)
    if intent == "saludo" and not n.get("entities"):
        name = (mock.public_customer(p).get("name") or "") if p else ""
        return step(s, "consulta", lambda r: T.message(r, f"¡Hola{', ' + name if name else ''}! ¿En qué te ayudo? Cuéntame qué necesitas."),
                    "¡Hola! ¿En qué te ayudo?", mode)
    if intent == "farmacia_cercana" and not n.get("entities", {}).get("producto"):
        phs = mock.pharmacies_with_stock(s["cart"]) if s.get("cart") else mock.pharmacies()[:3]
        if s.get("cart"):
            return to_pharmacies(s, None)
        def b(r):
            sf = T.Surface(r)
            sf.text("t1", "Estas son las farmacias más cercanas (distancias sintéticas):", "h3")
            for i, ph in enumerate(phs):
                T.pharmacy_card(sf, f"ph{i + 1}", ph, "Abierta")
            return sf.messages()
        return step(s, s["state"], b, f"La más cercana es {phs[0]['name']}.", mode)

    terms = [e["text"] for k in ("sintoma", "producto") for e in n.get("entities", {}).get(k, [])] + [text]
    found = mock.search_products(terms, include_rx=True)
    if not found and s["state"] == "productos" and s.get("lastProducts") and REF_RE.search(guardrails.norm(text)):
        return follow_up(s, guardrails.norm(text), mode)
    rx = [x for x in found if x.get("requiere_receta")]
    otc = mock.personalized_filter(guardrails.otc_only(found), p)
    hints = mock.ui_hints(p)
    otc = otc[: int(hints.get("max_options") or 3)]
    if g["rx"] or (rx and not otc):
        return handoff_resp(s, "Ese medicamento necesita receta médica. Un farmacéutico te puede orientar.", mode)
    if otc and not s.get("safety"):
        # SPEC §7.2.2: una pregunta de seguridad por sesión antes de la primera sugerencia (plantilla, sin LLM).
        s["pending_query"] = text
        prac = (mock.public_customer(p).get("archetype") == "Práctico")
        return step(s, "consulta", lambda r: T.safety(r, prac), T.SAFETY_Q, mode)
    safety = s.get("safety") or {}
    if safety and not safety.get("ok"):
        # Excluye productos que la persona nombró en su respuesta (alergia / ya lo toma). Nunca se infiere condición.
        said = set(w for w in guardrails.norm(safety.get("answer", "")).split() if len(w) >= 5)
        otc = [x for x in otc if not said & (set(x["tags"]) | set(guardrails.norm(x["name"]).split()))] or []

    ph = mock.nearest_with([x["sku"] for x in otc]) if otc else mock.pharmacies()[0]
    new_rev = s["revision"] + 1
    sid = f"fv-{new_rev}"
    symptom = bool(n.get("entities", {}).get("sintoma")) or intent == "consulta_sintoma"
    ctx = {"surfaceId": sid, "step": "consulta", "channel": "pwa", "user_utterance": text,
           "intent": {"label": intent, "entities": {k: [e["text"] for e in v] for k, v in n.get("entities", {}).items() if k != "cedula"},
                      "source": info["source"]},
           "data": {"products": [fmt_product(x, ph) for x in otc]},
           "customer": mock.public_customer(p), "guardrails": {"redFlag": False}}
    if otc:
        ctx["data"]["nearest_pharmacy"] = fmt_pharmacy(ph)
    else:
        ctx["data"]["note"] = "No hay productos para esto en el catálogo: haz UNA pregunta corta para entender qué necesita o sugiere hablar con un farmacéutico. Sin ProductCard."
    if hints:
        ctx["ui_hints"] = hints
    if safety and not safety.get("ok") and otc:
        ctx["data"]["safety"] = {"reporto_alergias_u_otros_medicamentos": True,
                                 "instruccion": "En note de cada ProductCard: 'Confírmalo con el farmacéutico antes de tomarlo'."}
    if s.get("cart"):
        ctx["data"]["cart_items"] = len(s["cart"])

    msgs, llm_info = None, {}
    for attempt in range(2):
        if time.time() + 11 > deadline:  # una llamada Bedrock (read_timeout 10 s) debe caber en el presupuesto
            break
        extra = None
        if attempt == 1:
            extra = ("Tu respuesta anterior NO pasó la validación: " + "; ".join(llm_info.get("errors", []))[:400] +
                     ". Devuelve solo JSONL válido siguiendo el formato.")
        r = llm.generate(ctx, deadline, extra)
        llm_info = {"ok": r["ok"], "ms": r.get("ms"), "retries": r.get("retries"), "error": r.get("error"), "attempt": attempt + 1}
        if not r["ok"]:
            break
        ok, vm, errs = validate.validate(r["text"], sid, otc, p, red_flag=False)
        if ok:
            msgs = vm
            break
        llm_info["errors"] = errs
    TRACE.update({"llm": {k: v for k, v in llm_info.items() if k != "errors"},
                  "llm_errors": [e.split(":")[0] for e in llm_info.get("errors") or []] or None})
    s["lastProducts"] = [x["sku"] for x in otc]
    if msgs is not None and safety and not safety.get("ok"):
        for c in validate.checks.components_of(msgs):
            if c.get("component") == "ProductCard":
                c["note"] = SAFETY_NOTE
    if msgs is not None:
        has_cards = any(c.get("component") == "ProductCard" for c in validate.checks.components_of(msgs))
        return step(s, "productos" if has_cards else "consulta", lambda r: msgs, validate.spoken_from(msgs), mode)
    # fail closed: plantilla segura, ninguna acción ejecutada
    if otc:
        intro = "Estas opciones de venta libre te pueden ayudar:" if symptom else "Encontré esto para ti:"
        note = SAFETY_NOTE if safety and not safety.get("ok") else None
        return step(s, "productos", lambda r: T.products(r, otc, ph, intro, symptom, note),
                    f"Te muestro {len(otc)} opción{'es' if len(otc) > 1 else ''} de venta libre.", "simulado")
    return step(s, "consulta", lambda r: T.message(r, "No te entendí bien. ¿Me cuentas qué síntoma tienes o qué producto buscas?",
                                                   buttons=[("Hablar con un farmacéutico", "handoff", {})]),
                "¿Me cuentas qué producto buscas?", "simulado")


ADD_RE = re.compile(r"\b(agreg\w*|anad\w*|ponlo|ponla|sumalo|lo quiero|la quiero|lo llevo|la llevo|me lo llevo|me la llevo)\b")
REF_RE = re.compile(ADD_RE.pattern + r"|\b(ese|esa|ese mismo|el primero|el segundo|el tercero|el ultimo|pedido|carrito)\b")
ORD = (("primer", 0), ("segund", 1), ("tercer", 2), ("ultim", -1))


def follow_up(s, t, mode):
    """«agrégalo a mi pedido», «el segundo»: se refiere a lo ya mostrado. Re-buscar ese texto en el catálogo
    no encuentra nada y el LLM respondía «no está en el catálogo» (lastProducts se pisaba con [])."""
    last = [x for x in map(mock.product, s["lastProducts"]) if x and not x.get("requiere_receta")]
    pick = next((i for w, i in ORD if re.search(rf"\b{w}", t)), None)
    if pick is not None and pick >= len(last):
        pick = None
    if last and ADD_RE.search(t) and (len(last) == 1 or pick is not None):
        sku = last[pick or 0]["sku"]
        TRACE["sku"] = sku
        return action("direct", {"sessionId": s["sessionId"], "revision": s["revision"],
                                 "action": {"name": "agregar_pedido", "context": {"sku": sku, "confirm": True}}})
    if not last:
        return step(s, "consulta", lambda r: T.message(r, "¿Qué producto buscas?"), "¿Qué producto buscas?", mode)
    ph = mock.nearest_with([x["sku"] for x in last])
    q = "¿Cuál agrego a tu pedido? Toca «Agregar» en el que quieras."
    return step(s, "productos", lambda r: T.products(r, last, ph, q, False), q, mode)


# ---------- pedido / facturación ----------
def priced(s):
    return mock.price_cart(s["cart"], mock.get_coupon(s["sessionId"], s["cedula"]))


def to_pharmacies(s, added_name):
    phs = mock.pharmacies_with_stock(s["cart"])
    cv = mock.cart_view(priced(s))
    return step(s, "farmacia", lambda r: T.pharmacies(r, phs, cv, added_name),
                (f"Agregué {added_name}. " if added_name else "") + (f"La farmacia más cercana con stock es {phs[0]['name']}. ¿Lo retiras ahí?" if phs else "No encontré farmacia con todo tu pedido."))


def to_resumen(s):
    ph = mock.pharmacy(s["pharmacyId"])
    cv = mock.cart_view(priced(s))
    return step(s, "resumen", lambda r: T.resumen(r, cv, ph), f"Tu total es {cv['total']}. Reservas y pagas al retirar en {ph['name']}.")


def billing_next(s, note=None):
    """Siguiente pregunta de facturación, tarjeta de confirmación o None si listo para reservar."""
    pr = priced(s)
    b = s.setdefault("billing", {})
    over = pr["gross"] > CF_LIMIT
    if over and b.get("tipo") == "consumidor_final":
        b["tipo"], s["billing_card"] = "datos", False
        note = "Como tu total supera $50, la factura necesita tus datos."
    if over:
        b["tipo"] = "datos"
    if not b.get("tipo"):
        s["billing_pending"] = "tipo"
        tl = mock.money(pr["total"])
        return step(s, "facturacion", lambda r: T.billing_tipo(r, tl), f"Tu total es {tl}. ¿Factura a consumidor final o con tus datos?")
    need = ["email"] if b["tipo"] == "consumidor_final" else ["nombre", "identificacion", "email"]
    miss = [f for f in need if not b.get(f)]
    if miss:
        s["billing_pending"], s["billing_card"] = miss[0], False
        return step(s, "facturacion", lambda r: T.billing_field(r, miss[0], note=note), T.FIELD_Q[miss[0]][0])
    if not s.get("billing_card") or s["state"] != "facturacion":
        s["billing_card"], s["billing_pending"] = True, "confirm"
        ph, cv = mock.pharmacy(s["pharmacyId"]), mock.cart_view(pr)
        return step(s, "facturacion", lambda r: T.billing_confirm(r, b, cv, ph), "Confirma tus datos y reservo tu pedido.")
    return None


def set_billing(s, campo, valor):
    b = s.setdefault("billing", {})
    v = str(valor or "").strip()
    if campo == "email":
        v = re.sub(r"\s+arroba\s+|\s*@\s*", "@", v.lower())
        v = re.sub(r"\s+punto\s+", ".", v).replace(" ", "")
        if not EMAIL_RE.match(v):
            return "Ese email no parece válido. ¿Me lo repites?"
    elif campo == "nombre":
        if len(v) < 3:
            return "¿Me dices el nombre completo o la razón social?"
    elif campo == "identificacion":
        v = v.replace(" ", "").replace("-", "") if re.fullmatch(r"[\d\s-]+", v) else v
        t = valid_id(v)
        if not t:
            return "Esa identificación no es válida. ¿Me la repites? (cédula de 10 dígitos, RUC de 13 o pasaporte)"
        b["tipoId"] = t
    else:
        return "Dato no permitido"
    b[campo] = v
    s["billing_card"] = False
    return None


def do_reserve(s, p):
    old = s["revision"]

    def sess_put(result):
        n = copy.deepcopy(s)
        n["revision"], n["state"] = old + 1, "confirmacion"
        n["cart"], n["billing_card"], n["billing_pending"] = [], False, None
        n["lastOrder"] = result["order"]["orderNumber"]
        return n, ("rev", old), {"rev": old + 1}

    res, created = mock.reserve(s["sessionId"], s, p, s["billing"], old, sess_put)
    if created:
        n, _, _ = sess_put(res)
        s.clear()
        s.update(n)
    else:
        cur = get_store().get("SES#" + s["sessionId"], "META")
        s.clear()
        s.update(cur)
    o = res["order"]
    return out(s, T.confirmacion(s["revision"], res),
               f"¡Listo! Tu pedido {o['orderNumber']} está reservado en {o['pharmacy']}. Pagas al retirar.")


def action(caller, body):
    s = load(body.get("sessionId"), caller)
    a = body.get("action") or {}
    name, ctx = a.get("name"), a.get("context") or {}
    if name not in ACTIONS:
        raise ApiError(400, "action_not_allowed", f"Acción no permitida: {name}", s)
    if body.get("revision") != s["revision"]:
        raise ApiError(409, "stale_revision", "Esa opción ya no está vigente", s)
    if s["state"] not in ACTIONS[name]:
        raise ApiError(409, "action_not_allowed", f"'{name}' no aplica en el paso '{s['state']}'", s)
    if name in COMMERCE and s.get("blocked"):
        raise ApiError(409, "blocked_red_flag", "Por seguridad no hay acciones comerciales tras una señal de alarma", s)
    if name in NEEDS_CONFIRM and ctx.get("confirm") is not True:
        raise ApiError(400, "confirmation_required", "Falta la confirmación explícita del usuario", s)
    p = profile_of(s)
    if name == "enviar_cedula":
        return do_cedula(s, extract_cedula(ctx.get("cedula")))
    if name == "consentimiento":
        return do_consent(s, ctx.get("acepta") is True or str(ctx.get("acepta")).lower() == "true")
    if name == "handoff":
        return handoff_resp(s, "Te comunico con un farmacéutico de verdad.")
    if name == "seguridad":
        return answer_safety(s, ctx.get("ok") is True, "no" if ctx.get("ok") is True else "sí")
    if name in ("agregar_pedido", "reservar"):
        pr = mock.product(ctx.get("sku"))
        if not pr:
            raise ApiError(400, "bad_request", "Producto desconocido", s)
        if pr.get("requiere_receta"):  # guardrail en la acción
            return handoff_resp(s, "Ese medicamento necesita receta médica. Un farmacéutico te puede orientar.")
        repo = name == "reservar" and bool(mock.public_customer(p).get("consent")) and \
            any(f["sku"] == pr["sku"] for f in (p or {}).get("frequent_products", []))
        qty = max(1, min(int(ctx.get("qty") or 1), 5))
        for it in s["cart"]:
            if it["sku"] == pr["sku"]:
                it["qty"] = min(10, it["qty"] + qty)
                it["reposicion"] = it.get("reposicion") or repo
                break
        else:
            s["cart"].append({"sku": pr["sku"], "qty": qty, "reposicion": repo})
        s["billing_card"] = False
        if repo and p.get("farmacia_habitual") and mock.has_stock(mock.pharmacy(p["farmacia_habitual"]), s["cart"]):
            s["pharmacyId"] = p["farmacia_habitual"]
            return to_resumen(s)
        return to_pharmacies(s, pr["name"])
    if name == "por_que":
        f = next((f for f in (p or {}).get("frequent_products", []) if f["sku"] == ctx.get("sku")), None)
        if f and mock.public_customer(p).get("consent"):
            txt = f"Te lo sugiero porque sueles llevar {f['name']} ({f['ritmo']}) y tu última compra fue hace {f['ultima_compra_hace_dias']} días. Solo miro tu ritmo de compra."
        else:
            txt = "Te lo sugerí por lo que me contaste hoy, no por tu historial."
        return step(s, s["state"], lambda r: T.message(r, txt), txt)
    if name == "seguir_comprando":
        return step(s, "consulta", lambda r: T.message(r, "¿Qué más necesitas? Puedes hablarme o escribirme."), "¿Qué más necesitas?")
    if name == "retirar_aqui":
        ph = mock.pharmacy(ctx.get("pharmacyId"))
        if not ph:
            raise ApiError(400, "bad_request", "Farmacia desconocida", s)
        if not s["cart"]:
            s["pharmacyId"] = ph["pharmacyId"]
            return step(s, s["state"], lambda r: T.message(r, f"Listo, retiras en {ph['name']}. ¿Qué necesitas?"), f"Listo, retiras en {ph['name']}.")
        if not mock.has_stock(ph, s["cart"]):
            return to_pharmacies(s, None)
        s["pharmacyId"] = ph["pharmacyId"]
        return to_resumen(s)
    if name == "confirmar_reserva":
        if not s["cart"] or not s.get("pharmacyId"):
            raise ApiError(409, "action_not_allowed", "No hay pedido para reservar", s)
        if not mock.has_stock(mock.pharmacy(s["pharmacyId"]), s["cart"]):
            return to_pharmacies(s, None)
        nxt = billing_next(s)
        return nxt if nxt is not None else do_reserve(s, p)
    if name == "facturacion_tipo":
        tipo = ctx.get("tipo")
        if tipo not in ("consumidor_final", "datos"):
            raise ApiError(400, "bad_request", "tipo inválido", s)
        s["billing_card"] = False
        if tipo == "consumidor_final" and priced(s)["gross"] > CF_LIMIT:
            s["billing"]["tipo"] = "datos"
            return billing_next(s, "Como tu total supera $50, la factura necesita tus datos.")
        s["billing"]["tipo"] = tipo
        return billing_next(s)
    if name == "facturacion_dato":
        campo = ctx.get("campo")
        if campo not in ("email", "nombre", "identificacion"):
            raise ApiError(400, "bad_request", "campo inválido", s)
        err = set_billing(s, campo, ctx.get("valor"))
        if err:
            s["billing_pending"] = campo
            return step(s, "facturacion", lambda r: T.billing_field(r, campo, error=err), err)
        return billing_next(s)
    raise ApiError(400, "action_not_allowed", name, s)


def answer_safety(s, ok, answer):
    s["safety"] = {"ok": bool(ok), "answer": str(answer)[:200], "ts": datetime.now(mock.EC_TZ).isoformat(timespec="seconds")}
    q = s.pop("pending_query", None)
    if not q:
        return step(s, "consulta", lambda r: T.message(r, "Gracias. ¿Qué necesitas?"), "Gracias. ¿Qué necesitas?")
    return free_turn(s, q, time.time() + TURN_BUDGET_S)


YES_RE = re.compile(r"\b(si|sí|acepto|claro|dale|ok|okay|de acuerdo|bueno|confirmo|confirmar)\b")
NO_RE = re.compile(r"\b(no|nop|prefiero no|no acepto)\b")
NONE_RE = re.compile(r"\b(no|ninguno|ninguna|nada|tampoco)\b")


def turn(caller, body):
    s = load(body.get("sessionId"), caller)
    text = str(body.get("text") or "").strip()[:500]
    if not text:
        raise ApiError(400, "bad_request", "text vacío", s)
    deadline = time.time() + TURN_BUDGET_S
    s["lastText"] = text
    g0 = guardrails.check_text(text)
    if g0["redFlag"]:
        return red_flag(s, "real")
    t = guardrails.norm(text)
    st = s["state"]
    if st in ("saludo", "cedula"):
        ced = extract_cedula(text)
        if not ced:
            return step(s, "cedula", lambda r: T.cedula(r, None, "Para empezar necesito tu número de cédula (10 dígitos).", greet=False),
                        "Para empezar necesito tu número de cédula.")
        return do_cedula(s, ced)
    if st == "consentimiento":
        if NO_RE.search(t):
            return do_consent(s, False)
        if YES_RE.search(t):
            return do_consent(s, True)
        p = profile_of(s)
        return step(s, "consentimiento", lambda r: T.consent(r, (p or {}).get("name")), "¿Aceptas? Puedes decir sí o no.")
    if st == "facturacion" and s.get("billing_pending"):
        pend = s["billing_pending"]
        if pend == "tipo":
            if "consumidor" in t:
                return action(caller, {"sessionId": s["sessionId"], "revision": s["revision"],
                                       "action": {"name": "facturacion_tipo", "context": {"tipo": "consumidor_final"}}})
            if re.search(r"datos|factura|nombre|ruc", t):
                return action(caller, {"sessionId": s["sessionId"], "revision": s["revision"],
                                       "action": {"name": "facturacion_tipo", "context": {"tipo": "datos"}}})
        elif pend == "confirm":
            if YES_RE.search(t) and not NO_RE.search(t):
                return action(caller, {"sessionId": s["sessionId"], "revision": s["revision"],
                                       "action": {"name": "confirmar_reserva", "context": {"confirm": True}}})
        elif pend in ("email", "nombre", "identificacion"):
            TRACE["billing_text"] = True
            return action(caller, {"sessionId": s["sessionId"], "revision": s["revision"],
                                   "action": {"name": "facturacion_dato", "context": {"campo": pend, "valor": text}}})
    if st in POST_ONBOARD and s.get("pending_query") and not s.get("safety"):
        # Respuesta a la pregunta de seguridad: cualquier respuesta continúa con la consulta pendiente.
        ok = bool(NONE_RE.search(t)) and not re.search(r"\b(si|alergi|tomo|estoy tomando)\b", t)
        return answer_safety(s, ok, text)
    return free_turn(s, text, deadline)
