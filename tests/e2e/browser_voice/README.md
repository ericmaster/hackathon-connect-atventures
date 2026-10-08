# Prueba de voz en Chrome headless (mic falso → app/src/lib/voice → Transcribe real)

Copia a /tmp/voicetest (rutas absolutas), `npm i playwright-core`, genera `speech.wav` (Polly PCM 16 kHz),
`vite build --config vite.config.mjs`, levanta `server.py` (127.0.0.1:8765, presigna con creds del box) y
`node run.mjs` / `node run.mjs deny` (permiso de mic negado → mensaje en español).
Resultado 8 oct 12:37: STT final exacto, 8 parciales; TTS reproduce; deny → `mic-denied`.
