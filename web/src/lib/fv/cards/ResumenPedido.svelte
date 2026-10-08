<script lang="ts">
	import type { Line } from './types.js';
	let {
		items = [],
		total,
		cashback,
		pharmacy,
		discount,
		coupon,
		subtotal,
		iva,
		cta = 'Confirmar pedido',
		onConfirm
	}: { items: Line[]; total: string; cashback?: string; pharmacy?: string; discount?: string; coupon?: string; subtotal?: string; iva?: string; cta?: string; onConfirm?: () => void } = $props();
</script>

<article class="rounded-card border border-line bg-card p-4 shadow-card">
	<h3 class="text-lg font-bold">Tu pedido</h3>
	<ul class="mt-2 divide-y divide-line">
		{#each items as it, i (i)}
			<li class="flex justify-between gap-2 py-2"><span>{it.qty} × {it.name}</span><span class="font-semibold whitespace-nowrap">{it.price}</span></li>
		{/each}
		{#if discount}<li class="flex justify-between py-2 text-secondary"><span>Cupón de bienvenida</span><span class="font-semibold">{discount}</span></li>
		{:else if coupon}<li class="flex justify-between py-2 text-secondary"><span>Cupón aplicado</span><span class="font-semibold">{coupon}</span></li>{/if}
	</ul>
	{#if subtotal || iva}<p class="mt-1 text-right text-sm text-muted">{subtotal ? `Subtotal ${subtotal}` : ''}{subtotal && iva ? ' · ' : ''}{iva ? `IVA ${iva}` : ''}</p>{/if}
	<div class="mt-2 flex justify-between border-t-2 border-ink pt-2 text-xl font-bold"><span>Total (IVA incl.)</span><span>{total}</span></div>
	{#if cashback}<p class="mt-1 text-right text-sm font-semibold text-primary-strong">Ganas {cashback} de cashback</p>{/if}
	{#if pharmacy}<p class="mt-2 text-sm text-muted">Retiras en <b class="text-ink">{pharmacy}</b> · pagas al retirar</p>{/if}
	<button type="button" onclick={() => onConfirm?.()} class="mt-3 w-full rounded-full bg-primary-strong py-3 font-semibold text-white">{cta}</button>
</article>
