<script lang="ts">
	let {
		text = 'Acepto que Farmaenlace use mi historial de compras para darme sugerencias personalizadas.',
		onSubmit
	}: { text?: string; onSubmit?: (acepta: boolean) => void } = $props();
	let acepta = $state(false);
</script>

<article class="rounded-card border border-line bg-card p-4 shadow-card">
	<h3 class="text-lg font-bold">Tu privacidad</h3>
	<label class="mt-2 flex cursor-pointer items-start gap-3 rounded-2xl bg-cream p-3">
		<input type="checkbox" bind:checked={acepta} class="mt-1 size-6 shrink-0 accent-primary-strong" />
		<span class="text-lg leading-snug">{text}</span>
	</label>
	<p class="mt-2 text-sm text-muted">Es opcional: puedes seguir sin aceptar (sin sugerencias personalizadas).</p>
	<button type="button" onclick={() => onSubmit?.(acepta)} class="mt-3 w-full rounded-full bg-primary-strong py-3 font-semibold text-white">Continuar</button>
</article>
