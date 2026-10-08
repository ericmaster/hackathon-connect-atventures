// JSON Pointer mínimo (RFC 6901) para bindings {path:"/x/y"}.
function parts(path: string): string[] {
	if (!path || path === '/') return [];
	return path.replace(/^\//, '').split('/').map((p) => p.replace(/~1/g, '/').replace(/~0/g, '~'));
}

export function getPath(data: unknown, path: string): unknown {
	let cur: unknown = data;
	for (const p of parts(path)) {
		if (cur == null || typeof cur !== 'object') return undefined;
		cur = (cur as Record<string, unknown>)[p];
	}
	return cur;
}

export function setPath(data: Record<string, unknown>, path: string, value: unknown): Record<string, unknown> {
	const ps = parts(path);
	if (ps.length === 0) return (value && typeof value === 'object' ? value : {}) as Record<string, unknown>;
	let cur: Record<string, unknown> = data;
	for (const p of ps.slice(0, -1)) {
		if (cur[p] == null || typeof cur[p] !== 'object') cur[p] = {};
		cur = cur[p] as Record<string, unknown>;
	}
	cur[ps[ps.length - 1]] = value;
	return data;
}

export function isBinding(v: unknown): v is { path: string } {
	return !!v && typeof v === 'object' && !Array.isArray(v) && typeof (v as { path?: unknown }).path === 'string';
}
