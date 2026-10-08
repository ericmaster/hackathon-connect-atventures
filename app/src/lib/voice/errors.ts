export type VoiceErrorCode = 'mic-denied' | 'mic-unavailable' | 'unsupported' | 'network' | 'stt' | 'tts' | 'busy';

export const MIC_DENIED_MESSAGE =
	'No tengo permiso para usar tu micrófono. Para hablarme, toca el candado junto a la dirección del navegador y permite el micrófono. Mientras tanto, puedes escribirme abajo.';

const MESSAGES: Record<VoiceErrorCode, string> = {
	'mic-denied': MIC_DENIED_MESSAGE,
	'mic-unavailable': 'No encuentro un micrófono disponible. Puedes escribirme abajo.',
	unsupported: 'Tu navegador no permite usar la voz aquí. Puedes escribirme abajo.',
	network: 'No pude conectar el servicio de voz. Intenta de nuevo o escríbeme abajo.',
	stt: 'No pude entender el audio. Intenta de nuevo o escríbeme abajo.',
	tts: 'No pude reproducir la respuesta en voz alta.',
	busy: 'Ya te estoy escuchando.'
};

export class VoiceError extends Error {
	readonly code: VoiceErrorCode;
	/** Mensaje en español, listo para mostrar al usuario. */
	readonly userMessage: string;
	constructor(code: VoiceErrorCode, detail?: string) {
		super(detail ? `${code}: ${detail}` : code);
		this.name = 'VoiceError';
		this.code = code;
		this.userMessage = MESSAGES[code];
	}
}
