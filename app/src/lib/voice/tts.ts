// TTS: /voice/tts → mp3 base64 (Polly Lupe). Reproducir solo tras interacción del usuario.
import { VoiceError } from './errors';
import { postJson } from './fetcher';

interface TtsResponse {
	audio: string;
	contentType?: string;
	engine?: string;
}

let audioEl: HTMLAudioElement | null = null;
let currentUrl: string | null = null;
let ctrl: AbortController | null = null;

const SILENT_MP3 =
	'data:audio/mpeg;base64,SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQxAADB8AhSmxhIIEVCSiJrDCQBTcu3UrAIwUdkRgQbFAZC1CQEwTJ9mjRvBA4UOLD8nKVOWfh+UlK3z/177OXrfOdKl7pyn3Xf//WreyTRUoAWgBgkOAGbZHBgG1OF6zM82DWbZaUmMBptgQhGjsyYqc9ae9XFz280948NMBWInljyzsNRFLPWdnZGWrddDsjK1unuSrVN9jJsK8KuQtQCtMBjCEtImISdNKJOopIpBFpNSMbIHCSRpRR5iakjTiyzLhchUUBwCgyKiweBv/7UsQbg8isVNoMPMjAAAA0gAAABEVFGmgqK////9bP/6XCykxBTUUzLjEwMKqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq';

function el(): HTMLAudioElement {
	if (!audioEl) {
		audioEl = new Audio();
		audioEl.preload = 'auto';
	}
	return audioEl;
}

// Desbloqueo automático con el primer toque/tecla del usuario (políticas de autoplay).
if (typeof window !== 'undefined') {
	const once = () => {
		unlockAudio();
		window.removeEventListener('pointerdown', once, true);
		window.removeEventListener('keydown', once, true);
	};
	window.addEventListener('pointerdown', once, true);
	window.addEventListener('keydown', once, true);
}

/** Llamar desde un toque del usuario (p. ej. el primer botón) para desbloquear audio en iOS/Chrome. */
export function unlockAudio(): void {
	const a = el();
	a.src = SILENT_MP3;
	a.play().catch(() => undefined);
}

export function stopSpeaking(): void {
	ctrl?.abort();
	ctrl = null;
	if (audioEl) {
		audioEl.pause();
		audioEl.removeAttribute('src');
	}
	if (currentUrl) URL.revokeObjectURL(currentUrl);
	currentUrl = null;
}

function b64ToBlob(b64: string, type: string): Blob {
	const bin = atob(b64);
	const bytes = new Uint8Array(bin.length);
	for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
	return new Blob([bytes], { type });
}

/** Sintetiza y reproduce `text`. Resuelve al terminar el audio. Interrumpe cualquier audio previo. */
export async function speak(text: string): Promise<void> {
	const t = text?.trim();
	if (!t) return;
	stopSpeaking();
	const c = new AbortController();
	ctrl = c;
	let r: TtsResponse;
	try {
		r = await postJson<TtsResponse>('/voice/tts', { text: t.slice(0, 400) }, c.signal);
		if (!r?.audio) throw new Error('sin audio');
	} catch (e) {
		if (c.signal.aborted) return;
		throw new VoiceError('tts', String(e));
	}
	if (c.signal.aborted) return;
	const a = el();
	currentUrl = URL.createObjectURL(b64ToBlob(r.audio, r.contentType ?? 'audio/mpeg'));
	a.src = currentUrl;
	await new Promise<void>((resolve, reject) => {
		a.onended = () => resolve();
		a.onerror = () => reject(new VoiceError('tts', 'playback'));
		c.signal.addEventListener('abort', () => resolve(), { once: true });
		a.play().catch((e) => reject(new VoiceError('tts', String(e))));
	});
}
