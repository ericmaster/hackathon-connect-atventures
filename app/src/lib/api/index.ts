// Selección: ?demo (fake) > ?transport=http|fake > VITE_FV_TRANSPORT (deploy: http) > fake.
import { fakeTransport } from './fake.js';
import { httpTransport } from './http.js';
import { API_URL } from './auth.js';
import type { Transport } from './transport.js';

export function pickTransport(): Transport {
	const params = new URLSearchParams(location.search);
	if (params.has('demo')) return fakeTransport; // ?demo = Plan B explícito
	const want = params.get('transport') || import.meta.env.VITE_FV_TRANSPORT || 'fake';
	if (want === 'http' && API_URL) return httpTransport;
	if (want === 'http') console.warn('[fv] VITE_FV_API_URL vacío: uso transporte fake');
	return fakeTransport;
}

export { fakeTransport, httpTransport };
export type { Transport };
