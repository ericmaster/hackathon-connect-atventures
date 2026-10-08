"""GLiNER2.5-multi-Decide handler. Lambda entry = handler. Local: python app.py "texto"..."""
import json, os, time

MODEL_ID = os.environ.get("MODEL_ID", "fastino/GLiNER2.5-multi-Decide")
MODEL_DIR = os.environ.get("MODEL_DIR")  # local weights dir
MODEL_S3 = os.environ.get("MODEL_S3")  # s3://bucket/prefix/ -> /tmp/model on cold start (beats lazy image load)
ENT_TH = float(os.environ.get("ENT_THRESHOLD", "0.15"))

# intent id -> label text the model sees. Short EN phrases scored best (descriptions hurt).
INTENTS = {
    "buscar_producto": "buy medicine or product",
    "consulta_sintoma": "ask about a symptom",
    "dar_cedula": "give ID number",
    "farmacia_cercana": "find nearest pharmacy",
    "checkout": "pay",
    "emergencia_medica": "medical emergency",
    "saludo": "greeting",
    "otro": "other",
}
# entity -> description. Order/wording matters (tuned on synthetic ES set).
ENTITIES = {
    "sintoma": "síntoma o enfermedad, ej. gripe, fiebre, tos, dolor de pecho",
    "cedula": "número de cédula ecuatoriana de 10 dígitos",
    "ubicacion": "ciudad, lugar o dirección",
    "producto": "medicine, brand or pharmacy product name, e.g. paracetamol, ibuprofen, sunscreen",
}

_model, LOAD_S, IO_S, _cold = None, None, None, True


def _s3_fetch(uri, dst="/tmp/model"):
    import boto3
    from boto3.s3.transfer import TransferConfig
    bucket, prefix = uri[5:].split("/", 1)
    s3, cfg = boto3.client("s3"), TransferConfig(max_concurrency=16, multipart_chunksize=16 << 20)
    for o in s3.list_objects_v2(Bucket=bucket, Prefix=prefix)["Contents"]:
        out = os.path.join(dst, o["Key"][len(prefix):].lstrip("/"))
        if not os.path.exists(out) or os.path.getsize(out) != o["Size"]:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            s3.download_file(bucket, o["Key"], out, Config=cfg)
    return dst


def _get():
    # lazy: Lambda init phase caps at 10s, load in first invoke instead
    global _model, LOAD_S, IO_S, MODEL_DIR
    if _model is None:
        t0 = time.time()
        if MODEL_S3:
            MODEL_DIR = _s3_fetch(MODEL_S3)
            IO_S = round(time.time() - t0, 2)
        import torch
        from gliner2 import AutoExtractor
        torch.set_num_threads(int(os.environ.get("THREADS", os.cpu_count() or 2)))
        _model = AutoExtractor.from_pretrained(MODEL_DIR or MODEL_ID)
        LOAD_S = round(time.time() - t0, 2)
    return _model


def predict(text, intents=None, entities=None, threshold=None):
    """intents: list of ids or {id: label_text}. entities: list or {name: description}."""
    m = _get()
    it = intents or INTENTS
    it = it if isinstance(it, dict) else {i: i for i in it}
    back = {v: k for k, v in it.items()}
    t = time.time()
    c = m.classify_text(text, {"intent": list(back)}, include_confidence=True)["intent"]
    e = m.extract_entities(text, entities or ENTITIES, threshold=threshold or ENT_TH,
                           include_confidence=True)["entities"]
    ms = round((time.time() - t) * 1000, 1)
    return {"intent": {"label": back.get(c["label"], c["label"]), "confidence": round(c["confidence"], 3)},
            "entities": {k: [{"text": x["text"], "confidence": round(x["confidence"], 3)} for x in v]
                         for k, v in e.items() if v}}, ms


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
        out, ms = predict(tx, event.get("intents"), event.get("entities"), event.get("threshold"))
        res.append({"text": tx, "ms": ms, "out": out})
    return {"model": MODEL_ID, "cold": cold, "load_s": LOAD_S, "io_s": IO_S, "results": res}


if __name__ == "__main__":
    import resource, sys
    U = sys.argv[1:] or [
        "hola, buenos días",
        "quiero algo para la gripe",
        "mi cédula es 1710034065",
        "¿dónde está la farmacia más cercana?",
        "quiero pagar",
        "me duele el pecho y no puedo respirar",
        "quiero comprar paracetamol en Quito",
        "tengo fiebre y tos desde ayer",
    ]
    r = handler({"texts": U})
    print(json.dumps(r, ensure_ascii=False, indent=1))
    print("load_s", LOAD_S, "maxrss_MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024)
