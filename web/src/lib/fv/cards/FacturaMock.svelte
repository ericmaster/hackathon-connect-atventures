<script lang="ts">
	import type { Line } from './types.js';
	let {
		number,
		customerName,
		customerId,
		email,
		items = [],
		subtotal,
		iva,
		discount,
		total,
		label = 'SIMULADA'
	}: {
		number?: string;
		customerName?: string;
		customerId?: string;
		email?: string;
		items?: Line[];
		subtotal?: string;
		iva?: string;
		discount?: string;
		total: string;
		label?: string;
	} = $props();
	const disc = $derived(discount && !discount.startsWith('-') && !discount.startsWith('−') ? '−' + discount : discount);
</script>

<article class="relative overflow-hidden rounded-card border border-line bg-card p-4 shadow-card">
	<div class="flex items-center justify-between">
		<h3 class="text-lg font-bold">Factura electrónica</h3>
		<span class="rounded-full border-2 border-danger px-3 py-0.5 text-sm font-bold tracking-wider text-danger">{label || 'SIMULADA'}</span>
	</div>
	<p class="text-sm text-muted">Documento de demostración · sin validez tributaria</p>
	<dl class="mt-2 grid grid-cols-[auto_1fr] gap-x-3 text-sm">
		{#if number}<dt class="text-muted">N.º</dt><dd class="font-mono">{number}</dd>{/if}
		{#if customerName}<dt class="text-muted">Cliente</dt><dd>{customerName}</dd>{/if}
		{#if customerId}<dt class="text-muted">ID</dt><dd class="font-mono">{customerId}</dd>{/if}
		{#if email}<dt class="text-muted">Email</dt><dd class="break-all">{email}</dd>{/if}
	</dl>
	{#if items.length}
		<ul class="mt-2 divide-y divide-line text-sm">
			{#each items as it, i (i)}<li class="flex justify-between py-1"><span>{it.qty} × {it.name}</span><span>{it.price}</span></li>{/each}
		</ul>
	{/if}
	<div class="mt-2 space-y-0.5 border-t border-line pt-2 text-sm">
		{#if subtotal}<p class="flex justify-between"><span>Subtotal</span><span>{subtotal}</span></p>{/if}
		{#if iva}<p class="flex justify-between"><span>IVA</span><span>{iva}</span></p>{/if}
		{#if discount}<p class="flex justify-between text-secondary"><span>Descuento cupón</span><span>{disc}</span></p>{/if}
		<p class="flex justify-between text-lg font-bold"><span>Total</span><span>{total}</span></p>
	</div>
	<p class="mt-2 text-xs text-muted">Se enviaría por email (demo: no se envía nada).</p>
</article>
