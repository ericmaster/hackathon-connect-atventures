// Fetcher pluggable para /voice/*. B debe inyectar el fetch firmado (SigV4, Identity Pool):
//   import { setVoiceFetcher } from '$lib/voice';
//   setVoiceFetcher(signedFetch);  // (path, init) => Promise<Response>
// Sin inyección: fetch directo a VITE_FV_API_URL (solo útil en local/sin auth).

export type VoiceFetcher = (path: string, init?: RequestInit) => Promise<Response>;

const BASE = ((import.meta.env.VITE_FV_API_URL as string | undefined) ?? '').replace(/\/$/, '');

let fetcher: VoiceFetcher = (path, init) => fetch(BASE + path, init);

export function setVoiceFetcher(f: VoiceFetcher): void {
	fetcher = f;
}

export async function postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
	const res = await fetcher(path, {
		method: 'POST',
		headers: { 'content-type': 'application/json' },
		body: JSON.stringify(body ?? {}),
		signal
	});
	if (!res.ok) throw new Error(`HTTP ${res.status} en ${path}`);
	const json = (await res.json()) as Record<string, unknown>;
	// Acepta {..} o {data: {..}} según cómo envuelva la Lambda.
	return (json && typeof json === 'object' && 'data' in json ? json.data : json) as T;
}
