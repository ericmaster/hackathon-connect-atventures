<script lang="ts">
	let { text }: { text: string } = $props();
</script>

<article role="alert" class="rounded-card bg-alerta p-4 text-white shadow-card">
	<div class="flex items-center gap-2">
		<svg viewBox="0 0 24 24" class="size-7 shrink-0" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 2 20h20L12 3Z" /><path d="M12 10v4M12 17h.01" /></svg>
		<h3 class="text-xl font-bold">Atención urgente</h3>
	</div>
	<p class="mt-2 text-lg leading-snug">{text}</p>
	<!-- Demo: no marca. Real = tel:911 -->
	<button type="button" class="mt-3 w-full rounded-full bg-white py-3 text-lg font-bold text-alerta">Llamar al ECU 911</button>
	<p class="mt-2 text-center text-sm opacity-90">Demo: este botón no llama.</p>
</article>
