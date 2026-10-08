// A2UI v0.9.1 (subset). Mensajes agente → cliente y acción cliente → agente.
export type Json = null | boolean | number | string | Json[] | { [k: string]: Json };
export type Comp = { id: string; component: string; [k: string]: unknown };

export type A2uiMessage = {
	version?: string;
	createSurface?: { surfaceId: string; catalogId?: string; theme?: Record<string, unknown> };
	updateComponents?: { surfaceId: string; components: Comp[] };
	updateDataModel?: { surfaceId: string; path?: string; value?: unknown };
	deleteSurface?: { surfaceId: string };
};

export type A2uiAction = {
	name: string;
	surfaceId: string;
	sourceComponentId: string;
	timestamp: string;
	context: Record<string, unknown>;
};

export type OnAction = (a: A2uiAction) => void;

export type Surface = {
	id: string;
	catalogId?: string;
	theme?: Record<string, unknown>;
	comps: Record<string, Comp>;
	data: Record<string, unknown>;
	showErrors: boolean;
	sent: boolean;
};

export const CATALOG_ID = 'https://farmaenlace.ec/a2ui/fv/v1';

export const BASIC = ['Text', 'Image', 'Icon', 'Row', 'Column', 'List', 'Card', 'Divider', 'Button', 'CheckBox', 'TextField', 'ChoicePicker'];
export const CUSTOM = [
	'ProductCard',
	'PharmacyCard',
	'SugerenciaPersonalizada',
	'Reposicion',
	'AvisoSalud',
	'ResumenPedido',
	'ConfirmacionPedido',
	'FacturaMock',
	'Cupon',
	'HandoffCard',
	'AlertaRoja',
	'ConsentimientoCard',
	'CedulaInput'
];
export const KNOWN = new Set([...BASIC, ...CUSTOM]);
