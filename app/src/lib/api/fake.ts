// Plan B: transporte local determinista. Misma FSM y acciones que CONTRACT.md, plantillas A2UI v0.9.1.
// Datos 100% sintéticos. Nunca nombra condiciones: personaliza solo por comportamiento.
import type { A2uiMessage, Comp } from '#lib/a2ui/types.js';
import { CATALOG_ID } from '#lib/a2ui/types.js';
import { cedulaEc, email as isEmail, rucEc } from '#lib/a2ui/checks.js';
import type { ActionBody, FvResponse, Transport } from './transport.js';

const V = 'v0.9.1';
const COUPON = 300; // $3 primera reserva
const CF_MAX = 5000; // $50 con IVA
const IVA = 0.15;
export const FV_CACHE_KEY = 'fv-cache';

type Prod = { sku: string; name: string; detail: string; price: number; rx?: boolean };
const P: Record<string, Prod> = {
	'FV-1001': { sku: 'FV-1001', name: 'Antigripal Día y Noche', detail: 'Caja x 12 tabletas', price: 450 },
	'FV-1002': { sku: 'FV-1002', name: 'Paracetamol 500 mg', detail: 'Genérico · 20 tabletas', price: 240 },
	'FV-1003': { sku: 'FV-1003', name: 'Vitamina C 1 g efervescente', detail: 'Tubo x 10', price: 390 },
	'FV-9001': { sku: 'FV-9001', name: 'Oseltamivir 75 mg', detail: 'Caja x 10 cápsulas', price: 2800, rx: true },
	'FV-2001': { sku: 'FV-2001', name: 'Multivitamínico 50+', detail: 'Frasco x 90 tabletas', price: 4890 },
	'FV-2002': { sku: 'FV-2002', name: 'Protector solar FPS 50', detail: 'Tubo 120 ml', price: 1590 }
};
const GRIPE = ['FV-1001', 'FV-1002', 'FV-1003', 'FV-9001'];
const PH = [
	// Igual que services/farmaenlace-mock/data.py (2 más cercanas a la ubicación demo).
	{ pharmacyId: 'MED-UIO-014', name: 'Medicity Quito CCI', distance: '240 m', hours: 'Abierto hasta las 22:00', phone: '+593 2 000 0014', mapsUrl: 'https://maps.google.com/?q=-0.1757,-78.484' },
	{ pharmacyId: 'ECO-UIO-003', name: 'Farmacias Económicas Shyris', distance: '880 m', hours: 'Abierto hasta las 21:00', phone: '+593 2 000 0003', mapsUrl: 'https://maps.google.com/?q=-0.1735,-78.4787' }
];
type Arch = 'cuidador' | 'practico' | null;
const PROFILES: Record<string, { name: string; arch: Arch; frecuente: string }> = {
	'1710034065': { name: 'don Luis', arch: 'cuidador', frecuente: 'FV-2001' },
	'1712456787': { name: 'Andrea', arch: 'practico', frecuente: 'FV-2002' }
};

type Billing = { tipo?: 'consumidor_final' | 'datos'; nombre?: string; identificacion?: string; email?: string };
type Sess = {
	id: string;
	rev: number;
	state: string;
	cedula?: string;
	name?: string;
	arch: Arch;
	consent: boolean;
	attempts: number;
	safetyOk: boolean;
	cart: { sku: string; qty: number; repo?: boolean }[];
	pharmacy?: (typeof PH)[number];
	billing: Billing;
	order?: { number: string; invoice: string };
	redFlag: boolean;
	lastAsk?: string;
};

const money = (c: number) => '$' + (Math.round(c) / 100).toFixed(2).replace('.', ',');

/** Constructor de surfaces: una por respuesta, root = Column. */
class UI {
	comps: Comp[] = [];
	root: string[] = [];
	n = 0;
	add(c: Record<string, unknown>, top = true): string {
		const id = `c${this.n++}`;
		this.comps.push({ id, ...c } as Comp);
		if (top) this.root.push(id);
		return id;
	}
	text(text: string, variant = 'body', top = true) {
		return this.add({ component: 'Text', text, variant }, top);
	}
	button(label: string, name: string, context: Record<string, unknown> = {}, variant = 'primary', top = true) {
		const l = this.text(label, 'body', false);
		return this.add({ component: 'Button', child: l, variant, action: { event: { name, context } } }, top);
	}
	build(): Comp[] {
		return [{ id: 'root', component: 'Column', children: this.root }, ...this.comps];
	}
}

const isCuidador = (s: Sess) => s.consent && s.arch === 'cuidador';
const isPractico = (s: Sess) => s.consent && s.arch === 'practico';

function resp(s: Sess, ui: UI, spokenText: string, data?: Record<string, unknown>): FvResponse {
	s.rev++;
	const surfaceId = `fv-${s.rev}`;
	const theme = isCuidador(s) ? { senior: true, fontScale: 'large' } : undefined;
	const messages: A2uiMessage[] = [
		{ version: V, createSurface: { surfaceId, catalogId: CATALOG_ID, ...(theme ? { theme } : {}) } },
		{ version: V, updateComponents: { surfaceId, components: ui.build() } }
	];
	if (data) messages.push({ version: V, updateDataModel: { surfaceId, path: '/', value: data } });
	return { sessionId: s.id, state: s.state, revision: s.rev, messages, spokenText, mode: 'simulado' };
}

function totals(s: Sess) {
	const gross = s.cart.reduce((a, l) => a + P[l.sku].price * l.qty, 0);
	const discount = s.cart.length ? Math.min(COUPON, gross) : 0;
	const total = gross - discount;
	const subtotal = total / (1 + IVA);
	const cashback = s.cart.reduce((a, l) => a + P[l.sku].price * l.qty * 0.05 * (l.repo ? 2 : 1), 0);
	return { gross, discount, total, subtotal, iva: total - subtotal, cashback, repo: s.cart.some((l) => l.repo) };
}
const lines = (s: Sess) => s.cart.map((l) => ({ name: P[l.sku].name, qty: l.qty, price: money(P[l.sku].price * l.qty) }));
const cb = (p: Prod, repo = false) => `${repo ? '10% cashback (doble)' : '5% cashback'} · ${money(p.price * (repo ? 0.1 : 0.05))}`;

function productCard(ui: UI, p: Prod, extra: Record<string, unknown> = {}, ctx: Record<string, unknown> = {}) {
	ui.add({
		component: 'ProductCard',
		sku: p.sku,
		name: p.name,
		detail: p.detail,
		price: money(p.price),
		cashback: cb(p),
		stock: `Hay stock a ${PH[0].distance}`,
		ventaLibre: !p.rx,
		...extra,
		action: { event: { name: 'agregar_pedido', context: { sku: p.sku, confirm: true, ...ctx } } }
	});
}

function chips(ui: UI, s: Sess) {
	ui.text('Puedes hablarme o escribir. Por ejemplo:', 'caption');
	ui.button('Algo para la gripe', 'decir', { text: 'algo para la gripe' }, 'secondary');
	if (!isCuidador(s)) ui.button('Hablar con un farmacéutico', 'handoff', {}, 'borderless');
}

// ---------- pasos ----------
function welcome(s: Sess): FvResponse {
	s.state = 'cedula';
	const ui = new UI();
	ui.text('¡Hola! Soy tu Farmacéutico Virtual de Farmaenlace.', 'h2');
	ui.add({ component: 'Cupon', title: '$3 de descuento en tu primera reserva', code: 'BIENVENIDA3', until: 'Válido hasta 31/12/2026 · demo', note: 'Se aplica solo a tu primera reserva' });
	ui.text('Para guardar tu beneficio, ¿me ayudas con tu número de cédula?');
	cedulaField(ui);
	return resp(s, ui, '¡Hola! Soy tu Farmacéutico Virtual. ¿Me ayudas con tu número de cédula?', { cedula: '' });
}
function cedulaField(ui: UI) {
	ui.add({ component: 'CedulaInput', label: 'Número de cédula', value: { path: '/cedula' }, action: { event: { name: 'enviar_cedula', context: { cedula: { path: '/cedula' } } } } });
	ui.text('Demo: 1710034065 (Cuidador) · 1712456787 (Práctico) · otra válida = perfil nuevo', 'caption');
}

function onCedula(s: Sess, raw: unknown): FvResponse {
	const c = String(raw ?? '').replace(/\D/g, '');
	if (s.state !== 'cedula') return say(s, 'Ya tengo tu cédula. ¿En qué te ayudo?');
	if (!cedulaEc(c)) {
		s.attempts++;
		if (s.attempts >= 3) return handoff(s, 'No pudimos validar la cédula tras 3 intentos.');
		const ui = new UI();
		ui.text('Mmm, no me cuadra. ¿Me la repites? Son 10 dígitos.');
		cedulaField(ui);
		return resp(s, ui, '¿Me la repites?', { cedula: '' });
	}
	s.cedula = c;
	const prof = PROFILES[c];
	s.name = prof?.name;
	s.arch = prof?.arch ?? null;
	s.state = 'consentimiento';
	const ui = new UI();
	ui.text(prof ? `¡Gracias, ${prof.name}!` : '¡Gracias! Te creé un perfil nuevo.', 'h3');
	ui.add({ component: 'ConsentimientoCard', action: { event: { name: 'consentimiento', context: {} } } });
	return resp(s, ui, 'Gracias. Una pregunta sobre tu privacidad.');
}

function onConsent(s: Sess, acepta: boolean): FvResponse {
	if (s.state !== 'consentimiento') return say(s, 'Ya guardé tu preferencia.');
	s.consent = !!acepta;
	s.state = 'consulta';
	const ui = new UI();
	ui.text('¡Listo, ya tienes tu beneficio!', 'h2');
	ui.text('Tu cupón de $3 se aplica a tu primera reserva.');
	if (!s.consent) ui.text('Sin problema: seguimos sin sugerencias personalizadas.', 'caption');
	if (isCuidador(s)) {
		const p = P['FV-2001'];
		ui.add({
			component: 'SugerenciaPersonalizada',
			message: `${cap(s.name)}, como sueles llevar tu ${p.name} cada mes, ¿te lo reservo en tu farmacia de siempre? Ganas doble cashback.`,
			product: { sku: p.sku, name: p.name, detail: p.detail, price: money(p.price), cashback: cb(p, true) },
			why: 'Lo compras más o menos cada 30 días y tu última compra fue hace 27 días. Solo miro tu historial de compras.',
			action: { event: { name: 'reservar', context: { sku: p.sku, confirm: true } } }
		});
		ui.text('¿O en qué más te ayudo? Toca el micrófono y dime.', 'h3');
		ui.button('Algo para la gripe', 'decir', { text: 'algo para la gripe' }, 'secondary');
		return resp(s, ui, `Listo ${s.name}. Como sueles llevar tu multivitamínico cada mes, ¿te lo reservo?`);
	}
	if (isPractico(s)) ui.text(`${cap(s.name)}, dime qué necesitas y te lo dejo listo en 2 toques.`, 'h3');
	else ui.text('¿En qué te ayudo hoy?', 'h3');
	chips(ui, s);
	return resp(s, ui, '¡Listo! ¿En qué te ayudo hoy?');
}

function safety(s: Sess): FvResponse {
	const ui = new UI();
	ui.text(isPractico(s) ? 'Rápido, por seguridad:' : 'Antes de sugerirte algo, por seguridad:', 'h3');
	ui.text('¿Tienes alergia a algún medicamento o estás tomando otro?');
	ui.button('No, ninguno', 'seguridad', { ok: true });
	ui.button('Sí', 'seguridad', { ok: false }, 'secondary');
	return resp(s, ui, '¿Tienes alergia a algún medicamento o estás tomando otro?');
}

function products(s: Sess): FvResponse {
	s.state = 'productos';
	const ui = new UI();
	const otc = GRIPE.map((k) => P[k]).filter((p) => !p.rx); // guardrail: solo venta libre
	if (isPractico(s)) {
		ui.text('Lo más rápido:', 'h3');
		productCard(ui, otc[0], { cta: `Agregar y retirar en ${PH[0].name}` }, { rapido: true });
	} else if (isCuidador(s)) {
		ui.text('Te recomiendo una opción sencilla:', 'h2');
		otc.slice(0, 2).forEach((p) => productCard(ui, p));
	} else {
		ui.text('Estas opciones son de venta libre:', 'h3');
		otc.forEach((p) => productCard(ui, p));
		ui.text('Hay otra opción que requiere receta y no te la muestro. Si la necesitas, un farmacéutico te ayuda.', 'caption');
	}
	ui.add({ component: 'AvisoSalud', text: 'Si persiste, consulta a un médico. No reemplaza la consulta con un profesional de salud.' });
	return resp(s, ui, isPractico(s) ? 'Esta es la opción más rápida.' : 'Te muestro opciones de venta libre. Si persiste, consulta a un médico.');
}

function addToCart(s: Sess, sku: unknown, repo: boolean, rapido: boolean): FvResponse {
	if (s.redFlag) return blocked(s);
	const p = P[String(sku)];
	if (!p) return say(s, 'No encontré ese producto.');
	if (p.rx) return handoff(s, `Pidió ${p.name}, que requiere receta.`);
	if (s.order) return say(s, 'Tu reserva ya está confirmada. Reinicia la demo para un pedido nuevo.');
	const l = s.cart.find((x) => x.sku === p.sku);
	if (l) l.qty++;
	else s.cart.push({ sku: p.sku, qty: 1, repo });
	if (rapido || isPractico(s)) {
		s.pharmacy = PH[0];
		return resumen(s, `Agregué ${p.name}. Retiras en ${PH[0].name}.`);
	}
	if (s.pharmacy) return resumen(s, `Agregué ${p.name}.`);
	s.state = 'farmacia';
	const ui = new UI();
	ui.text(`Agregué ${p.name}. ${isCuidador(s) ? '¿Lo retiras en tu farmacia de siempre?' : '¿Dónde lo retiras?'}`, 'h3');
	for (const ph of isCuidador(s) ? PH.slice(0, 1) : PH)
		ui.add({ component: 'PharmacyCard', ...ph, stock: 'Tiene todo tu pedido', action: { event: { name: 'retirar_aqui', context: { pharmacyId: ph.pharmacyId } } } });
	if (!isCuidador(s)) ui.button('Seguir comprando', 'seguir_comprando', {}, 'borderless');
	return resp(s, ui, `Agregué ${p.name}. ¿Dónde lo retiras?`);
}

function resumen(s: Sess, intro = 'Este es tu pedido.'): FvResponse {
	s.state = 'resumen';
	const t = totals(s);
	const ui = new UI();
	ui.text(intro, 'h3');
	ui.add({
		component: 'ResumenPedido',
		items: lines(s),
		discount: '-' + money(t.discount),
		total: money(t.total),
		cashback: money(t.cashback) + (t.repo ? ' (doble por reposición)' : ''),
		pharmacy: s.pharmacy?.name,
		cta: 'Continuar',
		action: { event: { name: 'confirmar_reserva', context: { confirm: true } } }
	});
	if (!isPractico(s)) ui.button('Seguir comprando', 'seguir_comprando', {}, 'borderless');
	return resp(s, ui, `Tu total es ${money(t.total)}. Pagas al retirar.`);
}

function needFields(s: Sess): (keyof Billing)[] {
	const t = totals(s);
	if (!s.billing.tipo) return ['tipo'];
	const req: (keyof Billing)[] = s.billing.tipo === 'consumidor_final' && t.total <= CF_MAX ? ['email'] : ['nombre', 'identificacion', 'email'];
	return req.filter((f) => !s.billing[f]);
}

const ASK: Record<string, { q: string; label: string; checks: unknown[] }> = {
	email: {
		q: '¿A qué email te envío la factura?',
		label: 'Email',
		checks: [
			{ call: 'required', message: 'Escribe tu email' },
			{ call: 'email', message: 'Revisa el email, por ejemplo nombre@correo.com' }
		]
	},
	nombre: { q: '¿A nombre de quién va la factura? (nombre o razón social)', label: 'Nombre o razón social', checks: [{ call: 'length', args: { min: 3 }, message: 'Escribe el nombre completo' }] },
	identificacion: {
		q: '¿Cuál es la cédula, RUC o pasaporte para la factura?',
		label: 'Cédula / RUC / pasaporte',
		checks: [
			{
				call: 'or',
				args: { values: [{ call: 'cedulaEc' }, { call: 'rucEc' }, { call: 'regex', args: { pattern: '^[A-Za-z0-9]{6,15}$' } }] },
				message: 'Revisa el número'
			}
		]
	}
};

function facturacion(s: Sess, note?: string): FvResponse {
	if (s.redFlag) return blocked(s);
	s.state = 'facturacion';
	const t = totals(s);
	if (!s.billing.tipo && t.total > CF_MAX) s.billing.tipo = 'datos';
	const need = needFields(s);
	const ui = new UI();
	if (note) ui.text(note, 'caption');
	if (need[0] === 'tipo') {
		ui.text(`Tu total es ${money(t.total)} con IVA. ¿Te hago la factura a consumidor final?`, 'h3');
		ui.text('Solo necesito tu email para enviártela.', 'caption');
		ui.button('Sí, consumidor final', 'facturacion_tipo', { tipo: 'consumidor_final' });
		ui.button('Factura con mis datos', 'facturacion_tipo', { tipo: 'datos' }, 'secondary');
		return resp(s, ui, '¿Te hago la factura a consumidor final?');
	}
	if (need.length) {
		const f = need[0];
		const a = ASK[f];
		s.lastAsk = f;
		if (f === 'nombre' && t.total > CF_MAX) ui.text(`Como el total (${money(t.total)}) pasa de $50, la factura va con tus datos.`, 'caption');
		ui.text(a.q, 'h3');
		ui.add({ component: 'TextField', label: a.label, variant: f === 'identificacion' ? 'number' : 'shortText', value: { path: `/factura/${f}` }, checks: a.checks });
		ui.button('Continuar', 'facturacion_dato', { campo: f, valor: { path: `/factura/${f}` } });
		return resp(s, ui, a.q, { factura: { [f]: '' } });
	}
	// confirmar datos
	s.lastAsk = undefined;
	const b = s.billing;
	const cf = b.tipo === 'consumidor_final';
	const col = [
		ui.text('Datos de tu factura', 'h3', false),
		ui.text(cf ? 'Consumidor final · 9999999999999' : `${b.nombre} · ${b.identificacion}`, 'body', false),
		ui.text(`Email: ${b.email}`, 'body', false),
		ui.text(`Total ${money(t.total)} · pagas al retirar en ${s.pharmacy?.name ?? PH[0].name}`, 'caption', false)
	];
	const colId = ui.add({ component: 'Column', children: col }, false);
	ui.add({ component: 'Card', child: colId });
	ui.button('Confirmar reserva', 'confirmar_reserva', { confirm: true });
	ui.button('Cambiar datos', 'facturacion_tipo', { tipo: 'cambiar' }, 'borderless');
	return resp(s, ui, `¿Confirmo tu reserva por ${money(t.total)}?`);
}

function onDato(s: Sess, campo: unknown, valor: unknown): FvResponse {
	const f = String(campo) as keyof Billing;
	const v = String(valor ?? '').trim();
	const ok =
		f === 'email' ? isEmail(v) : f === 'nombre' ? v.length >= 3 : f === 'identificacion' ? cedulaEc(v) || rucEc(v) || /^[A-Za-z0-9]{6,15}$/.test(v) : false;
	if (!ok) return facturacion(s, 'Mmm, ese dato no me cuadra. ¿Me lo repites?');
	(s.billing as Record<string, string>)[f] = v;
	return facturacion(s);
}

function loadCache(): Record<string, Billing> {
	try {
		return JSON.parse(localStorage.getItem(FV_CACHE_KEY) || '{}');
	} catch {
		return {};
	}
}

function confirmar(s: Sess): FvResponse {
	if (s.redFlag) return blocked(s);
	if (s.order) return confirmation(s); // idempotente
	if (!s.cart.length) return say(s, 'Tu pedido está vacío. ¿Qué necesitas?');
	if (!s.pharmacy) s.pharmacy = PH[0];
	if (s.state !== 'facturacion' || needFields(s).length) {
		// caché del dispositivo: datos de facturación previos (SPEC §7.4)
		const cached = s.cedula ? loadCache()[s.cedula] : undefined;
		if (cached && !s.billing.email) s.billing = { ...cached };
		return facturacion(s);
	}
	const n = 1000 + ((s.rev * 37) % 9000);
	s.order = { number: `R-${n}`, invoice: `001-002-${String(n).padStart(9, '0')}` };
	s.state = 'confirmacion';
	if (s.cedula) localStorage.setItem(FV_CACHE_KEY, JSON.stringify({ ...loadCache(), [s.cedula]: s.billing }));
	return confirmation(s);
}

function confirmation(s: Sess): FvResponse {
	const t = totals(s);
	const b = s.billing;
	const cf = b.tipo === 'consumidor_final' && t.total <= CF_MAX;
	const ui = new UI();
	ui.text('¡Reserva lista!', 'h2');
	ui.text('Pagas al retirar en la farmacia.');
	ui.add({ component: 'ConfirmacionPedido', orderNumber: s.order!.number, pharmacy: s.pharmacy?.name, pickupTime: 'Lista en 30 min · hoy hasta las 22:00', qrValue: `FV|${s.order!.number}|${s.pharmacy?.pharmacyId}` });
	ui.add({
		component: 'FacturaMock',
		number: s.order!.invoice,
		customerName: cf ? 'CONSUMIDOR FINAL' : b.nombre,
		customerId: cf ? '9999999999999' : b.identificacion,
		email: b.email,
		items: lines(s),
		subtotal: money(t.subtotal),
		iva: money(t.iva),
		discount: '-' + money(t.discount),
		total: money(t.total),
		label: 'SIMULADA'
	});
	ui.add({ component: 'Cupon', title: `Cupón de bienvenida aplicado: -${money(t.discount)}`, code: 'BIENVENIDA3', until: 'Usado en esta reserva', note: 'Muéstralo al farmacéutico' });
	ui.text(`Ganas ${money(t.cashback)} de cashback smart${t.repo ? ' (doble por reposición)' : ''}.`, 'h3');
	return resp(s, ui, `¡Listo! Tu reserva ${s.order!.number} está confirmada. Pagas al retirar.`);
}

function handoff(s: Sess, summary?: string): FvResponse {
	const ui = new UI();
	ui.text('Te paso con un farmacéutico de verdad.', 'h3');
	const cart = s.cart.map((l) => P[l.sku].name).join(', ');
	ui.add({
		component: 'HandoffCard',
		summary: [summary ?? 'Pidió hablar con un farmacéutico.', cart && `Pedido: ${cart}.`].filter(Boolean).join(' '),
		pharmacy: `${PH[0].name} · ${PH[0].distance}`,
		phone: PH[0].phone,
		mapsUrl: PH[0].mapsUrl
	});
	return resp(s, ui, 'Te paso con un farmacéutico.');
}

function redFlag(s: Sess): FvResponse {
	s.redFlag = true;
	const ui = new UI();
	ui.add({ component: 'AlertaRoja', text: 'Lo que describes puede ser una emergencia. Llama ya al ECU 911 o ve a urgencias.', phone: '911', action: { event: { name: 'handoff', context: {} } } });
	return resp(s, ui, 'Esto puede ser una emergencia. Llama ya al ECU 911.');
}
function blocked(s: Sess): FvResponse {
	const ui = new UI();
	ui.add({ component: 'AlertaRoja', text: 'Por tu seguridad no continúo con el pedido. Si es una emergencia, llama al ECU 911.', phone: '911', action: { event: { name: 'handoff', context: {} } } });
	return resp(s, ui, 'Por tu seguridad no continúo con el pedido.');
}
function say(s: Sess, text: string, withChips = false): FvResponse {
	const ui = new UI();
	ui.text(text, 'body');
	if (withChips) chips(ui, s);
	return resp(s, ui, text);
}
const cap = (x?: string) => (x ? x[0].toUpperCase() + x.slice(1) : '');

// ---------- texto libre ----------
const RX_RED = /dolor (fuerte )?(en el |de )?pecho|pecho|no (puedo|puede) respirar|dificultad para respirar|me ahogo|desmay|sangr(ado|a mucho)|convulsi|embarazad|beb[eé].*fiebre|fiebre.*beb[eé]/i;
const RX_RX = /oseltamivir|amoxicilina|antibi[oó]tic|receta/i;
const RX_HUMAN = /farmac[eé]utic[oa]|humano|hablar con (una |un )?persona/i;
const RX_DX = /qu[eé] tengo|diagn[oó]stic|qu[eé] enfermedad/i;
const RX_GRIPE = /gripe|gripa|resfr|tos\b|congesti|fiebre|catarro|dolor de cabeza|malestar|moquera/i;

function onText(s: Sess, text: string): FvResponse {
	const t = text.trim();
	if (RX_RED.test(t)) return redFlag(s); // alarma gana a todo
	if (s.state === 'cedula') {
		const d = t.replace(/\D/g, '');
		if (d.length >= 10) return onCedula(s, d.slice(0, 10));
		return say(s, 'Primero necesito tu cédula (10 dígitos). Puedes escribirla en el campo de arriba.');
	}
	if (s.state === 'consentimiento') {
		if (/^(s[ií]|acepto|ok|vale|claro)/i.test(t)) return onConsent(s, true);
		if (/^no/i.test(t)) return onConsent(s, false);
		return say(s, 'Marca la casilla si aceptas y toca Continuar. Es opcional.');
	}
	if (s.state === 'facturacion') {
		if (/consumidor final/i.test(t)) return onAction(s, { name: 'facturacion_tipo', context: { tipo: 'consumidor_final' } });
		if (s.lastAsk) return onDato(s, s.lastAsk, t);
	}
	if (RX_RX.test(t)) return handoff(s, 'Pidió un medicamento que requiere receta.');
	if (RX_DX.test(t)) {
		const ui = new UI();
		ui.text('No puedo darte un diagnóstico; eso lo hace un médico. Sí puedo sugerirte productos de venta libre o pasarte con un farmacéutico.');
		ui.button('Hablar con un farmacéutico', 'handoff', {}, 'secondary');
		return resp(s, ui, 'No puedo darte un diagnóstico, pero sí ayudarte con productos de venta libre.');
	}
	if (RX_HUMAN.test(t)) return handoff(s);
	if (RX_GRIPE.test(t)) return s.safetyOk ? products(s) : safety(s);
	if (/multivitam|reponer|lo de siempre/i.test(t) && s.consent && s.arch) return addToCart(s, PROFILES[s.cedula!].frecuente, true, false);
	return say(s, 'Te ayudo con productos de venta libre, tu pedido y tu cashback smart.', true);
}

function onAction(s: Sess, a: ActionBody): FvResponse {
	const c = a.context ?? {};
	switch (a.name) {
		case 'enviar_cedula':
			return onCedula(s, c.cedula);
		case 'consentimiento':
			return onConsent(s, c.acepta === true);
		case 'decir':
			return onText(s, String(c.text ?? ''));
		case 'seguridad':
			if (c.ok === true) {
				s.safetyOk = true;
				return products(s);
			}
			return handoff(s, 'Toma otros medicamentos o tiene alergias: mejor que un farmacéutico revise antes de sugerir.');
		case 'agregar_pedido':
			return addToCart(s, c.sku, false, c.rapido === true);
		case 'reservar':
			return addToCart(s, c.sku, true, false);
		case 'seguir_comprando':
			s.state = 'consulta';
			return say(s, '¿Qué más necesitas?', true);
		case 'retirar_aqui':
			s.pharmacy = PH.find((p) => p.pharmacyId === c.pharmacyId) ?? PH[0];
			return resumen(s);
		case 'confirmar_reserva':
			if (c.confirm !== true) return say(s, 'Necesito tu confirmación para reservar.');
			return confirmar(s);
		case 'facturacion_tipo':
			if (s.order) return confirmation(s);
			if (c.tipo === 'cambiar') s.billing = {};
			else if (c.tipo === 'consumidor_final' && totals(s).total <= CF_MAX) s.billing = { tipo: 'consumidor_final', email: s.billing.email };
			else s.billing.tipo = 'datos';
			return facturacion(s);
		case 'facturacion_dato':
			return onDato(s, c.campo, c.valor);
		case 'handoff':
			return handoff(s, c.reason === 'cedula_invalida' ? 'No pudimos validar la cédula tras 3 intentos.' : undefined);
		default:
			return say(s, 'Esa acción no está disponible en este paso.');
	}
}

// ---------- transporte ----------
let cur: Sess | null = null;
let seq = 0;
function newSess(): Sess {
	return { id: `fake-${Date.now().toString(36)}-${++seq}`, rev: 0, state: 'saludo', arch: null, consent: false, attempts: 0, safetyOk: false, cart: [], billing: {}, redFlag: false };
}
const delay = <T>(v: T, ms = 350) => new Promise<T>((r) => setTimeout(() => r(v), ms));
function get(id: string): Sess {
	if (!cur || cur.id !== id) cur = newSess();
	return cur;
}

export const fakeTransport: Transport = {
	kind: 'fake',
	start() {
		cur = newSess();
		return delay(welcome(cur), 150);
	},
	turn: (id, text) => delay(onText(get(id), text)),
	action: (id, _rev, a) => delay(onAction(get(id), a)),
	reset() {
		cur = newSess();
		return delay(welcome(cur), 150);
	}
};

/** Transcripción simulada para el micrófono fake según el paso. */
export function fakeTranscript(state: string): string {
	if (state === 'cedula') return '1712456787';
	if (state === 'facturacion') return 'consumidor final';
	return 'algo para la gripe';
}
