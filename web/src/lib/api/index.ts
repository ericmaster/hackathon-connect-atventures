import { httpTransport } from './http.js';
import { API_URL } from './auth.js';

/** Live = real API when `?demo` is absent and VITE_FV_API_URL is set. */
export function useLive(): boolean {
	const params = new URLSearchParams(typeof location !== 'undefined' ? location.search : '');
	return !params.has('demo') && !!API_URL;
}

export { httpTransport };
export type { Transport } from './transport.js';
