"""Genera connect-atv-meds.tsv (tabla Transcribe: Phrase/SoundsLike/IPA/DisplayAs, TAB).
SoundsLike/IPA: AWS ya los ignora → vacíos. Phrase: sin espacios ni dígitos, guiones para multipalabra.
Nombres públicos/sintéticos solamente."""
import re, sys, unicodedata

# (Phrase, DisplayAs or "")
TERMS = [
    # marcas del demo
    ("Medicity", ""), ("Económicas", ""), ("Smart-Club", "SmartClub"), ("Farmaenlace", ""),
    ("Farmacéutico-Virtual", "Farmacéutico Virtual"),
    # activos / genéricos (seed + OTC comunes)
    ("Paracetamol", ""), ("Acetaminofén", ""), ("Ibuprofeno", ""), ("Naproxeno", ""), ("Diclofenaco", ""),
    ("Loratadina", ""), ("Cetirizina", ""), ("Desloratadina", ""), ("Clorfenamina", ""),
    ("Fenilefrina", ""), ("Dextrometorfano", ""), ("Ambroxol", ""), ("Bromhexina", ""),
    ("Omeprazol", ""), ("Simeticona", ""), ("Oseltamivir", ""), ("Amoxicilina", ""),
    ("Antigripal", ""), ("Multivitamínico", ""), ("Antiácido", ""), ("Tensiómetro", ""),
    ("Complejo-B", "complejo B"),
    # marcas OTC frecuentes en farmacias de Ecuador
    ("Buprex", ""), ("Buprex-Flash", "Buprex Flash"), ("Tempra", ""), ("Finalín", ""), ("Apronax", ""),
    ("Dolo-Neurobión", "Dolo-Neurobión"), ("Neurobión", ""), ("Tapsin", ""), ("Lemonflu", ""),
    ("Desenfriolito", ""), ("Mucosolvan", ""), ("Bisolvon", ""), ("Sal-de-Frutas-Eno", "Sal de Frutas Eno"),
    ("Eno", ""), ("Alka-Seltzer", "Alka-Seltzer"), ("Vick-VapoRub", "Vick VapoRub"), ("Mentholatum", ""),
    ("Pedialyte", ""), ("Electrolit", ""), ("Hidraplus", ""), ("Enterogermina", ""), ("Redoxon", ""),
    ("Centrum", ""), ("Ensure", ""), ("Pampers", ""), ("Huggies", ""), ("Advil", ""), ("Aspirina", ""),
    ("Panadol", ""), ("Buscapina", ""), ("Sertal", ""), ("Voltaren", ""), ("Clarityne", ""),
    ("Strepsils", ""), ("Halls", ""), ("Dramamine", ""), ("Pepto-Bismol", "Pepto-Bismol"),
    ("Gaviscon", ""), ("Tamiflu", ""),
    # variantes fonéticas → DisplayAs canónico (SoundsLike ya no existe; así se guía la pronunciación)
    ("Bubreks", "Buprex"), ("A-Pronax", "Apronax"), ("Fina-lín", "Finalín"),
]

ALLOWED = re.compile(r"^[A-Za-z'\-.ÁÉÍÓÚÑáéíóúñü]+$")

def check(p):
    assert unicodedata.normalize("NFC", p) == p, p
    assert ALLOWED.match(p), f"char no permitido: {p}"
    assert not re.search(r"\d", p) and " " not in p, p
    assert not p[0] in ".'-" and not p[-1] in "'-", p
    assert "--" not in p and ".." not in p and "''" not in p, p

def main(out="connect-atv-meds.tsv"):
    seen = set()
    rows = ["Phrase\tSoundsLike\tIPA\tDisplayAs"]
    for p, d in TERMS:
        check(p)
        assert p.lower() not in seen, f"dup {p}"
        seen.add(p.lower())
        rows.append(f"{p}\t\t\t{d}")
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
    print(f"{len(TERMS)} términos → {out}")

if __name__ == "__main__":
    main(*sys.argv[1:])
