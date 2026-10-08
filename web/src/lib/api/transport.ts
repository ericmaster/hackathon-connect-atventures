// Contrato frontend ↔ API (ver services/api/CONTRACT.md).
import type { A2uiAction, A2uiMessage } from '#lib/a2ui/types.js';

export type FvResponse = {
	sessionId: string;
	state: string;
	revision: number;
	messages: A2uiMessage[] | string;
	spokenText?: string;
	mode: 'real' | 'simulado';
	error?: { code: string; message: string };
};

export type ActionBody = { name: string; context: Record<string, unknown>; surfaceId?: string; sourceComponentId?: string; timestamp?: string };

export interface Transport {
	readonly kind: 'fake' | 'http';
	start(): Promise<FvResponse>;
	turn(sessionId: string, text: string, signal?: AbortSignal): Promise<FvResponse>;
	action(sessionId: string, revision: number, action: ActionBody, signal?: AbortSignal): Promise<FvResponse>;
	reset(sessionId: string | null): Promise<FvResponse>;
}

export function toActionBody(a: A2uiAction): ActionBody {
	return { name: a.name, context: a.context, surfaceId: a.surfaceId, sourceComponentId: a.sourceComponentId, timestamp: a.timestamp };
}

/** La sesión/identidad ya no sirve (403 forbidden o sesión no encontrada): hay que pedir identidad y sesión nuevas. */
export class SessionLostError extends Error {
	override name = 'SessionLostError';
}
