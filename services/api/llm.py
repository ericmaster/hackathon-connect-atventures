"""Bedrock (Claude Haiku 4.5) con throttle global (≥1,1 s entre llamadas, lock condicional en DynamoDB)
y backoff exponencial con jitter (máx. 2 reintentos por throttling)."""
import json
import os
import random
import time
from pathlib import Path

from store import get_store

MODEL = os.environ.get("FV_LLM_MODEL", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
TEMPERATURE = os.environ.get("FV_LLM_TEMPERATURE", "0.1")
GAP_MS = int(os.environ.get("FV_BEDROCK_GAP_MS", "1100"))
MAX_THROTTLE_RETRIES = 2
THROTTLE = {"ThrottlingException", "TooManyRequestsException", "ServiceUnavailableException", "ModelNotReadyException"}
_HERE = Path(__file__).parent
_PROMPT = None
_client = None


def system_prompt():
    global _PROMPT
    if _PROMPT is None:
        for p in (_HERE / "system_prompt.md", _HERE.parent.parent / "tests" / "llm" / "system_prompt.md"):
            if p.exists():
                _PROMPT = p.read_text()
                break
    return _PROMPT


def _brt():
    global _client
    if _client is None:
        import boto3
        from botocore.config import Config
        _client = boto3.client("bedrock-runtime", config=Config(read_timeout=10, connect_timeout=3,
                                                                retries={"total_max_attempts": 1, "mode": "standard"}))
    return _client


def wait_slot(deadline):
    slot = get_store().reserve_slot(GAP_MS)
    delay = slot / 1000 - time.time()
    if time.time() + max(0, delay) > deadline:
        raise TimeoutError("no slot before deadline")
    if delay > 0:
        time.sleep(delay)


def generate(context, deadline, extra_user=None):
    """→ dict(ok, text, ms, retries, error). Respeta el presupuesto `deadline` (epoch s)."""
    user = "CONTEXTO DEL TURNO (JSON):\n" + json.dumps(context, ensure_ascii=False)
    if extra_user:
        user += "\n\n" + extra_user
    inf = {"maxTokens": 2500}
    if TEMPERATURE not in ("", "none", "None"):
        inf["temperature"] = float(TEMPERATURE)
    req = dict(modelId=MODEL, system=[{"text": system_prompt()}],
               messages=[{"role": "user", "content": [{"text": user}]}], inferenceConfig=inf)
    retries, err = 0, None
    for attempt in range(MAX_THROTTLE_RETRIES + 1):
        try:
            wait_slot(deadline)
        except TimeoutError as e:
            return {"ok": False, "error": str(e), "retries": retries, "ms": 0}
        t0 = time.time()
        try:
            r = _brt().converse(**req)
            text = "".join(b.get("text", "") for b in r["output"]["message"]["content"])
            return {"ok": True, "text": text, "ms": int((time.time() - t0) * 1000), "retries": retries,
                    "usage": r.get("usage", {})}
        except Exception as e:  # noqa: BLE001
            code = getattr(e, "response", {}).get("Error", {}).get("Code", type(e).__name__)
            err = f"{code}"
            if code not in THROTTLE or attempt == MAX_THROTTLE_RETRIES:
                break
            retries += 1
            sleep = min(4.0, 1.0 * 2 ** attempt) + random.uniform(0, 0.4)
            if time.time() + sleep + 11 > deadline:
                break
            time.sleep(sleep)
    return {"ok": False, "error": err, "retries": retries, "ms": 0}
