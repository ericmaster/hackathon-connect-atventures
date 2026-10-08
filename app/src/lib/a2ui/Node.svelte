<script lang="ts">
	// Renderer recursivo A2UI v0.9.1: un componente por id, hijos por id, bindings {path}.
	import Node from './Node.svelte';
	import type { Comp, OnAction, Surface } from './types.js';
	import { getPath, isBinding, setPath } from './pointer.js';
	import { firstError } from './checks.js';
	import ProductCard from '#lib/cards/ProductCard.svelte';
	import PharmacyCard from '#lib/cards/PharmacyCard.svelte';
	import SugerenciaPersonalizada from '#lib/cards/SugerenciaPersonalizada.svelte';
	import ResumenPedido from '#lib/cards/ResumenPedido.svelte';
	import Cupon from '#lib/cards/Cupon.svelte';
	import AlertaRoja from '#lib/cards/AlertaRoja.svelte';
	import ConfirmacionPedido from '#lib/cards/ConfirmacionPedido.svelte';
	import FacturaMock from '#lib/cards/FacturaMock.svelte';
	import HandoffCard from '#lib/cards/HandoffCard.svelte';
	import AvisoSalud from '#lib/cards/AvisoSalud.svelte';
	import ConsentimientoCard from '#lib/cards/ConsentimientoCard.svelte';
	import CedulaInput from '#lib/cards/CedulaInput.svelte';

	let { surface, id, onAction, depth = 0 }: { surface: Surface; id: string; onAction: OnAction; depth?: number } = $props();

	const c: Comp | undefined = $derived(depth < 40 ? surface.comps[id] : undefined);

	function rv(v: unknown): unknown {
		if (isBinding(v)) return getPath(surface.data, v.path);
		return v;
	}
	function rd(v: unknown, d = 0): unknown {
		if (isBinding(v)) return getPath(surface.data, v.path);
		if (d > 3 || !v || typeof v !== 'object') return v;
		if (Array.isArray(v)) return v.map((x) => rd(x, d + 1));
		return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, rd(x, d + 1)]));
	}
	const s = (v: unknown) => (v == null ? '' : String(rv(v)));
	// Props planas resueltas para componentes FV (sin action/checks).
	const p = $derived.by(() => {
		const out: Record<string, any> = {};
		if (!c) return out;
		for (const [k, v] of Object.entries(c)) if (k !== 'action' && k !== 'checks' && k !== 'actions') out[k] = rd(v);
		return out;
	});

	function openUrl(url: string) {
		if (/^(https?:|tel:|mailto:)/.test(url)) window.open(url, url.startsWith('http') ? '_blank' : '_self', 'noopener');
	}

	/** Dispara una acción A2UI. `action` puede ser {event}, {functionCall} o un nombre por defecto. */
	function fire(action: unknown, fallbackName: string, extra: Record<string, unknown> = {}) {
		const a = (action ?? {}) as { event?: { name?: string; context?: Record<string, unknown> }; functionCall?: { call?: string; args?: Record<string, unknown> }; name?: string; context?: Record<string, unknown> };
		if (a.functionCall) {
			if (a.functionCall.call === 'openUrl') openUrl(s(a.functionCall.args?.url));
			return;
		}
		const name = a.event?.name ?? a.name ?? fallbackName;
		if (!name) return;
		const rawCtx = a.event?.context ?? a.context ?? {};
		const context: Record<string, unknown> = {};
		for (const [k, v] of Object.entries(rawCtx)) context[k] = rd(v);
		Object.assign(context, extra);
		onAction({ name, surfaceId: surface.id, sourceComponentId: id, timestamp: new Date().toISOString(), context });
	}

	function surfaceValid(): boolean {
		for (const comp of Object.values(surface.comps)) {
			if (!comp.checks) continue;
			const val = isBinding(comp.value) ? getPath(surface.data, comp.value.path) : comp.value;
			if (firstError(comp.checks, surface.data, val)) return false;
		}
		return true;
	}

	function write(v: unknown) {
		if (c && isBinding(c.value)) surface.data = setPath(surface.data, c.value.path, v);
		else if (c) local = v;
	}
	let local: unknown = $state(undefined);
	const value = $derived(c ? (isBinding(c.value) ? getPath(surface.data, c.value.path) : (local ?? c.value)) : undefined);
	let dirty = $state(false);
	const err = $derived(c?.checks && (dirty || surface.showErrors) ? firstError(c.checks, surface.data, value) : null);

	const kids = $derived(Array.isArray(c?.children) ? (c.children as string[]) : []);
	const textCls: Record<string, string> = {
		h1: 'text-3xl font-bold leading-tight',
		h2: 'text-2xl font-bold leading-tight',
		h3: 'text-xl font-bold',
		h4: 'text-lg font-bold',
		h5: 'text-lg font-semibold',
		body: 'text-lg leading-snug',
		caption: 'text-sm text-muted'
	};
	const options = $derived(
		Array.isArray(rv(c?.options)) ? (rv(c?.options) as { label: unknown; value: string }[]) : []
	);
	function pick(v: string) {
		const multi = c?.variant === 'multipleSelection' || Array.isArray(value);
		if (multi) {
			const arr = Array.isArray(value) ? [...(value as string[])] : [];
			write(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);
		} else write(v);
		if (c?.action && !multi) fire(c.action, '', { value: v });
	}
	const selected = (v: string) => (Array.isArray(value) ? (value as string[]).includes(v) : value === v);
</script>

{#if c}
	{#if c.component === 'Text'}
		<p class={textCls[String(c.variant ?? 'body')] ?? textCls.body}>{s(c.text)}</p>
	{:else if c.component === 'Column' || c.component === 'List'}
		<div class="flex flex-col gap-3">
			{#each kids as k (k)}<Node {surface} id={k} {onAction} depth={depth + 1} />{/each}
		</div>
	{:else if c.component === 'Row'}
		<div class="flex flex-wrap items-center gap-2 *:min-w-0 *:flex-1">
			{#each kids as k (k)}<Node {surface} id={k} {onAction} depth={depth + 1} />{/each}
		</div>
	{:else if c.component === 'Card'}
		<div class="rounded-card border border-line bg-card p-4 shadow-card">
			{#if typeof c.child === 'string'}<Node {surface} id={c.child} {onAction} depth={depth + 1} />{/if}
		</div>
	{:else if c.component === 'Divider'}
		<hr class="border-line" />
	{:else if c.component === 'Image'}
		{#if /^(https:|data:image\/|\/)/.test(s(c.url))}<img src={s(c.url)} alt={s(c.alt ?? c.description)} class="max-h-60 w-full rounded-2xl object-cover" />{/if}
	{:else if c.component === 'Icon'}
		<span class="text-primary-strong" aria-hidden="true">●</span>
	{:else if c.component === 'Button'}
		<button
			type="button"
			onclick={() => {
				if (!surfaceValid()) {
					surface.showErrors = true;
					return;
				}
				fire(c.action, '');
			}}
			class="w-full rounded-full px-4 py-3 text-lg font-semibold active:scale-[.98] {c.variant === 'borderless'
				? 'text-primary-strong underline'
				: c.variant === 'primary' || !c.variant
					? 'bg-primary-strong text-white'
					: 'border-2 border-primary-strong text-primary-strong'}"
		>
			{#if typeof c.child === 'string' && surface.comps[c.child]}
				{@const ch = surface.comps[c.child]}
				{ch.component === 'Text' ? s(ch.text) : s(c.label)}
			{:else}{s(c.label ?? c.text)}{/if}
		</button>
	{:else if c.component === 'TextField'}
		<label class="block">
			{#if c.label}<span class="text-lg font-semibold">{s(c.label)}</span>{/if}
			<input
				value={String(value ?? '')}
				oninput={(e) => {
					dirty = false;
					write(e.currentTarget.value);
				}}
				onblur={() => (dirty = true)}
				type={c.variant === 'obscured' ? 'password' : 'text'}
				inputmode={c.variant === 'number' ? 'numeric' : String(c.label ?? '').toLowerCase().includes('email') ? 'email' : 'text'}
				aria-invalid={!!err}
				class="mt-1 w-full rounded-2xl border-2 bg-bg px-4 py-3 text-xl outline-none focus:border-primary-strong {err ? 'border-danger' : 'border-line'}"
			/>
			{#if err}<span class="mt-1 block font-semibold text-danger" role="alert">{err}</span>{/if}
		</label>
	{:else if c.component === 'CheckBox'}
		<label class="flex cursor-pointer items-start gap-3 rounded-2xl bg-cream p-3">
			<input type="checkbox" checked={!!value} onchange={(e) => write(e.currentTarget.checked)} class="mt-1 size-6 shrink-0 accent-primary-strong" />
			<span class="text-lg leading-snug">{s(c.label)}</span>
		</label>
	{:else if c.component === 'ChoicePicker'}
		<div class="flex flex-col gap-2" role="group" aria-label={s(c.label)}>
			{#if c.label}<span class="text-lg font-semibold">{s(c.label)}</span>{/if}
			{#each options as o (o.value)}
				<button
					type="button"
					aria-pressed={selected(o.value)}
					onclick={() => pick(o.value)}
					class="rounded-full border-2 px-4 py-3 text-left text-lg font-semibold {selected(o.value) ? 'border-primary-strong bg-primary-strong text-white' : 'border-line bg-card'}"
				>
					{s(o.label)}
				</button>
			{/each}
		</div>
	{:else if c.component === 'ProductCard'}
		{#if p.ventaLibre !== false}
			<!-- guardrail cliente: un producto con receta nunca se muestra como ProductCard -->
			<ProductCard {...p as any} onAdd={() => fire(c.action, 'agregar_pedido', c.action ? {} : { sku: p.sku, confirm: true })} />
		{/if}
	{:else if c.component === 'PharmacyCard'}
		{@const acts = (c.actions ?? {}) as Record<string, unknown>}
		<PharmacyCard
			{...p as any}
			onRetirar={() => fire(acts.retirar_aqui ?? c.action, 'retirar_aqui', c.action || acts.retirar_aqui ? {} : { pharmacyId: p.pharmacyId })}
			onComoLlegar={() => p.mapsUrl && openUrl(String(p.mapsUrl))}
			onLlamar={() => p.phone && openUrl('tel:' + String(p.phone).replace(/\s/g, ''))}
		/>
	{:else if c.component === 'SugerenciaPersonalizada' || c.component === 'Reposicion'}
		{#if p.product && p.product.ventaLibre !== false}
			<SugerenciaPersonalizada {...p as any} onReservar={() => fire(c.action, 'reservar', c.action ? {} : { sku: p.product?.sku, confirm: true })} />
		{/if}
	{:else if c.component === 'ResumenPedido'}
		<ResumenPedido {...p as any} onConfirm={() => fire(c.action, 'confirmar_reserva', c.action ? {} : { confirm: true })} />
	{:else if c.component === 'ConfirmacionPedido'}
		<ConfirmacionPedido {...p as any} />
	{:else if c.component === 'FacturaMock'}
		<FacturaMock {...p as any} />
	{:else if c.component === 'Cupon'}
		<Cupon {...p as any} />
	{:else if c.component === 'AvisoSalud'}
		<AvisoSalud {...p as any} />
	{:else if c.component === 'AlertaRoja'}
		<AlertaRoja {...p as any} onHandoff={() => fire(c.action, 'handoff')} />
	{:else if c.component === 'HandoffCard'}
		<HandoffCard
			{...p as any}
			onLlamar={() => p.phone && openUrl('tel:' + String(p.phone).replace(/\s/g, ''))}
			onComoLlegar={() => p.mapsUrl && openUrl(String(p.mapsUrl))}
		/>
	{:else if c.component === 'ConsentimientoCard'}
		<ConsentimientoCard {...p as any} onSubmit={(acepta: boolean) => fire(c.action, 'consentimiento', { acepta })} />
	{:else if c.component === 'CedulaInput'}
		<CedulaInput
			{...p as any}
			value={typeof value === 'string' ? value : ''}
			onSubmit={(cedula: string) => {
				write(cedula);
				fire(c.action, 'enviar_cedula', { cedula });
			}}
			onTooMany={() => fire(undefined, 'handoff', { reason: 'cedula_invalida' })}
		/>
	{/if}
{/if}
