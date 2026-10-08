// API de voz del Farmacéutico Virtual (workstream C).
//   startListening(onPartial, onFinal)  — mic → Transcribe es-US; parciales para mostrar, final para enviar
//   stopListening()                     — corta y emite el final
//   speak(text)                         — Polly Lupe vía /voice/tts (tras interacción del usuario)
// Auth: usa signedFetch de #lib/api/auth por defecto; setVoiceFetcher() para sustituirlo.
export { startListening, stopListening, cancelListening, isListening, type ListenOptions } from './stt';
export { speak, stopSpeaking, unlockAudio } from './tts';
export { setVoiceFetcher, type VoiceFetcher } from './fetcher';
export { VoiceError, MIC_DENIED_MESSAGE, type VoiceErrorCode } from './errors';

import { startListening, stopListening, cancelListening } from './stt';
import { speak, stopSpeaking } from './tts';
/** Objeto con la forma VoiceClient de B (#lib/voice-client.ts). */
export const voice = {
	simulated: false,
	startListening: (onPartial: (t: string) => void, onFinal: (t: string) => void) => startListening(onPartial, onFinal),
	stopListening,
	speak,
	cancel: () => {
		cancelListening();
		stopSpeaking();
	}
};
export default voice;
