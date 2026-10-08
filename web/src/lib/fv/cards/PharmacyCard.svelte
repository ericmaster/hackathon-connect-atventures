<script lang="ts">
	import type { Pharmacy } from './types.js';
	let {
		name,
		distance,
		hours,
		stock,
		onRetirar,
		onComoLlegar,
		onLlamar
	}: Pharmacy & { onRetirar?: () => void; onComoLlegar?: () => void; onLlamar?: () => void } = $props();
</script>

<article class="rounded-card border border-line bg-card p-4 shadow-card">
	<div class="flex items-center gap-3">
		<span class="grid size-11 shrink-0 place-items-center rounded-2xl bg-cream text-primary-strong" aria-hidden="true">
			<svg viewBox="0 0 24 24" class="size-6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11Z" /><circle cx="12" cy="10" r="2.5" /></svg>
		</span>
		<div>
			<h3 class="text-lg leading-tight font-bold">{name}</h3>
			<p class="text-muted">{[distance, hours].filter(Boolean).join(' · ')}</p>
		</div>
	</div>
	{#if stock}<p class="mt-2 text-sm font-semibold text-success-strong">{stock}</p>{/if}
	<div class="mt-3 flex flex-wrap gap-2 text-sm font-semibold *:flex-1 *:px-3 *:whitespace-nowrap">
		<button type="button" onclick={() => onRetirar?.()} class="rounded-full bg-primary-strong py-2.5 text-white">Retirar aquí</button>
		<button type="button" onclick={() => onComoLlegar?.()} class="rounded-full border border-primary-strong py-2.5 text-primary-strong">Cómo llegar</button>
		<button type="button" onclick={() => onLlamar?.()} class="rounded-full border border-primary-strong py-2.5 text-primary-strong">Llamar</button>
	</div>
</article>
