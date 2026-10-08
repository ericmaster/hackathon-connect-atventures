<script lang="ts">
	// QR decorativo determinístico a partir de un texto (demo, no escaneable).
	let { value, size = 'size-28' }: { value: string; size?: string } = $props();
	const cells = $derived.by(() => {
		let h = 2166136261;
		for (const ch of value ?? '') h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
		return Array.from({ length: 81 }, (_, i) => {
			const r = Math.floor(i / 9), c = i % 9;
			const finder = (r < 3 && c < 3) || (r < 3 && c > 5) || (r > 5 && c < 3);
			if (finder) return !(r % 8 === 1 && c % 8 === 1) || (r === 1 && c === 1);
			h = Math.imul(h ^ i, 16777619);
			return (h >>> 7) % 2 === 0;
		});
	});
</script>

<div class="grid {size} shrink-0 grid-cols-9 gap-px rounded-xl border border-line bg-card p-2" role="img" aria-label="Código QR de retiro (demo)">
	{#each cells as on, i (i)}<span class={on ? 'bg-ink' : ''}></span>{/each}
</div>
