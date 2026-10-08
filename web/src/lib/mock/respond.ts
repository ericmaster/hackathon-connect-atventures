// MOCK: respuestas generativas simuladas (sin backend). Datos 100% sintéticos.
// Guardrails = capa propia antes de "generar": alarma > receta > diagnóstico > intención.
// Reglas: nunca diagnostica, nunca afirma una condición, solo venta libre (OTC).
import type { Card, Product } from '#lib/cards/types.js';

export type Reply = { text: string; cards: Card[]; follow?: string[] };

const P = {
	paracetamol: { name: 'Paracetamol 500 mg', detail: 'Genérico · 20 tabletas', price: '$2,40', cashback: '5% cashback · $0,12', stock: 'Hay stock a 350 m', note: 'Venta libre.' },
	antigripal: { name: 'Antigripal día/noche', detail: 'Demo · 12 cápsulas', price: '$4,80', cashback: '5% cashback · $0,24', stock: 'Hay stock a 350 m', note: 'Venta libre. Lee el prospecto.' },
	suero: { name: 'Suero oral sabor naranja', detail: 'Demo · 500 ml', price: '$1,95', cashback: '5% cashback · $0,10', stock: 'Hay stock a 350 m' },
	pastillas: { name: 'Pastillas para la garganta miel-limón', detail: 'Demo · 16 unidades', price: '$3,20', cashback: '5% cashback · $0,16', stock: 'Últimas 4 unidades' },
	vitC: { name: 'Vitamina C 1 g', detail: '30 tabletas efervescentes', price: '$6,90', cashback: '5% cashback · $0,35', stock: 'Hay stock' },
	panales: { name: 'Pañitos húmedos x80', detail: 'Demo · pack familiar', price: '$3,60', cashback: '5% cashback · $0,18', stock: 'Hay stock' },
	protector: { name: 'Protector solar FPS 50', detail: 'Demo · 120 ml', price: '$14,50', cashback: '5% cashback · $0,73', stock: 'Hay stock' }
} satisfies Record<string, Product>;

const card = (p: Product): Card => ({ kind: 'product', ...p });
const centro: Card = { kind: 'pharmacy', name: 'Medicity Quito CCI', distance: '240 m', hours: 'Abierto hasta las 22:00', stock: 'Tiene todo lo que buscas' };
const norte: Card = { kind: 'pharmacy', name: 'Farmacias Económicas Shyris', distance: '880 m', hours: 'Abierto hasta las 21:00', stock: 'Stock parcial · 3 de 4 productos' };
const ASK = 'Antes de llevarlo, cuéntale al farmacéutico si tienes alergias o tomas otros medicamentos. Si persiste, consulta a un médico.';

const norm = (s: string) => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
const has = (t: string, ...w: string[]) => w.some((x) => t.includes(x));

export function respond(input: string): Reply {
	const t = ` ${norm(input)} `;

	// 1) Señales de alarma: componente fijo, gana a todo.
	if (has(t, 'pecho', 'respirar', 'ahog', 'desmay', 'convuls', 'sangr', 'inconscien', 'embaraz', 'paralis', 'suicid'))
		return {
			text: 'Lo que describes puede necesitar atención urgente. No esperes.',
			cards: [{ kind: 'alerta', text: 'Esto puede ser una emergencia. Llama ya al ECU 911 o ve a urgencias.' }, centro]
		};
	// 2) Medicamentos con receta: no sugerimos.
	if (has(t, 'antibiot', 'amoxi', 'receta', 'azitro', 'clonazep', 'tramadol'))
		return {
			text: 'Ese tipo de medicamento necesita receta médica, así que no puedo sugerirlo. Lleva tu receta y un farmacéutico te atiende en la farmacia más cercana.',
			cards: [centro]
		};
	// 3) Pedido de diagnóstico: no diagnosticamos.
	if (has(t, 'que tengo', 'diagnost', 'que enfermedad', 'es grave'))
		return {
			text: 'No puedo darte un diagnóstico; eso lo hace un médico. Sí puedo mostrarte productos de venta libre para aliviar molestias comunes o la farmacia más cercana para hablar con un farmacéutico.',
			cards: [centro],
			follow: ['Algo para la gripe', 'Farmacia más cercana con stock']
		};
	// 4) Intenciones.
	if (has(t, 'gripe', 'resfri', ' tos', 'garganta', 'congest', 'fiebre', 'dolor de cabeza', 'malestar'))
		return {
			text: `Te muestro opciones de venta libre para aliviar molestias de gripe y dónde retirarlas. ${ASK}`,
			cards: [card(P.antigripal), card(P.paracetamol), card(P.pastillas), { kind: 'sugerencia', habit: 'vitamina C cada mes', product: P.vitC }, centro],
			follow: ['Mis cupones SmartClub', 'Reponer mis productos frecuentes']
		};
	if (has(t, 'farmacia', 'cerca', 'stock', 'abiert', 'donde', 'retir'))
		return {
			text: 'Estas son las farmacias más cercanas a ti (ubicación simulada), ordenadas por distancia y stock.',
			cards: [centro, norte],
			follow: ['Algo para la gripe', 'Mis cupones SmartClub']
		};
	if (has(t, 'cupon', 'smartclub', 'smart', 'cashback', 'beneficio', 'descuento', 'puntos'))
		return {
			text: 'Tienes $3,85 de cashback smart acumulado y 2 cupones activos. Muestra el QR en caja o úsalos en tu próximo pedido.',
			cards: [
				{ kind: 'cupon', title: '5% en tu próxima compra', code: 'DEMO-SMART5', until: 'Válido 30 días · demo' },
				{ kind: 'cupon', title: '2x1 en protector solar', code: 'DEMO-SOL2X1', until: 'Válido hasta el domingo · demo' }
			],
			follow: ['Reponer mis productos frecuentes']
		};
	if (has(t, 'repon', 'frecuent', 'siempre', 'lo de siempre', 'repetir', 'otra vez'))
		return {
			text: 'Según tus compras anteriores (historial simulado), ya te toca reponer esto. Te armé el pedido para retirar hoy.',
			cards: [
				{ kind: 'sugerencia', habit: 'vitamina C cada mes', product: P.vitC },
				{ kind: 'sugerencia', habit: 'pañitos húmedos cada 2 semanas', product: P.panales },
				{
					kind: 'resumen',
					items: [
						{ name: P.vitC.name, qty: 1, price: P.vitC.price },
						{ name: P.panales.name, qty: 2, price: '$7,20' }
					],
					total: '$14,10',
					cashback: '$0,71'
				},
				centro
			]
		};
	if (has(t, ' sol', 'piel', 'protector', 'playa'))
		return { text: 'Para cuidarte del sol, una opción de venta libre:', cards: [card(P.protector), card(P.suero)] };
	return {
		text: 'En esta demo puedo ayudarte con productos de venta libre, farmacias cercanas con stock, tus cupones smart y reponer lo que sueles llevar. ¿Qué necesitas?',
		cards: [],
		follow: ['Algo para la gripe', 'Farmacia más cercana con stock', 'Mis cupones SmartClub', 'Reponer mis productos frecuentes']
	};
}

export const MOCK_TRANSCRIPT = 'Algo para la gripe';
