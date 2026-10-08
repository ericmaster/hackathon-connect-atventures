// MOCK: no backend yet. Replace with Bedrock later.
const REPLY =
	'¡Hola! Soy tu farmacéutico virtual (demo). Pronto te ayudo a buscar productos y ver tu cashback smart. Por ahora mis respuestas son simuladas.';

export const MOCK_TRANSCRIPT = '¿Qué tengo para el dolor de cabeza?';

export function reply(_text: string): Promise<string> {
	return new Promise((r) => setTimeout(() => r(REPLY), 600));
}

export function listen(): Promise<string> {
	return new Promise((r) => setTimeout(() => r(MOCK_TRANSCRIPT), 1500));
}
