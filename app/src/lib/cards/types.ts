// Props de las tarjetas custom (catálogo FV).
export type Product = { sku?: string; name: string; detail?: string; price: string; cashback?: string; stock?: string; note?: string; ventaLibre?: boolean };
export type Pharmacy = { pharmacyId?: string; name: string; distance?: string; hours?: string; stock?: string; phone?: string; mapsUrl?: string };
export type Line = { name: string; qty: number; price: string };

export type Card =
	| ({ kind: 'product' } & Product)
	| ({ kind: 'pharmacy' } & Pharmacy)
	| { kind: 'sugerencia'; habit: string; product: Product }
	| { kind: 'resumen'; items: Line[]; total: string; cashback: string }
	| { kind: 'cupon'; title: string; code: string; until: string }
	| { kind: 'alerta'; text: string };

export type Msg = { role: 'user' | 'assistant'; text?: string; card?: Card };
