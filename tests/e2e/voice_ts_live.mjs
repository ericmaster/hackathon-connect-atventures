// Valida el framing EventStream de app/src/lib/voice/eventstream.ts contra Transcribe real.
// Uso: python presign → URL por stdin (nunca se imprime); PCM16 16k en argv[2].
import { readFileSync } from 'node:fs';
import { audioEvent, decodeJson } from '../../app/src/lib/voice/eventstream.ts';

const url = readFileSync(0, 'utf8').trim();
const pcm = new Uint8Array(readFileSync(process.argv[2]));
const ws = new WebSocket(url);
ws.binaryType = 'arraybuffer';
const finals = [];
let partials = 0;
let tEnd = 0, tFinal = 0;
ws.onopen = async () => {
	for (let i = 0; i < pcm.length; i += 3200) {
		ws.send(audioEvent(pcm.subarray(i, i + 3200)));
		await new Promise((r) => setTimeout(r, 100));
	}
	ws.send(audioEvent(new Uint8Array(16000)));
	tEnd = performance.now();
	ws.send(audioEvent(new Uint8Array(0)));
};
ws.onmessage = (ev) => {
	const { headers, body } = decodeJson(ev.data);
	if (headers[':message-type'] !== 'event') { console.log('ERR', headers[':exception-type'], JSON.stringify(body)); process.exit(1); }
	for (const r of body?.Transcript?.Results ?? []) {
		if (r.IsPartial) partials++; else { finals.push(r.Alternatives[0].Transcript); tFinal = performance.now(); }
	}
};
ws.onclose = () => {
	console.log(JSON.stringify({ partials, final: finals.join(' '), final_after_audio_end_ms: Math.round(tFinal - tEnd) }));
	process.exit(finals.length ? 0 : 1);
};
