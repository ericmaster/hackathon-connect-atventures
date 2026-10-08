// Auth del transporte http: Cognito Identity Pool (identidades invitadas, sin login) + SigV4 (execute-api).
// Credenciales SOLO en memoria (nunca localStorage). Las peticiones son POST cross-origin: el SW no las toca.
// Reutilizable por voz/admin (workstream C): import { signedFetch } from '#lib/api/auth.js'.
import { AwsClient } from 'aws4fetch';

const env = import.meta.env;
export const REGION: string = env.VITE_FV_REGION || 'us-east-1';
export const IDENTITY_POOL_ID: string = env.VITE_FV_IDENTITY_POOL_ID || '';
export const API_URL: string = (env.VITE_FV_API_URL || '').replace(/\/+$/, '');

type Creds = { accessKeyId: string; secretAccessKey: string; sessionToken: string; expiration: number };
// IdentityId (no es credencial) en localStorage, como pide CONTRACT.md; credenciales solo en memoria.
const ID_KEY = 'fv-identity';
let identityId: string | null = typeof localStorage !== 'undefined' ? localStorage.getItem(ID_KEY) : null;
let creds: Creds | null = null;
let client: AwsClient | null = null;
let inflight: Promise<AwsClient> | null = null;

async function cognito<T>(target: 'GetId' | 'GetCredentialsForIdentity', body: unknown): Promise<T> {
	const r = await fetch(`https://cognito-identity.${REGION}.amazonaws.com/`, {
		method: 'POST',
		cache: 'no-store',
		headers: { 'X-Amz-Target': `AWSCognitoIdentityService.${target}`, 'Content-Type': 'application/x-amz-json-1.1' },
		body: JSON.stringify(body)
	});
	if (!r.ok) throw new Error(`cognito ${target} ${r.status}`);
	return r.json() as Promise<T>;
}

async function refresh(): Promise<AwsClient> {
	if (!IDENTITY_POOL_ID) throw new Error('VITE_FV_IDENTITY_POOL_ID no configurado');
	if (!identityId) {
		identityId = (await cognito<{ IdentityId: string }>('GetId', { IdentityPoolId: IDENTITY_POOL_ID })).IdentityId;
		localStorage.setItem(ID_KEY, identityId);
	}
	type R = { Credentials: { AccessKeyId: string; SecretKey: string; SessionToken: string; Expiration: number } };
	let res: R;
	try {
		res = await cognito<R>('GetCredentialsForIdentity', { IdentityId: identityId });
	} catch {
		// identidad caducada/borrada en el pool: pedir una nueva
		identityId = (await cognito<{ IdentityId: string }>('GetId', { IdentityPoolId: IDENTITY_POOL_ID })).IdentityId;
		localStorage.setItem(ID_KEY, identityId);
		res = await cognito<R>('GetCredentialsForIdentity', { IdentityId: identityId });
	}
	const c = res.Credentials;
	creds = { accessKeyId: c.AccessKeyId, secretAccessKey: c.SecretKey, sessionToken: c.SessionToken, expiration: c.Expiration * 1000 };
	client = new AwsClient({ ...creds, service: 'execute-api', region: REGION, retries: 0 });
	return client;
}

/** Cliente SigV4 con credenciales vigentes (renueva 2 min antes de expirar). */
export async function getClient(): Promise<AwsClient> {
	if (client && creds && creds.expiration - Date.now() > 120_000) return client;
	return (inflight ??= refresh().finally(() => (inflight = null)));
}

/** Olvida credenciales e identidad (la sesión del servidor queda huérfana). */
export function clearAuth() {
	identityId = null;
	localStorage.removeItem(ID_KEY);
	creds = null;
	client = null;
}

/** TODO(auth): cabeceras extra si algún día se usa otro esquema (JWT). Hoy SigV4 va en signedFetch. */
export async function getAuthHeaders(): Promise<Record<string, string>> {
	return {};
}

/** fetch firmado SigV4 (execute-api). Sin pool configurado hace fetch simple (solo dev/local). */
export async function signedFetch(input: string, init: RequestInit = {}): Promise<Response> {
	const url = /^https?:/.test(input) ? input : API_URL + input;
	const base: RequestInit = { ...init, cache: 'no-store', headers: { ...(await getAuthHeaders()), ...(init.headers as Record<string, string>) } };
	if (!IDENTITY_POOL_ID) return fetch(url, base);
	let r = await (await getClient()).fetch(url, base);
	if (r.status === 403 || r.status === 401) {
		creds = null; // credenciales expiradas/rotadas: un reintento
		r = await (await getClient()).fetch(url, base);
	}
	// 429 = API Gateway throttle (antes de Lambda): reintentar con backoff
	for (const delay of [700, 1600]) {
		if (r.status !== 429) break;
		if (init.signal?.aborted) return r;
		await new Promise<void>((resolve) => {
			const t = setTimeout(resolve, delay + Math.random() * 300);
			init.signal?.addEventListener(
				'abort',
				() => {
					clearTimeout(t);
					resolve();
				},
				{ once: true }
			);
		});
		if (init.signal?.aborted) return r;
		r = await (await getClient()).fetch(url, base);
	}
	return r;
}
