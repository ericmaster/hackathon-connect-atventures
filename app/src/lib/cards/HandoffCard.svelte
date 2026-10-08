<script lang="ts">
	let {
		summary,
		pharmacy,
		phone,
		onLlamar,
		onComoLlegar
	}: { summary?: string; pharmacy?: string; phone?: string; onLlamar?: () => void; onComoLlegar?: () => void } = $props();
</script>

<article class="rounded-card border-2 border-primary-strong bg-card p-4 shadow-card">
	<p class="text-xs font-semibold tracking-wider text-primary-strong uppercase">Farmacéutico humano</p>
	<h3 class="mt-1 text-xl font-bold">Habla con un farmacéutico</h3>
	{#if summary}<p class="mt-2 rounded-2xl bg-cream p-3 text-sm"><b>Resumen para el farmacéutico:</b> {summary}</p>{/if}
	{#if pharmacy}<p class="mt-2">{pharmacy}{#if phone}<span class="text-muted"> · {phone}</span>{/if}</p>{/if}
	<div class="mt-3 flex gap-2 font-semibold *:flex-1">
		<button type="button" onclick={() => onLlamar?.()} class="rounded-full bg-primary-strong py-2.5 text-white">Llamar</button>
		<button type="button" onclick={() => onComoLlegar?.()} class="rounded-full border border-primary-strong py-2.5 text-primary-strong">Cómo llegar</button>
	</div>
	<p class="mt-2 text-center text-xs text-muted">Demo: canal simulado.</p>
</article>
