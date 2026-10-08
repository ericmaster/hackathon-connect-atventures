<script lang="ts">
	import type { Product } from './types.js';
	let {
		habit,
		message,
		product,
		why,
		onReservar
	}: { habit?: string; message?: string; product: Product; why?: string; onReservar?: () => void } = $props();
	let open = $state(false);
	const whyText = $derived(why || `Te lo sugiero porque sueles comprar ${product?.name ?? 'este producto'} con cierta frecuencia. Solo uso tu historial de compras, nunca información de salud.`);
</script>

<article class="rounded-card border-2 border-accent bg-card p-4 shadow-card">
	<p class="text-xs font-semibold tracking-wider text-accent-strong uppercase">Para ti</p>
	<p class="mt-1 text-lg leading-snug">
		{#if message}{message}{:else}Como sueles llevar <b>{habit}</b>, ¿lo sumamos a tu pedido?{/if}
	</p>
	<div class="mt-3 flex items-center justify-between gap-2 rounded-2xl bg-cream p-3">
		<div>
			<p class="font-bold">{product?.name}</p>
			<p class="text-sm text-muted">{[product?.detail, product?.cashback].filter(Boolean).join(' · ')}</p>
		</div>
		<p class="font-bold whitespace-nowrap">{product?.price}</p>
	</div>
	<button type="button" onclick={() => onReservar?.()} class="mt-3 w-full rounded-full bg-primary-strong py-3 font-semibold text-white">Reservar</button>
	<button type="button" onclick={() => (open = !open)} aria-expanded={open} class="mt-2 w-full py-2 text-sm font-semibold text-accent-strong underline">
		¿Por qué me sugieres esto?
	</button>
	{#if open}<p class="rounded-2xl bg-cream p-3 text-sm">{whyText}</p>{/if}
</article>
