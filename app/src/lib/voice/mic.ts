// Captura de micrófono → PCM16 mono 16 kHz en bloques de ~100 ms.
import { VoiceError } from './errors';

export const TARGET_RATE = 16000;
const CHUNK_SAMPLES = 1600; // 100 ms a 16 kHz

const WORKLET_SRC = `
class FvPcmTap extends AudioWorkletProcessor {
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (ch) this.port.postMessage(ch.slice(0));
    return true;
  }
}
registerProcessor('fv-pcm-tap', FvPcmTap);
`;

/** Remuestreo simple (promedio por ventana / interpolación lineal) de Float32 a 16 kHz. */
export class Resampler {
	private ratio: number;
	private pos = 0; // posición fraccional en la entrada acumulada
	private carry: Float32Array = new Float32Array(0);
	constructor(inRate: number, outRate = TARGET_RATE) {
		this.ratio = inRate / outRate;
	}
	push(input: Float32Array): Float32Array {
		const buf = new Float32Array(this.carry.length + input.length);
		buf.set(this.carry, 0);
		buf.set(input, this.carry.length);
		const out: number[] = [];
		const r = this.ratio;
		while (this.pos + r <= buf.length) {
			if (r >= 1) {
				// promedio de la ventana [pos, pos+r) — antialias barato
				const a = Math.floor(this.pos);
				const b = Math.min(buf.length, Math.floor(this.pos + r));
				let s = 0;
				for (let i = a; i < b; i++) s += buf[i];
				out.push(b > a ? s / (b - a) : buf[a]);
			} else {
				const i = Math.floor(this.pos);
				const f = this.pos - i;
				out.push(buf[i] * (1 - f) + (buf[i + 1] ?? buf[i]) * f);
			}
			this.pos += r;
		}
		const used = Math.floor(this.pos);
		this.carry = buf.slice(used);
		this.pos -= used;
		return Float32Array.from(out);
	}
}

export function floatToPcm16(f: Float32Array): Uint8Array {
	const out = new Uint8Array(f.length * 2);
	const dv = new DataView(out.buffer);
	for (let i = 0; i < f.length; i++) {
		const s = Math.max(-1, Math.min(1, f[i]));
		dv.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
	}
	return out;
}

export interface MicHandle {
	stop(): void;
}

type AnyWindow = typeof globalThis & { webkitAudioContext?: typeof AudioContext };

/**
 * Crea el AudioContext de forma síncrona (dentro del gesto del usuario: iOS) y
 * luego pide el micrófono. `onChunk` recibe PCM16 LE mono 16 kHz (~100 ms).
 */
export async function startMic(onChunk: (pcm16: Uint8Array) => void): Promise<MicHandle> {
	const w = globalThis as AnyWindow;
	const Ctx = w.AudioContext ?? w.webkitAudioContext;
	if (!Ctx || !navigator.mediaDevices?.getUserMedia) throw new VoiceError('unsupported');
	const ctx = new Ctx();
	void ctx.resume();
	let stream: MediaStream;
	try {
		stream = await navigator.mediaDevices.getUserMedia({
			audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true }
		});
	} catch (e) {
		void ctx.close();
		const name = (e as { name?: string })?.name ?? '';
		if (name === 'NotAllowedError' || name === 'SecurityError' || name === 'PermissionDeniedError')
			throw new VoiceError('mic-denied', name);
		if (name === 'NotFoundError' || name === 'OverconstrainedError' || name === 'NotReadableError')
			throw new VoiceError('mic-unavailable', name);
		throw new VoiceError('unsupported', name);
	}

	const resampler = new Resampler(ctx.sampleRate);
	let pending = new Float32Array(0);
	const feed = (f: Float32Array) => {
		const r = resampler.push(f);
		const merged = new Float32Array(pending.length + r.length);
		merged.set(pending, 0);
		merged.set(r, pending.length);
		let o = 0;
		while (merged.length - o >= CHUNK_SAMPLES) {
			onChunk(floatToPcm16(merged.subarray(o, o + CHUNK_SAMPLES)));
			o += CHUNK_SAMPLES;
		}
		pending = merged.slice(o);
	};

	const source = ctx.createMediaStreamSource(stream);
	const sink = ctx.createGain();
	sink.gain.value = 0; // no reproducir el micrófono
	sink.connect(ctx.destination);
	let node: AudioNode;
	let workletUrl: string | null = null;
	try {
		if (!ctx.audioWorklet) throw new Error('no worklet');
		workletUrl = URL.createObjectURL(new Blob([WORKLET_SRC], { type: 'application/javascript' }));
		await ctx.audioWorklet.addModule(workletUrl);
		const wn = new AudioWorkletNode(ctx, 'fv-pcm-tap');
		wn.port.onmessage = (ev: MessageEvent<Float32Array>) => feed(ev.data);
		node = wn;
	} catch {
		const sp = ctx.createScriptProcessor(4096, 1, 1);
		sp.onaudioprocess = (ev) => feed(new Float32Array(ev.inputBuffer.getChannelData(0)));
		node = sp;
	}
	source.connect(node);
	node.connect(sink);

	let stopped = false;
	return {
		stop() {
			if (stopped) return;
			stopped = true;
			if (pending.length) onChunk(floatToPcm16(pending));
			pending = new Float32Array(0);
			try {
				source.disconnect();
				node.disconnect();
			} catch {
				/* noop */
			}
			if (node instanceof AudioWorkletNode) node.port.onmessage = null;
			stream.getTracks().forEach((t) => t.stop());
			void ctx.close();
			if (workletUrl) URL.revokeObjectURL(workletUrl);
		}
	};
}
