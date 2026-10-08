"""Guardrails propios (SPEC §8): corren ANTES del LLM y antes de cualquier acción comercial.

- Señal de alarma (lista de palabras + intención GLiNER) → AlertaRoja fija, bloquea comercio.
- Pedido de diagnóstico → respuesta fija sin diagnóstico + hand-off.
- Medicamento con receta → hand-off (nunca se sugiere).
- Nunca afirmar una condición: `leaks()` revisa texto visible contra condiciones del CRM y frases de afirmación.
"""
import re
import unicodedata


def norm(t):
    t = unicodedata.normalize("NFD", str(t or "").lower())
    return " ".join("".join(c for c in t if unicodedata.category(c) != "Mn").split())


RED_FLAGS = [
    r"dolor (fuerte )?(de|en el) pecho", r"me duele (mucho )?el pecho", r"opresion (en el )?pecho",
    r"(no puedo|no puede|dificultad para|cuesta|me cuesta) respirar", r"falta de aire", r"me ahogo", r"se ahoga",
    r"desmay", r"perdio el conocimiento", r"inconsciente", r"convulsi",
    r"sangrado (fuerte|abundante|que no para)", r"sangra mucho", r"vomit\w* sangre", r"tos con sangre",
    r"fiebre (muy )?alta.*(bebe|recien nacido|meses)", r"(bebe|recien nacido).*fiebre",
    r"embarazada.*(sangr|dolor|fiebre|contracc)", r"(sangr|dolor).*embarazada",
    r"(cara|boca|labios) (torcida|caida|dormid)", r"no puedo mover (el|la|un|una) (brazo|pierna)", r"derrame",
    r"infarto", r"sobredosis", r"me tome (todas|muchas) (las )?pastillas", r"intoxica", r"envenen",
    r"suicid", r"quitarme la vida", r"hacerme dano", r"no quiero vivir",
    r"reaccion alergica (grave|fuerte)", r"se me cierra la garganta", r"hinchazon (de|en) (la )?(cara|garganta|lengua)",
]
RED_RE = re.compile("|".join(RED_FLAGS))
DIAG_RE = re.compile(r"\b(que (enfermedad )?tengo|tengo (cancer|diabetes|covid|dengue|una infeccion)\s*\?|"
                     r"diagnostic\w*|sera que tengo|que me pasa|es grave lo que tengo)")
RX_RE = re.compile(r"\b(antibiotico|amoxicilina|azitromicina|oseltamivir|tamiflu|receta|clonazepam|tramadol|"
                   r"alprazolam|insulina|morfina|corticoide)")
HANDOFF_RE = re.compile(r"\b(hablar con (un|una|el|la)? ?(farmaceutic|persona|humano|asesor)|humano|asesor|farmaceutico real)")
# Afirmar una condición (regla dura §6). Mismo criterio que tests/llm/checks.py.
AFFIRM_RE = re.compile(r"\b(tienes|usted tiene|padeces|padece|sufres de|diagnostico de)\b", re.I)

COND_TERMS = {  # código CRM → regex de términos que NUNCA deben aparecer en texto visible
    "hipertension": r"hipertensi|presi[oó]n (alta|arterial)|coraz[oó]n",
    "artrosis": r"artrosis|artritis|articulaci",
    "rinitis": r"rinitis",
    "gastritis": r"gastritis",
    "diabetes": r"diabet|az[uú]car en la sangre",
}


def check_text(text, nlu=None):
    """→ dict(redFlag, diagnosis, rx, handoff, reasons)."""
    t = norm(text)
    reasons = []
    red = bool(RED_RE.search(t))
    if red:
        reasons.append("keyword_red_flag")
    intent = (nlu or {}).get("intent") or {}
    if intent.get("label") == "emergencia_medica" and float(intent.get("confidence") or 0) >= 0.8:
        red = True
        reasons.append("gliner_emergencia")
    diag = bool(DIAG_RE.search(t))
    rx = bool(RX_RE.search(t))
    ho = bool(HANDOFF_RE.search(t))
    return {"redFlag": red, "diagnosis": diag and not red, "rx": rx and not red, "handoff": ho and not red, "reasons": reasons}


def leaks(visible, profile=None):
    """Hits de condiciones del CRM o afirmaciones de condición en texto visible."""
    hits = []
    for c in (profile or {}).get("condiciones_probables") or []:
        pat = COND_TERMS.get(c, re.escape(c))
        if re.search(pat, visible, re.I) or re.search(pat, norm(visible), re.I):
            hits.append("condicion_crm")
    return hits


def otc_only(products):
    return [p for p in products if not p.get("requiere_receta")]
