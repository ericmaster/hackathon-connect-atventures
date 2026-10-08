<script lang="ts">
	let { title, code, until, note }: { title: string; code: string; until?: string; note?: string } = $props();
	// QR falso (decorativo, demo): patrón determinístico.
	const cells = Array.from({ length: 49 }, (_, i) => ((i * 2654435761) >>> 13) % 2 === 0);
</script>

<article class="flex items-center gap-3 rounded-card border-2 border-dashed border-accent bg-cream p-4">
	<div class="flex-1">
		<p class="text-xs font-semibold tracking-wider text-accent-strong uppercase">Cupón smart</p>
		<p class="mt-1 text-2xl leading-tight font-bold text-secondary">{title}</p>
		<p class="mt-2 inline-block rounded-full bg-card px-3 py-1 font-mono font-semibold">{code}</p>
		{#if until}<p class="mt-2 text-sm text-muted">{until}</p>{/if}
		{#if note}<p class="mt-1 text-sm font-semibold">{note}</p>{/if}
	</div>
	<div class="grid size-24 shrink-0 grid-cols-7 gap-px rounded-xl bg-card p-2" role="img" aria-label="QR de ejemplo">
		{#each cells as on, i (i)}<span class={on ? 'bg-ink' : ''}></span>{/each}
	</div>
</article>
