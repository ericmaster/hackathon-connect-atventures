// AWS EventStream (application/vnd.amazon.eventstream) mínimo para Transcribe streaming.
// Formato: [total u32][headersLen u32][preludeCrc u32][headers][payload][messageCrc u32]

const CRC_TABLE = (() => {
	const t = new Uint32Array(256);
	for (let n = 0; n < 256; n++) {
		let c = n;
		for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
		t[n] = c >>> 0;
	}
	return t;
})();

export function crc32(buf: Uint8Array, start = 0, end = buf.length): number {
	let c = 0xffffffff;
	for (let i = start; i < end; i++) c = CRC_TABLE[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
	return (c ^ 0xffffffff) >>> 0;
}

const enc = new TextEncoder();
const dec = new TextDecoder();

export function encodeMessage(headers: Record<string, string>, payload: Uint8Array): Uint8Array<ArrayBuffer> {
	const parts: Uint8Array[] = [];
	let hlen = 0;
	for (const [k, v] of Object.entries(headers)) {
		const kb = enc.encode(k);
		const vb = enc.encode(v);
		const h = new Uint8Array(1 + kb.length + 1 + 2 + vb.length);
		const dv = new DataView(h.buffer);
		h[0] = kb.length;
		h.set(kb, 1);
		h[1 + kb.length] = 7; // string
		dv.setUint16(2 + kb.length, vb.length);
		h.set(vb, 4 + kb.length);
		parts.push(h);
		hlen += h.length;
	}
	const total = 12 + hlen + payload.length + 4;
	const out = new Uint8Array(total);
	const dv = new DataView(out.buffer);
	dv.setUint32(0, total);
	dv.setUint32(4, hlen);
	dv.setUint32(8, crc32(out, 0, 8));
	let o = 12;
	for (const p of parts) {
		out.set(p, o);
		o += p.length;
	}
	out.set(payload, o);
	dv.setUint32(total - 4, crc32(out, 0, total - 4));
	return out;
}

export function audioEvent(pcm16: Uint8Array): Uint8Array<ArrayBuffer> {
	return encodeMessage(
		{ ':content-type': 'application/octet-stream', ':event-type': 'AudioEvent', ':message-type': 'event' },
		pcm16
	);
}

export interface DecodedMessage {
	headers: Record<string, string>;
	payload: Uint8Array;
}

export function decodeMessage(data: ArrayBuffer | Uint8Array): DecodedMessage {
	const buf = data instanceof Uint8Array ? data : new Uint8Array(data);
	const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
	const total = dv.getUint32(0);
	const hlen = dv.getUint32(4);
	if (crc32(buf, 0, 8) !== dv.getUint32(8)) throw new Error('eventstream: prelude crc');
	if (crc32(buf, 0, total - 4) !== dv.getUint32(total - 4)) throw new Error('eventstream: message crc');
	const headers: Record<string, string> = {};
	let i = 12;
	const end = 12 + hlen;
	while (i < end) {
		const n = buf[i++];
		const name = dec.decode(buf.subarray(i, i + n));
		i += n;
		const type = buf[i++];
		if (type !== 7) throw new Error(`eventstream: header type ${type}`);
		const len = dv.getUint16(i);
		i += 2;
		headers[name] = dec.decode(buf.subarray(i, i + len));
		i += len;
	}
	return { headers, payload: buf.subarray(end, total - 4) };
}

export function decodeJson(data: ArrayBuffer | Uint8Array): { headers: Record<string, string>; body: unknown } {
	const m = decodeMessage(data);
	return { headers: m.headers, body: m.payload.length ? JSON.parse(dec.decode(m.payload)) : null };
}
