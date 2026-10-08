import { startListening, stopListening, setVoiceFetcher, speak, VoiceError } from '/workspace/hackathon-connect/app/src/lib/voice/index.ts';
const out = document.getElementById('out')!;
const log: string[] = [];
const w = window as unknown as Record<string, unknown>;
setVoiceFetcher((path, init) => fetch('/api' + path, init));
w.runStt = () =>
	new Promise((resolve) => {
		const t0 = performance.now();
		let partials = 0;
		startListening(
			(p) => { partials++; log.push('partial: ' + p); },
			(f) => resolve({ final: f, partials, ms: Math.round(performance.now() - t0) })
		).catch((e: VoiceError) => resolve({ error: e.code, msg: e.userMessage }));
		setTimeout(() => stopListening(), 6000);
	});
w.runTts = async () => {
	const t0 = performance.now();
	try { await speak('Hola, soy tu Farmacéutico Virtual.'); return { ok: true, ms: Math.round(performance.now() - t0) }; }
	catch (e) { return { error: String(e) }; }
};
out.textContent = 'ready';
