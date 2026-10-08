<script lang="ts">
	import type { Product } from './types.js';
	let {
		name,
		detail,
		price,
		cashback,
		stock,
		note,
		ventaLibre = true,
		cta = 'Agregar al pedido',
		onAdd
	}: Product & { cta?: string; onAdd?: () => void } = $props();
</script>

<article class="rounded-card border border-line bg-card p-4 shadow-card">
	<div class="flex items-start justify-between gap-3">
		<div>
			<h3 class="text-lg leading-tight font-bold">{name}</h3>
			{#if detail}<p class="text-muted">{detail}</p>{/if}
		</div>
		<p class="text-xl font-bold whitespace-nowrap">{price}</p>
	</div>
	<div class="mt-2 flex flex-wrap gap-2 text-sm font-semibold">
		{#if ventaLibre}<span class="rounded-full bg-cream px-3 py-1 text-ink">Venta libre</span>{/if}
		{#if cashback}<span class="rounded-full bg-cream px-3 py-1 text-primary-strong">{cashback}</span>{/if}
		{#if stock}<span class="rounded-full bg-cream px-3 py-1 text-success-strong">{stock}</span>{/if}
	</div>
	{#if note}<p class="mt-2 text-sm text-muted">{note}</p>{/if}
	<button type="button" onclick={() => onAdd?.()} class="mt-3 w-full rounded-full bg-primary-strong py-3 font-semibold text-white active:scale-[.98]">
		{cta}
	</button>
</article>
