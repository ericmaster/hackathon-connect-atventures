"""GLiNER2.5-Decide handler. Lambda entry = handler. Local: python app.py"""
import json, os, time

MODEL_ID = os.environ.get("MODEL_ID", "fastino/GLiNER2.5-Decide")
MODEL_DIR = os.environ.get("MODEL_DIR")  # baked weights path in image

INTENTS = {
    "buscar_producto": "user wants to find or buy a medicine or product",
    "consulta_sintoma": "user describes a symptom or asks what to take",
    "dar_cedula": "user gives their ID number (cedula)",
    "farmacia_cercana": "user asks for the nearest pharmacy or store location",
    "checkout": "user wants to pay or finish the purchase",
    "emergencia_medica": "medical emergency: chest pain, cannot breathe, fainting, severe bleeding",
    "saludo": "greeting",
    "otro": "anything else",
}
ENTITIES = {
    "sintoma": "symptom or illness",
    "producto": "medicine or pharmacy product",
    "cedula": "national ID number",
    "ubicacion": "place, city or address",
}

_model, LOAD_S, _cold = None, None, True


def _get():
    # lazy: Lambda init phase caps at 10s, load in first invoke instead
    global _model, LOAD_S
    if _model is None:
        t0 = time.time()
        import torch
        from gliner2 import AutoExtractor
        torch.set_num_threads(int(os.environ.get("THREADS", os.cpu_count() or 2)))
        _model = AutoExtractor.from_pretrained(MODEL_DIR or MODEL_ID)
        LOAD_S = round(time.time() - t0, 2)
    return _model


def predict(text, intents=None, entities=None, threshold=0.4):
    m = _get()
    s = m.create_schema()
    s = s.classification("intent", intents or INTENTS)
    s = s.entities(entities or ENTITIES)
    t = time.time()
    out = m.extract(text, s, threshold=threshold, include_confidence=True)
    return out, round((time.time() - t) * 1000, 1)


def handler(event, context=None):
    global _cold
    cold, _cold = _cold, False
    if isinstance(event, str):
        event = json.loads(event)
    if "body" in event and isinstance(event["body"], str):  # function URL
        event = json.loads(event["body"])
    _get()
    texts = event.get("texts") or [event.get("text", "")]
    res = []
    for tx in texts:
        out, ms = predict(tx, event.get("intents"), event.get("entities"), event.get("threshold", 0.4))
        res.append({"text": tx, "ms": ms, "out": out})
    return {"model": MODEL_ID, "cold": cold, "load_s": LOAD_S, "results": res}


if __name__ == "__main__":
    import resource, sys
    U = sys.argv[1:] or [
        "hola, buenos días",
        "quiero algo para la gripe",
        "mi cédula es 1710034065",
        "¿dónde está la farmacia más cercana?",
        "quiero pagar",
        "me duele el pecho y no puedo respirar",
    ]
    r = handler({"texts": U})
    print(json.dumps(r, ensure_ascii=False, indent=1))
    print("load_s", LOAD_S, "maxrss_MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024)
