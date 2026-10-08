<script lang="ts">
	let { title, code, until, note }: { title: string; code: string; until?: string; note?: string } = $props();
</script>

<article class="flex items-center gap-3 rounded-card border-2 border-dashed border-accent bg-cream p-4">
	<div class="flex-1">
		<p class="text-xs font-semibold tracking-wider text-accent-strong uppercase">Cupón smart</p>
		<p class="mt-1 text-2xl leading-tight font-bold text-secondary">{title}</p>
		<p class="mt-2 inline-block rounded-full bg-card px-3 py-1 font-mono font-semibold">{code}</p>
		{#if until}<p class="mt-2 text-sm text-muted">{until}</p>{/if}
		{#if note}<p class="mt-1 text-sm font-semibold">{note}</p>{/if}
	</div>
</article>
