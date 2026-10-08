// Cliente admin (solo GET). Auth: signedFetch de #lib/api/auth (SigV4, Identity Pool) por defecto.
// Hook: setAdminFetcher() para sustituirlo (p. ej. otro esquema de auth o tests).
import { signedFetch } from '#lib/api/auth.js';

export type AdminFetcher = (path: string, init?: RequestInit) => Promise<Response>;
let fetcher: AdminFetcher = (path, init) => signedFetch(path, init);

export function setAdminFetcher(f: AdminFetcher): void {
	fetcher = f;
}

export type Row = Record<string, unknown>;

export const TABS = [
	{ id: 'crm', label: 'CRM' },
	{ id: 'catalogo', label: 'Catálogo' },
	{ id: 'inventario', label: 'Inventario' },
	{ id: 'farmacias', label: 'Farmacias' },
	{ id: 'smartclub', label: 'SmartClub' },
	{ id: 'pedidos', label: 'Pedidos' },
	{ id: 'facturacion', label: 'Facturación' },
	{ id: 'logs', label: 'Logs' }
] as const;

export type TabId = (typeof TABS)[number]['id'];

export async function loadService(id: TabId, signal?: AbortSignal): Promise<Row[]> {
	const r = await fetcher(`/admin/${id}`, { method: 'GET', signal });
	if (!r.ok) throw new Error(r.status === 403 ? 'Sin permiso de administrador (403)' : `Error HTTP ${r.status}`);
	const j = (await r.json()) as { items?: Row[] };
	return Array.isArray(j.items) ? j.items : [];
}

/** Campos internos: se muestran rotulados, nunca llegan al cliente. */
export function isInternal(col: string): boolean {
	return col.startsWith('condiciones_probables');
}
