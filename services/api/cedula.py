"""Validación módulo 10 de la cédula ecuatoriana (SPEC §7.1)."""
import re


def valid_cedula(c) -> bool:
    c = re.sub(r"\D", "", str(c or ""))
    if len(c) != 10:
        return False
    prov = int(c[:2])
    if not (1 <= prov <= 24 or prov == 30) or int(c[2]) >= 6:
        return False
    s = 0
    for i in range(9):
        v = int(c[i]) * (2 if i % 2 == 0 else 1)
        s += v - 9 if v > 9 else v
    return (10 - s % 10) % 10 == int(c[9])


def valid_ruc(r) -> bool:
    r = re.sub(r"\D", "", str(r or ""))
    return len(r) == 13 and r.endswith("001") and 1 <= int(r[:2]) <= 24 and int(r[2]) in (0, 1, 2, 3, 4, 5, 6, 9)


def valid_id(v) -> str | None:
    """Devuelve tipoIdentificacionComprador SRI (05 cédula, 04 RUC, 06 pasaporte) o None."""
    v = str(v or "").strip()
    d = re.sub(r"\D", "", v)
    if len(d) == 10 and d == re.sub(r"[\s-]", "", v) and valid_cedula(d):
        return "05"
    if len(d) == 13 and valid_ruc(d):
        return "04"
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9]{5,19}", v):
        return "06"
    return None


def extract_cedula(text) -> str | None:
    """Toma los dígitos de un texto ("mi cédula es 17 1003 4065")."""
    d = re.sub(r"\D", "", str(text or ""))
    return d if d else None
