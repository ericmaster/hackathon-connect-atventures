"""Intención + entidades: GLiNER (Lambda connect-atv-gliner) con fallback por palabras clave."""
import json
import os
import re
import time

from guardrails import norm

GLINER_FN = os.environ.get("FV_GLINER_FUNCTION", "connect-atv-gliner")
GLINER_TIMEOUT = float(os.environ.get("FV_GLINER_TIMEOUT_S", "4"))
_client = None

KEYWORDS = [
    ("emergencia_medica", r"pecho|respirar|desmay|convulsi|sangr|911|emergencia|infarto|ahogo"),
    ("checkout", r"\b(pagar|reservar|confirmar|comprar ya|checkout|eso es todo)\b"),
    ("farmacia_cercana", r"farmacia|sucursal|cerca|donde (queda|esta)|horario"),
    ("dar_cedula", r"\b\d{10}\b|cedula"),
    ("consulta_sintoma", r"gripe|fiebre|tos|dolor|garganta|resfri|diarrea|alergi|acidez|estornud|congest|mareo|"
                         r"vomit|picazon|me duele|malestar|ojos|herida|quemadura|\bsol\b"),
    ("buscar_producto", r"quiero|necesito|busco|tienen|venden|precio|cuanto cuesta|paracetamol|ibuprofeno|vitamina|"
                        r"panal|protector|crema|desodorante|alcohol|curita|termometro|jarabe|suero|algo para"),
    ("saludo", r"^(hola|buen[oa]s|que tal|saludos)"),
]
SYMPTOMS = r"(gripe|fiebre|tos|dolor de cabeza|dolor|garganta|resfriado|diarrea|alergia|acidez|estornudos|congestion|" \
           r"vomito|picazon|ojos secos|herida|quemadura|insolacion|malestar)"


def keyword_nlu(text):
    t = norm(text)
    label = next((lab for lab, pat in KEYWORDS if re.search(pat, t)), "otro")
    ents = {}
    sym = re.findall(SYMPTOMS, t)
    if sym:
        ents["sintoma"] = [{"text": s, "confidence": 1.0} for s in dict.fromkeys(sym)]
    return {"intent": {"label": label, "confidence": 0.6}, "entities": ents, "source": "keywords"}


def gliner(text):
    """→ (nlu, info). Nunca lanza; si GLiNER está frío o falla, usa palabras clave."""
    global _client
    t0 = time.time()
    if os.environ.get("FV_GLINER_DISABLED") == "1":
        return keyword_nlu(text), {"source": "keywords", "reason": "disabled", "ms": 0}
    try:
        if _client is None:
            import boto3
            from botocore.config import Config
            _client = boto3.client("lambda", config=Config(read_timeout=GLINER_TIMEOUT, connect_timeout=2,
                                                           retries={"total_max_attempts": 1, "mode": "standard"}))
        r = _client.invoke(FunctionName=GLINER_FN, Payload=json.dumps({"texts": [text]}).encode())
        body = json.loads(r["Payload"].read() or b"{}")
        if r.get("FunctionError") or not body.get("results"):
            raise RuntimeError("gliner_error")
        out = body["results"][0]["out"]
        out["source"] = "gliner"
        # Complementa entidades con palabras clave si GLiNER no extrajo síntoma.
        kw = keyword_nlu(text)
        if not out.get("entities", {}).get("sintoma") and kw["entities"].get("sintoma"):
            out.setdefault("entities", {})["sintoma"] = kw["entities"]["sintoma"]
        return out, {"source": "gliner", "cold": body.get("cold"), "ms": int((time.time() - t0) * 1000)}
    except Exception as e:  # noqa: BLE001 — timeout/frío/permiso → fallback
        return keyword_nlu(text), {"source": "keywords", "reason": type(e).__name__, "ms": int((time.time() - t0) * 1000)}


def warm():
    """Invocación asíncrona (Event) para calentar GLiNER sin esperar."""
    try:
        import boto3
        boto3.client("lambda").invoke(FunctionName=GLINER_FN, InvocationType="Event",
                                      Payload=json.dumps({"texts": ["hola"]}).encode())
        return True
    except Exception:  # noqa: BLE001
        return False
