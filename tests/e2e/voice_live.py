"""Prueba viva STT/TTS desde el box (credenciales locales). No imprime credenciales ni URLs.

/workspace/.venv-c/bin/python tests/e2e/voice_live.py
Necesita: boto3, websockets.
"""
import asyncio
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "services", "api"))
sys.path.insert(0, HERE)
import voice  # noqa: E402
import eventstream  # noqa: E402
import websockets  # noqa: E402

PHRASES = [
    "Mi cédula es uno siete uno cero cero tres cuatro cero seis cinco.",
    "Quiero algo para la gripe, tengo Buprex y Tempra en casa.",
]


def presign_via_lambda():
    """URL firmada por la Lambda desplegada (credenciales del rol), por invoke directo."""
    import smoke
    st, b, _ = smoke.Invoker("boto3")(smoke.event("POST", "/voice/stt-url", {"language": "es-US", "sampleRate": 16000}))
    if st != 200:
        raise RuntimeError(f"stt-url via Lambda → {st}")
    return b


VIA_LAMBDA = "--via-lambda" in sys.argv


async def stt(pcm: bytes, realtime: bool = True):
    t0 = time.perf_counter()
    info = presign_via_lambda() if VIA_LAMBDA else voice.presign_transcribe_url()
    t_presign = (time.perf_counter() - t0) * 1000
    partials, finals = [], []
    t_audio_end = None
    t_final = None
    async with websockets.connect(info["url"], max_size=None, open_timeout=10) as ws:
        t_open = (time.perf_counter() - t0) * 1000

        async def sender():
            nonlocal t_audio_end
            chunk = 3200  # 100 ms a 16 kHz PCM16
            for i in range(0, len(pcm), chunk):
                await ws.send(eventstream.audio_event(pcm[i : i + chunk]))
                if realtime:
                    await asyncio.sleep(0.1)
            await ws.send(eventstream.audio_event(b"\x00" * 3200 * 5))  # 0.5 s silencio
            t_audio_end = time.perf_counter()
            await ws.send(eventstream.audio_event(b""))  # fin de stream

        async def receiver():
            nonlocal t_final
            async for msg in ws:
                h, body = eventstream.parse_json(msg)
                if h.get(":message-type") != "event":
                    raise RuntimeError(f"{h.get(':exception-type') or h.get(':error-code')}: {body}")
                for r in (body or {}).get("Transcript", {}).get("Results", []):
                    alt = r["Alternatives"][0]["Transcript"] if r.get("Alternatives") else ""
                    if r.get("IsPartial"):
                        partials.append(alt)
                    else:
                        finals.append(alt)
                        t_final = time.perf_counter()

        await asyncio.gather(sender(), receiver())
    lag = (t_final - t_audio_end) * 1000 if (t_final and t_audio_end) else None
    return {"presign_ms": round(t_presign), "open_ms": round(t_open), "partials": len(partials),
            "final": " ".join(finals), "final_after_audio_end_ms": round(lag) if lag is not None else None}


def main():
    ok = True
    r = voice.synthesize("Hola, soy tu Farmacéutico Virtual. ¿En qué te ayudo hoy?")
    print(f"TTS mp3: engine={r['engine']} bytes={len(r['audio']) * 3 // 4} polly_ms={r['ms']}")
    rn = voice.synthesize("Hola, ¿me repites tu cédula?", engines=("neural",))
    print(f"TTS mp3 neural: bytes={len(rn['audio']) * 3 // 4} polly_ms={rn['ms']}")
    for p in PHRASES:
        pcm = voice.synthesize_pcm16(p)
        res = asyncio.run(stt(pcm))
        print(json.dumps({"input": p, "audio_s": round(len(pcm) / 32000, 1), **res}, ensure_ascii=False))
        ok = ok and bool(res["final"])
    print("LIVE", "(URL firmada por la Lambda)" if VIA_LAMBDA else "(URL firmada local)", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
