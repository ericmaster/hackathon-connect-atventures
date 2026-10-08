"""Voz del Farmacéutico Virtual (workstream C).

- presign_transcribe_url(): URL WebSocket SigV4 temporal para Amazon Transcribe
  streaming (es-US). Usa las credenciales del rol de la Lambda; nunca se loguea.
- synthesize(text): mp3 base64 con Polly Lupe (es-US), generative -> neural.

Sin dependencias además de boto3/botocore (incluidos en el runtime Lambda).
"""
from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import hmac
import os
import time
import urllib.parse

import boto3

REGION = os.environ.get("FV_VOICE_REGION") or os.environ.get("AWS_REGION") or "us-east-1"
TRANSCRIBE_PORT = 8443
TRANSCRIBE_PATH = "/stream-transcription-websocket"
URL_TTL_S = 300  # ~5 min
MAX_TTS_CHARS = int(os.environ.get("FV_TTS_MAX_CHARS", "400"))
POLLY_VOICE = os.environ.get("FV_TTS_VOICE", "Lupe")
POLLY_LANG = "es-US"
# Orden de motores; "neural,generative" o "neural" si generative tarda (~1,2 s vs ~0,2 s medido)
TTS_ENGINES = tuple(e.strip() for e in os.environ.get("FV_TTS_ENGINES", "generative,neural").split(",") if e.strip())
ALLOWED_LANGS = {"es-US", "es-ES", "en-US"}
ALLOWED_RATES = {8000, 16000}

_session = None
_polly = None


def _boto_session():
    global _session
    if _session is None:
        _session = boto3.session.Session()
    return _session


def _polly_client():
    global _polly
    if _polly is None:
        _polly = _boto_session().client("polly", region_name=REGION)
    return _polly


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _q(v: str) -> str:
    return urllib.parse.quote(str(v), safe="-_.~")


def presign_transcribe_url(
    language: str = "es-US",
    sample_rate: int = 16000,
    vocabulary_name: str | None = None,
    *,
    region: str | None = None,
    expires: int = URL_TTL_S,
    credentials=None,
    now: _dt.datetime | None = None,
) -> dict:
    """Devuelve {"url", "expiresAt", "language", "sampleRate", "mediaEncoding"}.

    `credentials` (objeto con access_key/secret_key/token) y `now` existen para
    tests offline. La URL firmada es un secreto de corta vida: no loguearla.
    """
    if language not in ALLOWED_LANGS:
        raise ValueError("language no permitido")
    if int(sample_rate) not in ALLOWED_RATES:
        raise ValueError("sample_rate no permitido")
    expires = max(1, min(int(expires), 300))
    region = region or REGION
    if credentials is None:
        c = _boto_session().get_credentials()
        if c is None:
            raise RuntimeError("sin credenciales AWS")
        credentials = c.get_frozen_credentials()
    now = now or _dt.datetime.now(_dt.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")
    service = "transcribe"
    host = f"transcribestreaming.{region}.amazonaws.com:{TRANSCRIBE_PORT}"
    scope = f"{datestamp}/{region}/{service}/aws4_request"

    params = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{credentials.access_key}/{scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires),
        "X-Amz-SignedHeaders": "host",
        "language-code": language,
        "media-encoding": "pcm",
        "sample-rate": str(int(sample_rate)),
    }
    if getattr(credentials, "token", None):
        params["X-Amz-Security-Token"] = credentials.token
    if vocabulary_name:
        params["vocabulary-name"] = vocabulary_name

    canonical_qs = "&".join(f"{_q(k)}={_q(v)}" for k, v in sorted(params.items()))
    payload_hash = hashlib.sha256(b"").hexdigest()
    canonical_request = "\n".join(
        ["GET", TRANSCRIBE_PATH, canonical_qs, f"host:{host}\n", "host", payload_hash]
    )
    string_to_sign = "\n".join(
        ["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical_request.encode()).hexdigest()]
    )
    k = _sign(("AWS4" + credentials.secret_key).encode(), datestamp)
    k = _sign(k, region)
    k = _sign(k, service)
    k = _sign(k, "aws4_request")
    signature = hmac.new(k, string_to_sign.encode(), hashlib.sha256).hexdigest()
    url = f"wss://{host}{TRANSCRIBE_PATH}?{canonical_qs}&X-Amz-Signature={signature}"
    return {
        "url": url,
        "expiresAt": int(now.timestamp()) + expires,
        "language": language,
        "sampleRate": int(sample_rate),
        "mediaEncoding": "pcm",
    }


def _clean_text(text: str) -> str:
    text = " ".join(str(text or "").split())
    if len(text) > MAX_TTS_CHARS:
        cut = text[:MAX_TTS_CHARS]
        # cortar en el último fin de frase/espacio para no partir palabras
        for sep in (". ", "? ", "! ", ", ", " "):
            i = cut.rfind(sep)
            if i > MAX_TTS_CHARS // 2:
                cut = cut[: i + 1]
                break
        text = cut.strip()
    return text


def synthesize(text: str, *, engines=None, client=None) -> dict:
    """Devuelve {"audio": base64 mp3, "format": "mp3", "engine", "voice", "chars", "ms"}.

    Texto plano (no SSML), recortado a MAX_TTS_CHARS. Si el motor generative
    falla (o no está disponible), usa neural.
    """
    text = _clean_text(text)
    if not text:
        raise ValueError("texto vacío")
    engines = engines or TTS_ENGINES
    client = client or _polly_client()
    last_err: Exception | None = None
    for engine in engines:
        t0 = time.perf_counter()
        try:
            r = client.synthesize_speech(
                Text=text,
                TextType="text",
                OutputFormat="mp3",
                SampleRate="24000",
                VoiceId=POLLY_VOICE,
                LanguageCode=POLLY_LANG,
                Engine=engine,
            )
            audio = r["AudioStream"].read()
            return {
                "audio": base64.b64encode(audio).decode("ascii"),
                "format": "mp3",
                "contentType": "audio/mpeg",
                "engine": engine,
                "voice": POLLY_VOICE,
                "chars": len(text),
                "ms": int((time.perf_counter() - t0) * 1000),
            }
        except Exception as e:  # noqa: BLE001 - fallback al siguiente motor
            last_err = e
    raise RuntimeError(f"Polly falló: {type(last_err).__name__}") from last_err


def synthesize_pcm16(text: str, engine: str = "neural") -> bytes:
    """PCM16 16 kHz mono (para pruebas STT). No lo usa la API."""
    r = _polly_client().synthesize_speech(
        Text=_clean_text(text), OutputFormat="pcm", SampleRate="16000",
        VoiceId=POLLY_VOICE, LanguageCode=POLLY_LANG, Engine=engine,
    )
    return r["AudioStream"].read()


# --- Handlers opcionales para la Lambda de A -------------------------------------
def handle_stt_url(body: dict | None = None) -> dict:
    body = body or {}
    return presign_transcribe_url(
        language=body.get("language", "es-US"),
        sample_rate=int(body.get("sampleRate", 16000)),
        vocabulary_name=os.environ.get("FV_TRANSCRIBE_VOCABULARY") or None,
    )


def handle_tts(body: dict | None = None) -> dict:
    body = body or {}
    return synthesize(body.get("text", ""))
