<script lang="ts">
	import type { Line } from './types.js';
	let { items, total, cashback }: { items: Line[]; total: string; cashback: string } = $props();
</script>

<article class="rounded-card border border-line bg-card p-4 shadow-card">
	<h3 class="text-lg font-bold">Tu pedido</h3>
	<ul class="mt-2 divide-y divide-line">
		{#each items as it (it.name)}
			<li class="flex justify-between py-2"><span>{it.qty} × {it.name}</span><span class="font-semibold">{it.price}</span></li>
		{/each}
	</ul>
	<div class="mt-2 flex justify-between border-t-2 border-ink pt-2 text-xl font-bold"><span>Total</span><span>{total}</span></div>
	<p class="mt-1 text-right text-sm font-semibold text-primary-strong">Ganas {cashback} de cashback</p>
	<button type="button" class="mt-3 w-full rounded-full bg-primary-strong py-3 font-semibold text-white">Confirmar pedido</button>
</article>
