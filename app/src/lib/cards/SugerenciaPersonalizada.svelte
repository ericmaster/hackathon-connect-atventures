<script lang="ts">
	import type { Product } from './types.js';
	let { habit, product }: { habit: string; product: Product } = $props();
</script>

<article class="rounded-card border-2 border-accent bg-card p-4 shadow-card">
	<p class="text-xs font-semibold tracking-wider text-accent-strong uppercase">Para ti</p>
	<p class="mt-1 text-lg leading-snug">Como sueles llevar <b>{habit}</b>, ¿lo sumamos a tu pedido?</p>
	<div class="mt-3 flex items-center justify-between rounded-2xl bg-cream p-3">
		<div>
			<p class="font-bold">{product.name}</p>
			<p class="text-sm text-muted">{product.detail} · {product.cashback}</p>
		</div>
		<p class="font-bold">{product.price}</p>
	</div>
	<button type="button" class="mt-3 w-full rounded-full bg-primary-strong py-3 font-semibold text-white">Reservar</button>
	<button type="button" class="mt-2 w-full text-sm font-semibold text-accent-strong underline">¿Por qué me sugieres esto?</button>
</article>
