"""Cliente Bedrock mínimo para el harness: ConverseStream + límite 1 RPS + backoff.

Sin dependencias fuera de boto3. Las credenciales salen de ~/.aws (nunca se imprimen).
"""
import random
import threading
import time

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError, EventStreamError

MIN_GAP_S = 1.1  # Bedrock: máx. 1 RPS en el evento → >= 1,1 s entre llamadas
RETRYABLE = {
    "ThrottlingException", "ServiceUnavailableException", "ModelNotReadyException",
    "TooManyRequestsException", "InternalServerException", "ModelTimeoutException",
}


class RateLimiter:
    """Garantiza un espacio mínimo entre el *inicio* de dos llamadas (proceso entero)."""

    def __init__(self, gap_s=MIN_GAP_S):
        self.gap_s, self._last, self._lock = gap_s, 0.0, threading.Lock()

    def wait(self):
        with self._lock:
            delta = time.monotonic() - self._last
            if delta < self.gap_s:
                time.sleep(self.gap_s - delta)
            self._last = time.monotonic()


LIMITER = RateLimiter()


def client(region="us-east-1"):
    # Reintentos propios (abajo); los de botocore se apagan para no romper el 1 RPS.
    cfg = Config(region_name=region, retries={"max_attempts": 1, "mode": "standard"}, read_timeout=120)
    return boto3.client("bedrock-runtime", config=cfg)


def _err_code(e):
    if isinstance(e, ClientError):
        return e.response.get("Error", {}).get("Code", "")
    if isinstance(e, EventStreamError):
        return e.response.get("Error", {}).get("Code", "") if hasattr(e, "response") else ""
    return ""


def converse_stream(brt, model_id, system, user, temperature=0.2, max_tokens=3000,
                    system_in_user=False, max_attempts=6, extra=None, output_config=None):
    """Una llamada ConverseStream. Devuelve dict con texto, tokens, ttft y latencia.

    - ttft_s: tiempo hasta el primer delta de *texto* (ignora el razonamiento).
    - latency_s: hasta el final del stream (incluye razonamiento si lo hay).
    - retries: reintentos por throttling/5xx (backoff exponencial con jitter).
    """
    if system_in_user:
        messages = [{"role": "user", "content": [{"text": system + "\n\n---\n\n" + user}]}]
        sys_blocks = None
    else:
        messages = [{"role": "user", "content": [{"text": user}]}]
        sys_blocks = [{"text": system}]
    inf = {"maxTokens": max_tokens}
    if temperature is not None:  # Haiku 5.5 rechaza temperature ("deprecated for this model")
        inf["temperature"] = temperature
    req = dict(modelId=model_id, messages=messages, inferenceConfig=inf)
    if output_config:
        req["outputConfig"] = output_config
    if sys_blocks:
        req["system"] = sys_blocks
    if extra:
        req["additionalModelRequestFields"] = extra

    retries, last_err = 0, None
    for attempt in range(max_attempts):
        LIMITER.wait()
        t0 = time.monotonic()
        try:
            resp = brt.converse_stream(**req)
            text, reasoning, ttft, usage, stop, server_ms = [], [], None, {}, None, None
            for ev in resp["stream"]:
                if "contentBlockDelta" in ev:
                    d = ev["contentBlockDelta"]["delta"]
                    if "text" in d:
                        if ttft is None:
                            ttft = time.monotonic() - t0
                        text.append(d["text"])
                    elif "reasoningContent" in d:
                        reasoning.append(d["reasoningContent"].get("text", ""))
                elif "messageStop" in ev:
                    stop = ev["messageStop"].get("stopReason")
                elif "metadata" in ev:
                    usage = ev["metadata"].get("usage", {})
                    server_ms = ev["metadata"].get("metrics", {}).get("latencyMs")
                else:
                    for k in ("throttlingException", "serviceUnavailableException",
                              "modelStreamErrorException", "internalServerException"):
                        if k in ev:
                            raise RuntimeError(f"stream:{k}")
            return {
                "ok": True, "text": "".join(text), "reasoning_chars": len("".join(reasoning)),
                "ttft_s": ttft, "latency_s": time.monotonic() - t0, "server_latency_ms": server_ms,
                "input_tokens": usage.get("inputTokens"), "output_tokens": usage.get("outputTokens"),
                "stop_reason": stop, "retries": retries,
            }
        except (ClientError, EventStreamError, RuntimeError) as e:
            code = _err_code(e) or str(e)
            last_err = f"{type(e).__name__}:{code}:{str(e)[:300]}"
            retryable = code in RETRYABLE or "throttl" in str(e).lower() or str(e).startswith("stream:")
            if not retryable or attempt == max_attempts - 1:
                break
            retries += 1
            time.sleep(min(30, (2 ** attempt) * 1.5) + random.uniform(0, 0.5))
    return {"ok": False, "error": last_err, "retries": retries, "text": ""}
