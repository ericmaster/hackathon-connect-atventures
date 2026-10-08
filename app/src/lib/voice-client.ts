// Interfaz de voz que implementa workstream C en app/src/lib/voice/index.ts
// (export `voice` o default con esta forma). Si no existe, usamos el fake (voz SIMULADA).
export interface VoiceClient {
	/** true si es la implementación simulada. */
	readonly simulated?: boolean;
	startListening(onPartial: (text: string) => void, onFinal: (text: string) => void): Promise<void> | void;
	stopListening(): void;
	speak(text: string): Promise<void> | void;
	/** Opcional: detener audio en curso (Reiniciar demo). */
	cancel?(): void;
}

let fakePhrase = 'algo para la gripe';
/** El shell indica qué frase simular según el paso actual (solo voz fake). */
export function setFakePhrase(p: string) {
	fakePhrase = p;
}

let timers: ReturnType<typeof setTimeout>[] = [];
export const fakeVoice: VoiceClient = {
	simulated: true,
	startListening(onPartial, onFinal) {
		const words = fakePhrase.split(' ');
		words.forEach((_, i) => timers.push(setTimeout(() => onPartial(words.slice(0, i + 1).join(' ')), 300 * (i + 1))));
		timers.push(setTimeout(() => onFinal(fakePhrase), 300 * words.length + 400));
	},
	stopListening() {
		timers.forEach(clearTimeout);
		timers = [];
	},
	speak() {
		/* no-op: TTS lo provee C */
	},
	cancel() {
		this.stopListening();
	}
};

const mods = import.meta.glob('./voice/index.ts');
type VoiceMod = Partial<VoiceClient> & { voice?: VoiceClient; default?: VoiceClient; cancelListening?: () => void; stopSpeaking?: () => void };
/** Carga la voz real de C (solo si `real`, p. ej. transporte http); si no, voz simulada. */
export async function loadVoice(real: boolean): Promise<VoiceClient> {
	const load = mods['./voice/index.ts'];
	if (real && load) {
		try {
			const m = (await load()) as VoiceMod;
			const v = m.voice ?? m.default;
			if (v && typeof v.startListening === 'function') return v;
			if (typeof m.startListening === 'function' && m.stopListening && m.speak) {
				return {
					simulated: false,
					startListening: m.startListening,
					stopListening: m.stopListening,
					speak: m.speak,
					cancel: () => (m.cancelListening?.(), m.stopSpeaking?.())
				};
			}
		} catch (e) {
			console.warn('[voice] módulo de C falló, uso voz simulada', e);
		}
	}
	return fakeVoice;
}
