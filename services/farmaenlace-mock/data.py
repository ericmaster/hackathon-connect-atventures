"""Datos semilla de la API mock de Farmaenlace (tabla `connect-atv-farmaenlace`).

TODO es sintético o referencial:
- Precios: REFERENCIALES/MOCK. No son precios de Farmaenlace ni de ninguna farmacia real.
- Farmacias: nombres y direcciones públicas de locales Medicity/Económicas en Quito (fuentes en README.md);
  coordenadas aproximadas; teléfonos, horarios y stock son MOCK.
- Clientes: personas, cédulas y saldos ficticios.
"""
IVA = 0.15  # Ecuador: medicamentos 0 %, resto 15 %
PRICE_NOTE = "Precio referencial de demo (mock); no es un precio real de Farmaenlace"

# Ubicación demo del cliente (Av. Amazonas y Naciones Unidas, Quito) cuando no llega lat/lng.
DEMO_LAT, DEMO_LNG = -0.1765, -78.4860

# sku, name, detail, price (sin IVA), iva, tags, extra
# Los 24 SKU originales conservan nombre/tags/precio (comportamiento idéntico del demo);
# se agrega presentación/forma farmacéutica realista.
_P = [
    ("FV-1001", "Antigripal Día y Noche", "Caja x 12 tabletas · con fenilefrina", 4.50, 0, "gripe resfriado congestion antigripal", {"contraindica": ["hipertension"], "boost": 1, "forma": "tableta", "principio": "paracetamol + fenilefrina + clorfenamina"}),
    ("FV-1002", "Paracetamol 500 mg", "Genérico · 20 tabletas", 2.40, 0, "gripe fiebre dolor cabeza paracetamol acetaminofen malestar", {"forma": "tableta", "principio": "paracetamol 500 mg"}),
    ("FV-1003", "Vitamina C 1 g efervescente", "Tubo x 10", 3.90, 0, "gripe resfriado defensas vitamina", {"forma": "tableta efervescente", "principio": "ácido ascórbico 1 g"}),
    ("FV-1004", "Antigripal sin descongestionante", "Caja x 10 cápsulas · sin fenilefrina", 5.20, 0, "gripe resfriado antigripal", {"boost": 1, "forma": "cápsula", "principio": "paracetamol + clorfenamina"}),
    ("FV-1005", "Jarabe para la tos 120 ml", "Dextrometorfano · adultos", 6.80, 0, "tos jarabe gripe garganta", {"forma": "jarabe", "principio": "dextrometorfano 15 mg/5 ml"}),
    ("FV-1006", "Pastillas para la garganta", "Miel y limón · x 16", 2.10, 0, "garganta tos dolor", {"forma": "pastilla", "principio": "amilmetacresol + alcohol diclorobencílico"}),
    ("FV-1007", "Ibuprofeno 400 mg", "Genérico · 10 tabletas", 2.90, 0, "dolor cabeza muscular fiebre ibuprofeno inflamacion", {"contraindica": ["hipertension", "gastritis"], "forma": "tableta", "principio": "ibuprofeno 400 mg"}),
    ("FV-1008", "Suero oral 500 ml", "Sabor coco", 1.60, 0, "diarrea deshidratacion suero vomito", {"forma": "solución oral", "principio": "sales de rehidratación oral"}),
    ("FV-1009", "Antiácido masticable", "x 12 tabletas", 3.20, 0, "acidez estomago gastritis indigestion agruras", {"forma": "tableta masticable", "principio": "carbonato de calcio + hidróxido de magnesio"}),
    ("FV-1010", "Loratadina 10 mg", "Genérico · 10 tabletas", 2.70, 0, "alergia estornudos picazon rinitis loratadina", {"forma": "tableta", "principio": "loratadina 10 mg"}),
    ("FV-1011", "Gotas lubricantes oculares", "Frasco 10 ml", 7.40, 0, "ojos resequedad ojo", {"forma": "solución oftálmica", "principio": "carboximetilcelulosa 0,5 %"}),
    ("FV-2001", "Multivitamínico 50+", "Frasco x 30 tabletas", 12.80, 0, "vitamina multivitaminico energia", {"forma": "tableta", "principio": "multivitamínico + minerales"}),
    ("FV-2002", "Crema humectante corporal", "400 ml · piel seca", 8.90, IVA, "piel crema humectante resequedad", {"forma": "crema"}),
    ("FV-2003", "Pañal adulto talla M", "Paquete x 10", 11.50, IVA, "panal adulto incontinencia", {"forma": "pañal"}),
    ("FV-2004", "Protector solar FPS 50", "Tubo 120 ml", 14.90, IVA, "sol protector solar bloqueador piel", {"forma": "crema"}),
    ("FV-2005", "Desodorante roll-on", "50 ml", 3.80, IVA, "desodorante higiene", {"forma": "roll-on"}),
    ("FV-2006", "Alcohol antiséptico 70 %", "Frasco 500 ml", 2.30, IVA, "alcohol herida desinfectante", {"forma": "solución tópica"}),
    ("FV-2007", "Curitas surtidas", "Caja x 30", 2.60, IVA, "herida curita corte", {"forma": "apósito"}),
    ("FV-2008", "Termómetro digital", "Lectura en 10 s", 6.50, IVA, "fiebre termometro temperatura", {"forma": "dispositivo"}),
    ("FV-2009", "Tensiómetro digital de brazo", "Memoria 60 lecturas", 45.00, IVA, "presion tensiometro", {"forma": "dispositivo"}),
    ("FV-2010", "Pañales infantiles talla 3", "Paquete x 40", 15.90, IVA, "panal bebe infantil", {"forma": "pañal"}),
    ("FV-2011", "Paracetamol infantil jarabe", "120 ml · niños", 3.40, 0, "fiebre nino infantil paracetamol dolor", {"forma": "jarabe", "principio": "paracetamol 160 mg/5 ml"}),
    # Señuelos con receta: nunca se sugieren
    ("FV-9001", "Oseltamivir 75 mg", "Caja x 10 cápsulas", 28.00, 0, "gripe influenza oseltamivir", {"requiere_receta": True, "forma": "cápsula", "principio": "oseltamivir 75 mg"}),
    ("FV-9002", "Amoxicilina 500 mg", "Caja x 21 cápsulas", 9.50, 0, "infeccion antibiotico amoxicilina garganta", {"requiere_receta": True, "forma": "cápsula", "principio": "amoxicilina 500 mg"}),
    # Ampliación del catálogo (venta libre). Tags elegidos para no alterar el ranking de las búsquedas del demo.
    ("FV-1012", "Clotrimazol crema 1 %", "Tubo 20 g", 3.60, 0, "hongos pie micosis clotrimazol", {"forma": "crema", "principio": "clotrimazol 1 %"}),
    ("FV-1013", "Simeticona 80 mg masticable", "Caja x 20 tabletas", 3.10, 0, "gases flatulencia simeticona hinchazon", {"forma": "tableta masticable", "principio": "simeticona 80 mg"}),
    ("FV-1014", "Dimenhidrinato 50 mg", "Caja x 10 tabletas", 2.80, 0, "mareo viaje nausea dimenhidrinato", {"forma": "tableta", "principio": "dimenhidrinato 50 mg"}),
    ("FV-1015", "Pomada de óxido de zinc", "Tubo 60 g · rozaduras", 4.20, 0, "rozadura panalitis zinc pomada", {"forma": "pomada", "principio": "óxido de zinc 20 %"}),
    ("FV-1016", "Solución salina nasal", "Spray 30 ml · 0,9 %", 4.80, 0, "nariz nasal salina lavado", {"forma": "spray nasal", "principio": "cloruro de sodio 0,9 %"}),
    ("FV-2012", "Mascarillas quirúrgicas", "Caja x 50 · 3 capas", 5.50, IVA, "mascarilla tapabocas", {"forma": "insumo"}),
    ("FV-2013", "Gel antibacterial", "Frasco 250 ml · alcohol 70 %", 2.95, IVA, "gel antibacterial manos", {"forma": "gel"}),
    ("FV-2014", "Gasas estériles 10 x 10 cm", "Sobre x 10", 1.90, IVA, "gasa esteril", {"forma": "insumo"}),
    ("FV-2015", "Crema dental con flúor", "Tubo 100 ml", 2.75, IVA, "dental dientes crema cepillado", {"forma": "pasta"}),
    ("FV-2016", "Repelente de insectos", "Spray 120 ml · DEET 15 %", 7.90, IVA, "repelente mosquito insectos", {"forma": "spray"}),
    ("FV-2017", "Shampoo anticaspa", "Frasco 375 ml", 6.40, IVA, "caspa shampoo cabello", {"forma": "shampoo"}),
    ("FV-2018", "Prueba de embarazo", "1 prueba · resultado en 3 min", 4.50, IVA, "embarazo prueba", {"forma": "dispositivo"}),
]

PRODUCTS = []
for sku, name, detail, price, iva, tags, extra in _P:
    PRODUCTS.append({"sku": sku, "name": name, "detail": detail, "price": price, "iva": iva,
                     "tags": tags.split(), "requiere_receta": bool(extra.get("requiere_receta")),
                     "contraindica": extra.get("contraindica", []), "cashback_pct": 5,
                     "boost": extra.get("boost", 0), "forma": extra.get("forma"),
                     "principio_activo": extra.get("principio"), "precio_referencial": True, "nota_precio": PRICE_NOTE})

_ORIG = [p[0] for p in _P[:24]]   # patrón de stock original (no cambiar: el demo depende de él)
_NEW = [p[0] for p in _P[24:]]


def _stock(orig, new):
    d = dict(orig)
    d.update(new)
    return d


# Direcciones públicas (ver README.md § Fuentes). Coordenadas aproximadas. Teléfono/horario/stock MOCK.
PHARMACIES = [
    {"pharmacyId": "MED-UIO-014", "name": "Medicity Quito CCI", "brand": "Medicity",
     "address": "Av. Amazonas N36-152 y Naciones Unidas (C.C. Iñaquito)", "lat": -0.1757, "lng": -78.4840,
     "hours": "Abierto hasta las 22:00", "phone": "+593 2 000 0014", "fuente": "farmaenlace.com/puntos-de-venta",
     "stock": _stock({s: 12 for s in _ORIG if s != "FV-2009"}, {s: 9 for s in _NEW})},
    {"pharmacyId": "ECO-UIO-003", "name": "Económicas Shyris", "brand": "Económicas",
     "address": "Av. de los Shyris N37-104 y El Comercio", "lat": -0.1735, "lng": -78.4787,
     "hours": "Abierto hasta las 21:00", "phone": "+593 2 000 0003", "fuente": "ubica.ec",
     "stock": _stock({s: 8 for s in _ORIG}, {s: 6 for s in _NEW})},
    {"pharmacyId": "MED-UIO-021", "name": "Medicity Amazonas", "brand": "Medicity",
     "address": "Av. Amazonas N31-63 y Av. Eloy Alfaro", "lat": -0.1895, "lng": -78.4868,
     "hours": "Abierto 24 horas", "phone": "+593 2 000 0021", "fuente": "humana.med.ec (puntos de venta Medicity)",
     "stock": _stock({s: 20 for s in _ORIG}, {s: 15 for s in _NEW})},
    {"pharmacyId": "ECO-UIO-011", "name": "Económicas El Inca 2", "brand": "Económicas",
     "address": "Av. El Inca E13-50 y De los Madroños", "lat": -0.1544, "lng": -78.4714,
     "hours": "Abierto hasta las 20:00", "phone": "+593 2 000 0011", "fuente": "ubica.ec / exa.ai place",
     "stock": _stock({s: 5 for s in _ORIG[::2]}, {s: 4 for s in _NEW[::2]})},
    {"pharmacyId": "MED-UIO-030", "name": "Medicity Quito Robles", "brand": "Medicity",
     "address": "Av. Amazonas N21-108 entre Robles y Roca", "lat": -0.2040, "lng": -78.4930,
     "hours": "Abierto hasta las 19:00", "phone": "+593 2 000 0030", "fuente": "humana.med.ec (puntos de venta Medicity)",
     "stock": _stock({s: 3 for s in _ORIG}, {s: 2 for s in _NEW})},
]

PROFILES = [
    {"cedula": "1710034065", "name": "don Luis", "archetype": "Cuidador",
     "ui_hints": {"font": "extra-large", "voice_first": True, "max_options": 2},
     "frequent_products": [{"sku": "FV-2001", "name": "Multivitamínico 50+", "ritmo": "mensual", "ritmo_dias": 30, "ultima_compra_hace_dias": 27},
                           {"sku": "FV-2002", "name": "Crema humectante corporal", "ritmo": "bimestral", "ritmo_dias": 60, "ultima_compra_hace_dias": 20},
                           {"sku": "FV-2003", "name": "Pañal adulto talla M", "ritmo": "mensual", "ritmo_dias": 30, "ultima_compra_hace_dias": 12}],
     "condiciones_probables": ["hipertension", "artrosis"],  # NUNCA salen del servidor
     "farmacia_habitual": "ECO-UIO-003", "preferencias": {"canal": "voz"},
     "consent": None, "billing": None, "smartclub": {"socio": True, "cashback_saldo": 1.20}},
    {"cedula": "1712456787", "name": "Andrea", "archetype": "Práctico",
     "ui_hints": {"font": "normal", "voice_first": False, "max_options": 1, "quick_add": True},
     "frequent_products": [{"sku": "FV-1001", "name": "Antigripal Día y Noche", "ritmo": "ocasional", "ritmo_dias": 120, "ultima_compra_hace_dias": 90},
                           {"sku": "FV-2004", "name": "Protector solar FPS 50", "ritmo": "bimestral", "ritmo_dias": 60, "ultima_compra_hace_dias": 25},
                           {"sku": "FV-2005", "name": "Desodorante roll-on", "ritmo": "mensual", "ritmo_dias": 30, "ultima_compra_hace_dias": 10}],
     "condiciones_probables": ["rinitis"],
     "farmacia_habitual": "MED-UIO-014", "preferencias": {"canal": "texto"},
     "consent": None, "billing": None, "smartclub": {"socio": True, "cashback_saldo": 0.35}},
    # Perfiles sintéticos extra (solo admin / pruebas manuales)
    {"cedula": "1703344556", "name": "doña Rosa", "archetype": "Cuidador",
     "ui_hints": {"font": "extra-large", "voice_first": True, "max_options": 2},
     "frequent_products": [{"sku": "FV-2003", "name": "Pañal adulto talla M", "ritmo": "mensual", "ritmo_dias": 30, "ultima_compra_hace_dias": 29}],
     "condiciones_probables": ["diabetes"], "farmacia_habitual": "MED-UIO-021", "preferencias": {"canal": "voz"},
     "consent": None, "billing": None, "smartclub": {"socio": True, "cashback_saldo": 4.10}},
    {"cedula": "1756677889", "name": "Mateo", "archetype": "Práctico",
     "ui_hints": {"font": "normal", "voice_first": False, "max_options": 1, "quick_add": True},
     "frequent_products": [{"sku": "FV-2013", "name": "Gel antibacterial", "ritmo": "mensual", "ritmo_dias": 30, "ultima_compra_hace_dias": 8}],
     "condiciones_probables": [], "farmacia_habitual": "ECO-UIO-011", "preferencias": {"canal": "texto"},
     "consent": None, "billing": None, "smartclub": {"socio": False, "cashback_saldo": 0.0}},
]

COUPONS = {"BIENVENIDA": {"code": "BIENVENIDA3", "title": "Cupón de bienvenida $3 en tu primera reserva",
                          "amount": 3.00, "until": "31/12/2026", "note": "Muéstralo al farmacéutico"}}
PROMOS = [{"id": "REPOSICION2X", "title": "Doble cashback SmartClub en tu reposición", "cashback_pct": 10},
          {"id": "CASHBACK5", "title": "5% cashback SmartClub", "cashback_pct": 5}]

# Emisor MOCK (no es el RUC real de Farmaenlace)
EMISOR = {"ruc": "0999999999001", "razonSocial": "FARMAENLACE MOCK (DEMO HACKATHON)", "estab": "001", "ptoEmi": "002"}
