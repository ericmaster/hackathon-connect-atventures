"""A/B STT local (sin Lambda): reutiliza tests/e2e/voice_live.stt con URL firmada local.
voice_live.stt() firma sin vocabulario; aquí se pasa FV_TRANSCRIBE_VOCABULARY (si existe).
No imprime credenciales ni URLs.

  /workspace/.venv-c/bin/python infra/transcribe/ab_test.py                 # sin vocab
  FV_TRANSCRIBE_VOCABULARY=connect-atv-meds /workspace/.venv-c/bin/python infra/transcribe/ab_test.py
"""
import asyncio, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tests", "e2e"))
import voice_live  # noqa: E402
voice = voice_live.voice

PHRASES = [
    "Quiero Buprex y Tempra para la gripe.",
    "Tienen Apronax?",
    "Soy cliente SmartClub de Medicity.",
    "Quiero algo para la gripe, tengo Buprex y Tempra en casa.",
    "Necesito Finalín y Dolo-Neurobión.",
    "Me da un Mucosolvan y Sal de Frutas Eno.",
    "Busco Lemonflu o Tapsin en Económicas.",
    "Tienen Enterogermina y Electrolit?",
]

vocab = os.environ.get("FV_TRANSCRIBE_VOCABULARY") or None
_orig = voice.presign_transcribe_url
voice.presign_transcribe_url = lambda *a, **k: _orig(*a, **{"vocabulary_name": vocab, **k})

for p in PHRASES:
    pcm = voice.synthesize_pcm16(p)
    r = asyncio.run(voice_live.stt(pcm))
    print(json.dumps({"vocab": vocab, "input": p, "final": r["final"]}, ensure_ascii=False), flush=True)
