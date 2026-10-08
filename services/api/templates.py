"""Plantillas A2UI v0.9.1 deterministas (pasos fijos del FSM y fallbacks seguros)."""
from fixtures import CATALOG_ID
from mock import distance_label, money

V = "v0.9.1"
AVISO = "Si persiste, consulta a un médico. No reemplaza la consulta con un profesional de salud."


class Surface:
    def __init__(self, rev):
        self.sid, self.comps, self.data, self.root = f"fv-{rev}", [], [], []

    def add(self, cid, component, top=True, **props):
        self.comps.append(dict({"id": cid, "component": component}, **props))
        if top:
            self.root.append(cid)
        return cid

    def text(self, cid, text, variant="body", top=True):
        return self.add(cid, "Text", top, text=text, variant=variant)

    def button(self, cid, label, name, context=None, variant="primary", top=True):
        self.add(cid + "l", "Text", False, text=label)
        ev = {"name": name}
        if context is not None:
            ev["context"] = context
        return self.add(cid, "Button", top, child=cid + "l", variant=variant, action={"event": ev})

    def link(self, cid, label, url, top=True):
        self.add(cid + "l", "Text", False, text=label)
        return self.add(cid, "Button", top, child=cid + "l", variant="borderless",
                        action={"functionCall": {"call": "openUrl", "args": {"url": url}}})

    def model(self, path, value):
        self.data.append((path, value))

    def messages(self):
        comps = [{"id": "root", "component": "Column", "children": self.root}] + self.comps
        out = [{"version": V, "createSurface": {"surfaceId": self.sid, "catalogId": CATALOG_ID}},
               {"version": V, "updateComponents": {"surfaceId": self.sid, "components": comps}}]
        for p, v in self.data:
            out.append({"version": V, "updateDataModel": {"surfaceId": self.sid, "path": p, "value": v}})
        return out


def product_card(s, cid, p, pharmacy, note=None):
    st = pharmacy["stock"].get(p["sku"], 0) if pharmacy else 0
    props = dict(sku=p["sku"], name=p["name"], detail=p["detail"], price=money(p["price"]),
                 cashback=f"{p['cashback_pct']}% cashback · {money(p['price'] * p['cashback_pct'] / 100)}",
                 stock=(f"Hay stock a {distance_label(pharmacy['distance_m'])}" if st else "Consultar stock"),
                 ventaLibre=True, action={"event": {"name": "agregar_pedido", "context": {"sku": p["sku"], "confirm": True}}})
    if note:
        props["note"] = note
    return s.add(cid, "ProductCard", **props)


def pharmacy_card(s, cid, ph, stock_label="Tiene tu pedido"):
    return s.add(cid, "PharmacyCard", pharmacyId=ph["pharmacyId"], name=ph["name"], distance=distance_label(ph["distance_m"]),
                 hours=ph["hours"], stock=stock_label, phone=ph["phone"], mapsUrl=ph["mapsUrl"],
                 action={"event": {"name": "retirar_aqui", "context": {"pharmacyId": ph["pharmacyId"]}}})


def cedula(rev, coupon, retry=None, handoff_ph=None, greet=True):
    s = Surface(rev)
    if greet:
        s.text("t1", "¡Hola! Soy tu Farmacéutico Virtual de Farmaenlace.", "h2")
        if coupon:
            s.add("cup", "Cupon", title=coupon["title"], code=coupon["code"], until=coupon["until"],
                  note="Se aplica en tu primera reserva")
    s.text("t2", retry or "¿Me ayudas con tu número de cédula?", "body")
    s.add("f1", "TextField", label="Cédula", variant="number", value={"path": "/cedula"},
          checks=[{"call": "required", "args": {"value": {"path": "/cedula"}}, "message": "Escribe tu cédula"},
                  {"call": "cedulaEc", "args": {"value": {"path": "/cedula"}}, "message": "¿Me la repites? Revisa los 10 dígitos"}])
    s.button("b1", "Continuar", "enviar_cedula", {"cedula": {"path": "/cedula"}})
    if handoff_ph:
        handoff_card(s, handoff_ph, "No pudimos validar la cédula. Un farmacéutico puede ayudarte.")
    s.model("/cedula", "")
    return s.messages()


def consent(rev, name=None):
    s = Surface(rev)
    s.text("t1", f"¡Gracias{', ' + name if name else ''}! Un último paso.", "h2")
    s.add("c1", "CheckBox", label="Acepto que Farmaenlace use mi historial de compras para darme sugerencias personalizadas",
          value={"path": "/consent"})
    s.text("t2", "Puedes seguir sin aceptar; solo no personalizaremos tus sugerencias.", "caption")
    s.button("b1", "Continuar", "consentimiento", {"acepta": {"path": "/consent"}})
    s.model("/consent", False)
    return s.messages()


def listo(rev, customer, coupon, repo=None, repo_product=None, pharmacy=None):
    s = Surface(rev)
    name = customer.get("name")
    s.text("t1", f"¡Listo{', ' + name if name else ''}! Ya tienes tu beneficio.", "h2")
    if coupon and coupon.get("status") == "disponible":
        s.add("cup", "Cupon", title=coupon["title"], code=coupon["code"], until=coupon["until"], note=coupon["note"])
    if repo and repo_product:
        p = repo_product
        s.add("rep", "SugerenciaPersonalizada",
              message=f"Sueles llevar tu {p['name']} cada mes. ¿Te lo reservo{' en ' + pharmacy['name'] if pharmacy else ''}?",
              product={"sku": p["sku"], "name": p["name"], "price": money(p["price"]),
                       "cashback": f"Doble cashback SmartClub · {money(p['price'] * p['cashback_pct'] * 2 / 100)}"},
              why=f"Te lo sugiero porque lo compras {repo['ritmo']} y tu última compra fue hace {repo['ultima_compra_hace_dias']} días.",
              action={"event": {"name": "reservar", "context": {"sku": p["sku"], "confirm": True}}})
    s.text("t2", "¿En qué te ayudo hoy? Puedes hablarme o escribirme.", "body")
    return s.messages()


def products(rev, prods, pharmacy, intro, symptom=True):
    s = Surface(rev)
    s.text("t1", intro, "h3")
    for i, p in enumerate(prods):
        product_card(s, f"p{i + 1}", p, pharmacy)
    if pharmacy:
        pharmacy_card(s, "ph1", pharmacy, "Tiene estos productos")
    if symptom:
        s.add("av", "AvisoSalud", text=AVISO)
    return s.messages()


def message(rev, text, aviso=False, buttons=()):
    s = Surface(rev)
    s.text("t1", text, "body")
    if aviso:
        s.add("av", "AvisoSalud", text=AVISO)
    for i, (label, name, ctx) in enumerate(buttons):
        s.button(f"b{i}", label, name, ctx, variant="primary" if i == 0 else "borderless")
    return s.messages()


def pharmacies(rev, phs, cv, added_name=None):
    s = Surface(rev)
    s.text("t1", (f"Agregué {added_name} a tu pedido. " if added_name else "") + "¿Dónde lo retiras?", "h3")
    s.text("t2", f"Tu pedido: {len(cv['items'])} producto(s) · total {cv['total']}", "caption")
    for i, ph in enumerate(phs):
        pharmacy_card(s, f"ph{i + 1}", ph)
    if not phs:
        s.text("t3", "Ninguna farmacia cercana tiene todo tu pedido. Prueba quitando un producto.", "body")
    s.button("more", "Agregar algo más", "seguir_comprando", {}, variant="borderless")
    return s.messages()


def resumen(rev, cv, ph):
    s = Surface(rev)
    s.text("t1", "Revisa tu pedido", "h3")
    props = dict(items=cv["items"], subtotal=cv["subtotal"], iva=cv["iva"], total=cv["total"], cashback=cv["cashback"],
                 pharmacy=ph["name"], action={"event": {"name": "confirmar_reserva", "context": {"confirm": True}}})
    if cv.get("coupon"):
        props["coupon"] = cv["coupon"]
    s.add("rs", "ResumenPedido", **props)
    pharmacy_card(s, "ph1", ph)
    s.text("t2", "Reservas ahora y pagas al retirar en la farmacia.", "caption")
    s.button("more", "Agregar algo más", "seguir_comprando", {}, variant="borderless")
    return s.messages()


FIELD_Q = {"email": ("¿A qué email te enviamos la factura?", "Email", "shortText"),
           "nombre": ("¿A nombre de quién va la factura? (nombre o razón social)", "Nombre o razón social", "shortText"),
           "identificacion": ("¿Tu cédula, RUC o pasaporte para la factura?", "Cédula / RUC / pasaporte", "shortText")}


def billing_tipo(rev, total_label):
    s = Surface(rev)
    s.text("t1", f"Tu total es {total_label}. ¿Cómo quieres tu factura?", "h3")
    s.button("b1", "Consumidor final", "facturacion_tipo", {"tipo": "consumidor_final"})
    s.button("b2", "Factura con mis datos", "facturacion_tipo", {"tipo": "datos"}, variant="borderless")
    s.text("t2", "Con consumidor final solo te pido tu email.", "caption")
    return s.messages()


def billing_field(rev, campo, error=None, note=None):
    q, label, variant = FIELD_Q[campo]
    s = Surface(rev)
    if note:
        s.text("t0", note, "caption")
    s.text("t1", error or q, "h3")
    checks = [{"call": "required", "args": {"value": {"path": f"/factura/{campo}"}}, "message": "Este dato es necesario"}]
    if campo == "email":
        checks.append({"call": "email", "args": {"value": {"path": "/factura/email"}}, "message": "Revisa el email"})
    s.add("f1", "TextField", label=label, variant=variant, value={"path": f"/factura/{campo}"}, checks=checks)
    s.button("b1", "Continuar", "facturacion_dato", {"campo": campo, "valor": {"path": f"/factura/{campo}"}})
    s.model(f"/factura/{campo}", "")
    return s.messages()


def billing_confirm(rev, b, cv, ph):
    s = Surface(rev)
    s.text("t1", "Confirma tus datos de factura", "h3")
    cf = b.get("tipo") == "consumidor_final"
    s.add("cd", "Card", child="cdc")
    s.add("cdc", "Column", False, children=["c1", "c2", "c3", "c4"])
    s.text("c1", "Consumidor final" if cf else b.get("nombre", ""), "body", top=False)
    s.text("c2", "ID 9999999999999" if cf else f"ID {b.get('identificacion', '')}", "caption", top=False)
    s.text("c3", f"Factura a {b.get('email', '')}", "caption", top=False)
    s.text("c4", f"Total {cv['total']} · retiras en {ph['name']} · pagas al retirar", "body", top=False)
    s.button("b1", "Confirmar y reservar", "confirmar_reserva", {"confirm": True})
    s.button("b2", "Cambiar datos", "facturacion_tipo", {"tipo": "datos"}, variant="borderless")
    return s.messages()


def confirmacion(rev, res):
    o, inv, pr = res["order"], res["invoice"], res["pricing"]
    s = Surface(rev)
    s.text("t1", "¡Listo! Tu pedido está reservado.", "h2")
    s.add("cf", "ConfirmacionPedido", orderNumber=o["orderNumber"], pharmacy=o["pharmacy"], pickupTime=o["pickupTime"],
          qrValue=o["qrValue"])
    s.add("fx", "FacturaMock", number=inv["number"], customerName=inv["customerName"], customerId=inv["customerId"],
          email=inv["email"], items=inv["items"], subtotal=inv["subtotal"], iva=inv["iva"], total=inv["total"], label="SIMULADA")
    if res.get("coupon"):
        c = res["coupon"]
        s.add("cup", "Cupon", title=f"{c['title']} · aplicado −{money(pr['discount'])}", code=c["code"], until=c["until"],
              note="Muéstralo al farmacéutico")
    s.text("t2", f"Ganas {money(pr['cashback'])} de cashback SmartClub" + (" (doble por reposición)." if pr["double_cashback"] else "."), "body")
    s.text("t3", "Pagas al retirar en la farmacia. Muéstrale el código al farmacéutico.", "caption")
    s.button("b1", "Nueva consulta", "seguir_comprando", {}, variant="borderless")
    return s.messages()


def handoff_card(s, ph, summary):
    s.add("ho", "HandoffCard", summary=summary, pharmacy=ph["name"] if ph else "", phone=ph["phone"] if ph else "",
          mapsUrl=ph["mapsUrl"] if ph else "")
    if ph:
        s.link("hocall", "Llamar", "tel:" + ph["phone"].replace(" ", ""))
        s.link("homap", "Cómo llegar", ph["mapsUrl"])


def handoff(rev, ph, summary, intro="Te comunico con un farmacéutico de verdad."):
    s = Surface(rev)
    s.text("t1", intro, "h3")
    handoff_card(s, ph, summary)
    return s.messages()


def alerta(rev, ph):
    s = Surface(rev)
    s.add("al", "AlertaRoja", text="Lo que describes puede ser una emergencia. Llama ahora al ECU 911 o acude a emergencias.",
          phone="911", action={"event": {"name": "handoff", "context": {}}})
    s.link("call", "Llamar al 911", "tel:911")
    s.text("t1", "Por tu seguridad no te voy a sugerir productos ahora.", "caption")
    return s.messages()


def stale(rev, text="Esa opción ya no está vigente. Sigamos desde aquí."):
    return message(rev, text)
