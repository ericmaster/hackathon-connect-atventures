<script lang="ts">
	import { cedulaEc } from '#lib/a2ui/checks.js';
	let {
		label = 'Número de cédula',
		value = '',
		onSubmit,
		onTooMany
	}: { label?: string; value?: string; onSubmit?: (cedula: string) => void; onTooMany?: () => void } = $props();
	let v = $state('');
	$effect(() => {
		if (value) v = String(value);
	});
	let error = $state('');
	let attempts = $state(0);
	function submit(e: Event) {
		e.preventDefault();
		const c = v.replace(/\D/g, '');
		if (!cedulaEc(c)) {
			attempts++;
			error = attempts >= 3 ? 'No logro validarla. Te paso con un farmacéutico.' : 'Mmm, no me cuadra. ¿Me la repites?';
			if (attempts >= 3) onTooMany?.();
			return;
		}
		error = '';
		onSubmit?.(c);
	}
</script>

<form class="rounded-card border border-line bg-card p-4 shadow-card" onsubmit={submit}>
	<label class="block text-lg font-semibold" for="cedula-in">{label}</label>
	<input
		id="cedula-in"
		bind:value={v}
		oninput={() => (error = '')}
		inputmode="numeric"
		autocomplete="off"
		maxlength="10"
		placeholder="10 dígitos"
		aria-invalid={!!error}
		class="mt-2 w-full rounded-2xl border-2 bg-bg px-4 py-3 text-center font-mono text-3xl tracking-widest outline-none focus:border-primary-strong {error ? 'border-danger' : 'border-line'}"
	/>
	{#if error}<p class="mt-2 font-semibold text-danger" role="alert">{error}</p>{/if}
	<button type="submit" class="mt-3 w-full rounded-full bg-primary-strong py-3 text-lg font-semibold text-white">Continuar</button>
	<p class="mt-2 text-center text-xs text-muted">Se valida en tu teléfono (módulo 10). Datos sintéticos.</p>
</form>
