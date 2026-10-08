// MOCK: conversación demo para mostrar el lenguaje visual. Datos 100% sintéticos.
import type { Msg, Product } from '#lib/cards/types.js';

const vitC: Product = { name: 'Vitamina C 1 g', detail: '30 tabletas', price: '$6,90', cashback: '5% cashback', stock: 'Hay stock' };

export const DEMO: Msg[] = [
	{ role: 'user', text: 'Me duele la cabeza, ¿qué me das?' },
	{ role: 'assistant', text: 'Te muestro dos opciones de venta libre. Si persiste, consulta a un médico.' },
	{
		role: 'assistant',
		card: { kind: 'product', name: 'Paracetamol 500 mg', detail: 'Genérico · 20 tabletas', price: '$2,40', cashback: '5% cashback · $0,12', stock: 'Hay stock a 350 m', note: 'Venta libre.' }
	},
	{
		role: 'assistant',
		card: { kind: 'product', name: 'Ibuprofeno 400 mg', detail: 'Genérico · 10 cápsulas', price: '$3,10', cashback: '5% cashback · $0,16', stock: 'Hay stock a 350 m' }
	},
	{ role: 'assistant', card: { kind: 'sugerencia', habit: 'vitamina C cada mes', product: vitC } },
	{ role: 'user', text: 'Ya, retiro en la más cerca.' },
	{ role: 'assistant', card: { kind: 'pharmacy', name: 'Farmacia Demo Centro', distance: '350 m', hours: 'Abierto hasta las 22:00', stock: 'Tiene todo tu pedido' } },
	{
		role: 'assistant',
		card: { kind: 'resumen', items: [{ name: 'Paracetamol 500 mg', qty: 1, price: '$2,40' }, { name: 'Vitamina C 1 g', qty: 1, price: '$6,90' }], total: '$9,30', cashback: '$0,47' }
	},
	{ role: 'assistant', text: '¡Listo! Te guardé un cupón para la próxima.' },
	{ role: 'assistant', card: { kind: 'cupon', title: '5% en tu próxima compra', code: 'DEMO-SMART5', until: 'Válido 30 días · demo' } },
	{ role: 'user', text: 'Mi papá tiene dolor fuerte en el pecho.' },
	{ role: 'assistant', card: { kind: 'alerta', text: 'Esto puede ser una emergencia. Llama ya al ECU 911 o ve a urgencias.' } }
];
