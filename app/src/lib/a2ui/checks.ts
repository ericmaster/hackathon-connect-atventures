// Funciones de validación en el dispositivo (catálogo Basic + FV: cedulaEc, rucEc).
import { getPath, isBinding } from './pointer.js';

/** Módulo 10 cédula Ecuador (SPEC §7.1). */
export function cedulaEc(v: unknown): boolean {
	const s = String(v ?? '').replace(/\D/g, '');
	if (!/^\d{10}$/.test(s)) return false;
	const prov = +s.slice(0, 2);
	if (!((prov >= 1 && prov <= 24) || prov === 30)) return false;
	if (+s[2] >= 6) return false;
	let sum = 0;
	for (let i = 0; i < 9; i++) {
		let d = +s[i] * (i % 2 === 0 ? 2 : 1);
		if (d > 9) d -= 9;
		sum += d;
	}
	return (10 - (sum % 10)) % 10 === +s[9];
}

/** RUC simple: persona natural = cédula válida + 001; sociedades: 13 dígitos terminados en 001 (sin verificar dígito). */
export function rucEc(v: unknown): boolean {
	const s = String(v ?? '').replace(/\D/g, '');
	if (!/^\d{13}$/.test(s) || !s.endsWith('001')) return false;
	return +s[2] < 6 ? cedulaEc(s.slice(0, 10)) : true;
}

export function email(v: unknown): boolean {
	return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(v ?? '').trim());
}

type Call = { call?: string; args?: Record<string, unknown>; condition?: Call; message?: string };

export function evalCall(c: Call, data: unknown, fallback: unknown): boolean {
	const call = c.condition ?? c;
	const raw = call.args ?? {};
	const a: Record<string, unknown> = {};
	for (const [k, v] of Object.entries(raw)) a[k] = isBinding(v) ? getPath(data, v.path) : v;
	const val = 'value' in a ? a.value : fallback;
	const s = String(val ?? '');
	switch (call.call) {
		case 'required':
			return Array.isArray(val) ? val.length > 0 : s.trim() !== '' && val !== false;
		case 'regex':
			try {
				return new RegExp(String(a.pattern ?? '')).test(s);
			} catch {
				return true;
			}
		case 'length':
			return s.length >= Number(a.min ?? 0) && s.length <= Number(a.max ?? Infinity);
		case 'numeric':
			return s !== '' && !isNaN(+s) && +s >= Number(a.min ?? -Infinity) && +s <= Number(a.max ?? Infinity);
		case 'email':
			return email(val);
		case 'cedulaEc':
			return cedulaEc(val);
		case 'rucEc':
			return rucEc(val);
		case 'and':
			return ((a.values as Call[]) ?? []).every((x) => evalCall(x, data, fallback));
		case 'or':
			return ((a.values as Call[]) ?? []).some((x) => evalCall(x, data, fallback));
		case 'not':
			return !evalCall(a.value as Call, data, fallback);
		default:
			return true; // función desconocida: no bloquea
	}
}

/** Devuelve el primer mensaje de error o null. */
export function firstError(checks: unknown, data: unknown, value: unknown): string | null {
	if (!Array.isArray(checks)) return null;
	for (const c of checks as Call[]) if (!evalCall(c, data, value)) return c.message ?? 'Revisa este dato';
	return null;
}
