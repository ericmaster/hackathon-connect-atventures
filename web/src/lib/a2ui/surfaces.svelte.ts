// Estado de surfaces A2UI: aplica createSurface/updateComponents/updateDataModel/deleteSurface.
import { KNOWN, type A2uiMessage, type Comp, type Surface } from './types.js';
import { setPath } from './pointer.js';

export function parseMessages(input: unknown): A2uiMessage[] {
	if (typeof input === 'string') {
		return input
			.split('\n')
			.map((l) => l.trim())
			.filter(Boolean)
			.flatMap((l) => {
				try {
					return [JSON.parse(l) as A2uiMessage];
				} catch {
					console.warn('[a2ui] línea JSONL inválida descartada');
					return [];
				}
			});
	}
	return Array.isArray(input) ? (input as A2uiMessage[]) : [];
}

export class SurfaceStore {
	surfaces: Record<string, Surface> = $state({});

	/** Aplica mensajes; devuelve ids creados/eliminados y errores (componentes rechazados). */
	apply(input: unknown) {
		const created: string[] = [];
		const deleted: string[] = [];
		const errors: string[] = [];
		const ensure = (id: string) =>
			(this.surfaces[id] ??= { id, comps: {}, data: {}, showErrors: false, sent: false });
		for (const m of parseMessages(input)) {
			if (!m || typeof m !== 'object') continue;
			if (m.createSurface?.surfaceId) {
				const { surfaceId, catalogId, theme } = m.createSurface;
				if (!this.surfaces[surfaceId]) created.push(surfaceId);
				this.surfaces[surfaceId] = { id: surfaceId, catalogId, theme, comps: {}, data: {}, showErrors: false, sent: false };
			} else if (m.updateComponents?.surfaceId) {
				const { surfaceId, components } = m.updateComponents;
				if (!this.surfaces[surfaceId]) created.push(surfaceId);
				const s = ensure(surfaceId);
				for (const c of components ?? []) {
					if (!c || typeof c.id !== 'string' || typeof c.component !== 'string') {
						errors.push('componente sin id/tipo');
						continue;
					}
					if (!KNOWN.has(c.component)) {
						errors.push(`componente desconocido rechazado: ${c.component}`);
						continue;
					}
					s.comps[c.id] = c as Comp;
				}
			} else if (m.updateDataModel?.surfaceId) {
				const { surfaceId, path, value } = m.updateDataModel;
				const s = ensure(surfaceId);
				s.data = setPath(s.data, path ?? '/', value);
			} else if (m.deleteSurface?.surfaceId) {
				delete this.surfaces[m.deleteSurface.surfaceId];
				deleted.push(m.deleteSurface.surfaceId);
			}
		}
		if (errors.length) console.warn('[a2ui]', errors);
		return { created, deleted, errors };
	}

	clear() {
		this.surfaces = {};
	}
}
