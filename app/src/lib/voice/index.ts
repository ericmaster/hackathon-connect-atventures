// API de voz del Farmacéutico Virtual (workstream C).
//   startListening(onPartial, onFinal)  — mic → Transcribe es-US; parciales para mostrar, final para enviar
//   stopListening()                     — corta y emite el final
//   speak(text)                         — Polly Lupe vía /voice/tts (tras interacción del usuario)
// Integración: setVoiceFetcher(signedFetch) con el fetch SigV4 de $lib/api/auth.
export { startListening, stopListening, cancelListening, isListening, type ListenOptions } from './stt';
export { speak, stopSpeaking, unlockAudio } from './tts';
export { setVoiceFetcher, type VoiceFetcher } from './fetcher';
export { VoiceError, MIC_DENIED_MESSAGE, type VoiceErrorCode } from './errors';
