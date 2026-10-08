"""Datos sintéticos del demo (ninguna persona, cédula ni precio es real)."""

CATALOG_ID = "https://farmaenlace.ec/a2ui/fv/v1"
IVA = 0.15  # Ecuador: medicamentos 0 %, resto 15 %

# sku, name, detail, price (sin IVA), iva, tags, extra
_P = [
    ("FV-1001", "Antigripal Día y Noche", "Caja x 12 tabletas · con fenilefrina", 4.50, 0, "gripe resfriado congestion antigripal", {"contraindica": ["hipertension"]}),
    ("FV-1002", "Paracetamol 500 mg", "Genérico · 20 tabletas", 2.40, 0, "gripe fiebre dolor cabeza paracetamol acetaminofen malestar", {}),
    ("FV-1003", "Vitamina C 1 g efervescente", "Tubo x 10", 3.90, 0, "gripe resfriado defensas vitamina", {}),
    ("FV-1004", "Antigripal sin descongestionante", "Caja x 10 cápsulas · sin fenilefrina", 5.20, 0, "gripe resfriado antigripal", {}),
    ("FV-1005", "Jarabe para la tos 120 ml", "Dextrometorfano · adultos", 6.80, 0, "tos jarabe gripe garganta", {}),
    ("FV-1006", "Pastillas para la garganta", "Miel y limón · x 16", 2.10, 0, "garganta tos dolor", {}),
    ("FV-1007", "Ibuprofeno 400 mg", "Genérico · 10 tabletas", 2.90, 0, "dolor cabeza muscular fiebre ibuprofeno inflamacion", {"contraindica": ["hipertension", "gastritis"]}),
    ("FV-1008", "Suero oral 500 ml", "Sabor coco", 1.60, 0, "diarrea deshidratacion suero vomito", {}),
    ("FV-1009", "Antiácido masticable", "x 12 tabletas", 3.20, 0, "acidez estomago gastritis indigestion agruras", {}),
    ("FV-1010", "Loratadina 10 mg", "Genérico · 10 tabletas", 2.70, 0, "alergia estornudos picazon rinitis loratadina", {}),
    ("FV-1011", "Gotas lubricantes oculares", "Frasco 10 ml", 7.40, 0, "ojos resequedad ojo", {}),
    ("FV-2001", "Multivitamínico 50+", "Frasco x 30 tabletas", 12.80, 0, "vitamina multivitaminico energia", {}),
    ("FV-2002", "Crema humectante corporal", "400 ml · piel seca", 8.90, IVA, "piel crema humectante resequedad", {}),
    ("FV-2003", "Pañal adulto talla M", "Paquete x 10", 11.50, IVA, "panal adulto incontinencia", {}),
    ("FV-2004", "Protector solar FPS 50", "Tubo 120 ml", 14.90, IVA, "sol protector solar bloqueador piel", {}),
    ("FV-2005", "Desodorante roll-on", "50 ml", 3.80, IVA, "desodorante higiene", {}),
    ("FV-2006", "Alcohol antiséptico 70 %", "Frasco 500 ml", 2.30, IVA, "alcohol herida desinfectante", {}),
    ("FV-2007", "Curitas surtidas", "Caja x 30", 2.60, IVA, "herida curita corte", {}),
    ("FV-2008", "Termómetro digital", "Lectura en 10 s", 6.50, IVA, "fiebre termometro temperatura", {}),
    ("FV-2009", "Tensiómetro digital de brazo", "Memoria 60 lecturas", 45.00, IVA, "presion tensiometro", {}),
    ("FV-2010", "Pañales infantiles talla 3", "Paquete x 40", 15.90, IVA, "panal bebe infantil", {}),
    ("FV-2011", "Paracetamol infantil jarabe", "120 ml · niños", 3.40, 0, "fiebre nino infantil paracetamol dolor", {}),
    # Señuelos con receta: nunca se sugieren
    ("FV-9001", "Oseltamivir 75 mg", "Caja x 10 cápsulas", 28.00, 0, "gripe influenza oseltamivir", {"requiere_receta": True}),
    ("FV-9002", "Amoxicilina 500 mg", "Caja x 21 cápsulas", 9.50, 0, "infeccion antibiotico amoxicilina garganta", {"requiere_receta": True}),
]

PRODUCTS = []
for sku, name, detail, price, iva, tags, extra in _P:
    PRODUCTS.append({"sku": sku, "name": name, "detail": detail, "price": price, "iva": iva,
                     "tags": tags.split(), "requiere_receta": bool(extra.get("requiere_receta")),
                     "contraindica": extra.get("contraindica", []), "cashback_pct": 5})

_ALL = [p["sku"] for p in PRODUCTS]
PHARMACIES = [
    {"pharmacyId": "MED-UIO-014", "name": "Medicity La Carolina", "brand": "Medicity", "distance_m": 350,
     "hours": "Abierto hasta las 22:00", "phone": "+593 2 000 0014", "address": "Av. Amazonas y Naciones Unidas (sintético)",
     "mapsUrl": "https://maps.google.com/?q=-0.1807,-78.4840", "stock": {s: 12 for s in _ALL if s != "FV-2009"}},
    {"pharmacyId": "ECO-UIO-003", "name": "Económicas El Inca", "brand": "Económicas", "distance_m": 600,
     "hours": "Abierto hasta las 21:00", "phone": "+593 2 000 0003", "address": "Av. El Inca (sintético)",
     "mapsUrl": "https://maps.google.com/?q=-0.1530,-78.4790", "stock": {s: 8 for s in _ALL}},
    {"pharmacyId": "MED-UIO-021", "name": "Medicity Quicentro", "brand": "Medicity", "distance_m": 1200,
     "hours": "Abierto 24 horas", "phone": "+593 2 000 0021", "address": "Av. Naciones Unidas (sintético)",
     "mapsUrl": "https://maps.google.com/?q=-0.1760,-78.4800", "stock": {s: 20 for s in _ALL}},
    {"pharmacyId": "ECO-UIO-011", "name": "Económicas La Floresta", "brand": "Económicas", "distance_m": 2100,
     "hours": "Abierto hasta las 20:00", "phone": "+593 2 000 0011", "address": "La Floresta (sintético)",
     "mapsUrl": "https://maps.google.com/?q=-0.2050,-78.4870", "stock": {s: 5 for s in _ALL[::2]}},
    {"pharmacyId": "MED-UIO-030", "name": "Medicity Centro Histórico", "brand": "Medicity", "distance_m": 3400,
     "hours": "Abierto hasta las 19:00", "phone": "+593 2 000 0030", "address": "Centro Histórico (sintético)",
     "mapsUrl": "https://maps.google.com/?q=-0.2200,-78.5120", "stock": {s: 3 for s in _ALL}},
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
]

COUPONS = {"BIENVENIDA": {"code": "BIENVENIDA3", "title": "Cupón de bienvenida $3 en tu primera reserva",
                          "amount": 3.00, "until": "31/12/2026", "note": "Muéstralo al farmacéutico"}}
PROMOS = [{"id": "REPOSICION2X", "title": "Doble cashback SmartClub en tu reposición", "cashback_pct": 10},
          {"id": "CASHBACK5", "title": "5% cashback SmartClub", "cashback_pct": 5}]
