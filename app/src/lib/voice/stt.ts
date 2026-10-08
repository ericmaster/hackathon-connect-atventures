// STT: Amazon Transcribe streaming (es-US) vía URL WebSocket presignada por la API.
import { audioEvent, decodeJson } from './eventstream';
import { VoiceError } from './errors';
import { postJson } from './fetcher';
import { startMic, TARGET_RATE, type MicHandle } from './mic';

export interface ListenOptions {
	/** Corte automático tras este silencio después de un resultado final (ms). 0 = solo manual. */
	endSilenceMs?: number;
	/** Duración máxima de la escucha (ms). */
	maxMs?: number;
	onError?: (e: VoiceError) => void;
	onState?: (s: 'connecting' | 'listening' | 'finishing' | 'idle') => void;
}

interface SttUrl {
	url: string;
	expiresAt?: number;
}

interface TranscriptResult {
	IsPartial?: boolean;
	Alternatives?: { Transcript?: string }[];
}

let session: Session | null = null;

class Session {
	private ws: WebSocket | null = null;
	private mic: MicHandle | null = null;
	private finals: string[] = [];
	private partial = '';
	private queue: Uint8Array[] = [];
	private done = false;
	private silenceTimer: ReturnType<typeof setTimeout> | null = null;
	private maxTimer: ReturnType<typeof setTimeout> | null = null;
	private closeTimer: ReturnType<typeof setTimeout> | null = null;

	constructor(
		private onPartial: (t: string) => void,
		private onFinal: (t: string) => void,
		private opts: Required<Pick<ListenOptions, 'endSilenceMs' | 'maxMs'>> & ListenOptions
	) {}

	async start(): Promise<void> {
		this.opts.onState?.('connecting');
		// Mic primero (gesto del usuario) y URL en paralelo.
		const urlP = postJson<SttUrl>('/voice/stt-url', { language: 'es-US', sampleRate: TARGET_RATE });
		urlP.catch(() => undefined);
		try {
			this.mic = await startMic((pcm) => this.send(pcm));
		} catch (e) {
			this.done = true;
			throw e;
		}
		let info: SttUrl;
		try {
			info = await urlP;
			if (!info?.url) throw new Error('sin url');
		} catch (e) {
			this.teardown();
			throw new VoiceError('network', String(e));
		}
		if (this.done) return; // stop() antes de conectar
		await new Promise<void>((resolve, reject) => {
			const ws = new WebSocket(info.url);
			ws.binaryType = 'arraybuffer';
			this.ws = ws;
			ws.onopen = () => {
				for (const q of this.queue) ws.send(audioEvent(q));
				this.queue = [];
				this.opts.onState?.('listening');
				resolve();
			};
			ws.onmessage = (ev) => this.onMessage(ev.data as ArrayBuffer);
			ws.onerror = () => {
				if (ws.readyState !== WebSocket.OPEN) reject(new VoiceError('network', 'ws'));
			};
			ws.onclose = () => this.finish();
		}).catch((e) => {
			this.teardown();
			throw e;
		});
		this.maxTimer = setTimeout(() => this.stop(), this.opts.maxMs);
	}

	private send(pcm: Uint8Array) {
		if (this.done) return;
		if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(audioEvent(pcm));
		else if (this.queue.length < 50) this.queue.push(pcm); // ≤5 s de buffer mientras conecta
	}

	private text(): string {
		return [...this.finals, this.partial].filter(Boolean).join(' ').trim();
	}

	private onMessage(data: ArrayBuffer) {
		let msg: { headers: Record<string, string>; body: unknown };
		try {
			msg = decodeJson(data);
		} catch {
			return;
		}
		if (msg.headers[':message-type'] !== 'event') {
			this.opts.onError?.(new VoiceError('stt', msg.headers[':exception-type'] ?? 'exception'));
			this.finish();
			return;
		}
		const results =
			(msg.body as { Transcript?: { Results?: TranscriptResult[] } })?.Transcript?.Results ?? [];
		for (const r of results) {
			const t = r.Alternatives?.[0]?.Transcript ?? '';
			if (r.IsPartial) {
				this.partial = t;
				this.clearSilence();
			} else {
				this.partial = '';
				if (t) this.finals.push(t);
				this.armSilence();
			}
		}
		if (results.length) this.onPartial(this.text());
	}

	private clearSilence() {
		if (this.silenceTimer) clearTimeout(this.silenceTimer);
		this.silenceTimer = null;
	}

	private armSilence() {
		this.clearSilence();
		if (this.opts.endSilenceMs > 0) this.silenceTimer = setTimeout(() => this.stop(), this.opts.endSilenceMs);
	}

	/** Deja de capturar; espera el último final de Transcribe (máx. 2 s) y emite onFinal. */
	stop() {
		if (this.done) return;
		this.mic?.stop();
		this.mic = null;
		this.opts.onState?.('finishing');
		const ws = this.ws;
		if (ws?.readyState === WebSocket.OPEN) {
			ws.send(audioEvent(new Uint8Array(0))); // fin de stream
			this.closeTimer = setTimeout(() => this.finish(), 2000);
		} else {
			this.finish();
		}
	}

	/** Cancela sin emitir onFinal (reset de la conversación). */
	cancel() {
		this.done = true;
		this.teardown();
		this.opts.onState?.('idle');
	}

	private finish() {
		if (this.done) return;
		this.done = true;
		this.partial = ''; // solo enviamos texto final
		const t = this.finals.join(' ').trim();
		this.teardown();
		this.opts.onState?.('idle');
		this.onFinal(t);
	}

	private teardown() {
		this.clearSilence();
		if (this.maxTimer) clearTimeout(this.maxTimer);
		if (this.closeTimer) clearTimeout(this.closeTimer);
		this.mic?.stop();
		this.mic = null;
		try {
			this.ws?.close();
		} catch {
			/* noop */
		}
		this.ws = null;
		if (session === this) session = null;
	}
}

/**
 * Empieza a escuchar. `onPartial` recibe el texto en vivo (para mostrar),
 * `onFinal` se llama una vez con el transcript final (puede ser '' si no se oyó nada).
 * Rechaza con VoiceError (p. ej. code 'mic-denied' → mostrar e.userMessage; el texto sigue disponible).
 */
export async function startListening(
	onPartial: (text: string) => void,
	onFinal: (text: string) => void,
	opts: ListenOptions = {}
): Promise<void> {
	if (session) throw new VoiceError('busy');
	const s = new Session(onPartial, onFinal, { endSilenceMs: 1500, maxMs: 20000, ...opts });
	session = s;
	try {
		await s.start();
	} catch (e) {
		if (session === s) session = null;
		throw e instanceof VoiceError ? e : new VoiceError('network', String(e));
	}
}

export function stopListening(): void {
	session?.stop();
}

export function cancelListening(): void {
	session?.cancel();
}

export function isListening(): boolean {
	return session !== null;
}
