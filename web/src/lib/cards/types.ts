// Props de las tarjetas custom. Antes del renderer A2UI real.
export type Product = { name: string; detail: string; price: string; cashback: string; stock: string; note?: string };
export type Pharmacy = { name: string; distance: string; hours: string; stock: string };
export type Line = { name: string; qty: number; price: string };

export type Card =
	| ({ kind: 'product' } & Product)
	| ({ kind: 'pharmacy' } & Pharmacy)
	| { kind: 'sugerencia'; habit: string; product: Product }
	| { kind: 'resumen'; items: Line[]; total: string; cashback: string }
	| { kind: 'cupon'; title: string; code: string; until: string }
	| { kind: 'alerta'; text: string };

export type Msg = { role: 'user' | 'assistant'; text?: string; card?: Card };
