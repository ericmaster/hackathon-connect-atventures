// Fetcher para /voice/*. Por defecto usa el fetch firmado SigV4 de B (#lib/api/auth: Identity Pool
// invitado → execute-api). Sin pool configurado, signedFetch hace fetch simple a VITE_FV_API_URL.
// Se puede sustituir (tests / otro transporte): setVoiceFetcher((path, init) => ...).
import { signedFetch } from '#lib/api/auth.js';

export type VoiceFetcher = (path: string, init?: RequestInit) => Promise<Response>;

let fetcher: VoiceFetcher = (path, init) => signedFetch(path, init);

export function setVoiceFetcher(f: VoiceFetcher): void {
	fetcher = f;
}

export async function postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
	const res = await fetcher(path, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body ?? {}),
		signal
	});
	if (!res.ok) throw new Error(`HTTP ${res.status} en ${path}`);
	const json = (await res.json()) as Record<string, unknown>;
	// Acepta {..} o {data: {..}} según cómo envuelva la Lambda.
	return (json && typeof json === 'object' && 'data' in json ? json.data : json) as T;
}
