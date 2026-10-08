// Transporte http: API Gateway (IAM) firmado con SigV4 vía Cognito Identity Pool (ver auth.ts y CONTRACT.md).
import { API_URL, signedFetch } from './auth.js';
import { SessionLostError, type ActionBody, type FvResponse, type Transport } from './transport.js';

async function post(path: string, body: unknown, signal?: AbortSignal): Promise<FvResponse> {
	const r = await signedFetch(API_URL + path, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
		signal
	});
	let data: FvResponse | null = null;
	try {
		data = (await r.json()) as FvResponse;
	} catch {
		/* sin cuerpo JSON */
	}
	// 403 (identidad distinta / firma rechazada, ya reintentada en signedFetch) o sesión borrada: el shell re-crea identidad + sesión.
	if (r.status === 403 || (r.status === 404 && data?.error?.code === 'not_found'))
		throw new SessionLostError(`API ${path} → ${r.status}`);
	// Solo aceptamos cuerpos con revisión numérica. 4xx con surface (p.ej. stale_revision) se muestran; un 500 con
	// `messages: []` / `revision: null` se trata como error: la tarjeta actual queda y el shell pide reintentar.
	const usable = !!data && typeof data.revision === 'number';
	if (usable && r.ok) return data!;
	if (usable && Array.isArray(data!.messages) && data!.messages.length > 0) return data!;
	throw new Error(`API ${path} → ${r.status}`);
}

export const httpTransport: Transport = {
	kind: 'http',
	start: () => post('/session', { qr: new URLSearchParams(location.search).get('qr') || 'BIENVENIDA' }),
	turn: (sessionId, text, signal) => post('/turn', { sessionId, text: text.slice(0, 500) }, signal),
	action: (sessionId, revision, action: ActionBody, signal) => post('/action', { sessionId, revision, action }, signal),
	reset: (sessionId) => (sessionId ? post('/demo/reset', { sessionId }) : post('/session', {}))
};
