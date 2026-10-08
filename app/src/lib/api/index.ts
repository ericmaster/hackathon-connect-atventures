// Selección de transporte: ?transport=http|fake > VITE_FV_TRANSPORT > fake (Plan B, default hasta exponer la API).
import { fakeTransport } from './fake.js';
import { httpTransport } from './http.js';
import { API_URL } from './auth.js';
import type { Transport } from './transport.js';

export function pickTransport(): Transport {
	const q = new URLSearchParams(location.search).get('transport');
	const want = q || import.meta.env.VITE_FV_TRANSPORT || 'fake';
	if (want === 'http' && API_URL) return httpTransport;
	if (want === 'http') console.warn('[fv] VITE_FV_API_URL vacío: uso transporte fake');
	return fakeTransport;
}

export { fakeTransport, httpTransport };
export type { Transport };
