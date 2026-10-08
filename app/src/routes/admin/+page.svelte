<script lang="ts">
	import { API_URL } from '#lib/api/auth.js';
	import { TABS, loadService, isInternal, type Row, type TabId } from './api';

	let tab = $state<TabId>('crm');
	let rows = $state<Row[]>([]);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let loadedAt = $state<string | null>(null);
	let filter = $state('');
	let ctrl: AbortController | null = null;

	const columns = $derived.by(() => {
		const cols: string[] = [];
		for (const r of rows.slice(0, 50)) for (const k of Object.keys(r)) if (!cols.includes(k)) cols.push(k);
		// internos al final
		return [...cols.filter((c) => !isInternal(c)), ...cols.filter(isInternal)];
	});

	const shown = $derived.by(() => {
		const q = filter.trim().toLowerCase();
		return q ? rows.filter((r) => JSON.stringify(r).toLowerCase().includes(q)) : rows;
	});

	async function refresh() {
		ctrl?.abort();
		const c = new AbortController();
		ctrl = c;
		loading = true;
		error = null;
		try {
			const items = await loadService(tab, c.signal);
			if (c.signal.aborted) return;
			rows = items;
			loadedAt = new Date().toLocaleTimeString('es-EC');
		} catch (e) {
			if (c.signal.aborted) return;
			rows = [];
			error = API_URL ? String((e as Error)?.message ?? e) : 'API no configurada (VITE_FV_API_URL vacío).';
		} finally {
			if (ctrl === c) loading = false;
		}
	}

	function select(id: TabId) {
		tab = id;
		filter = '';
		void refresh();
	}

	function cell(v: unknown): string {
		if (v === null || v === undefined) return '—';
		if (typeof v === 'object') {
			const s = JSON.stringify(v);
			return s.length > 160 ? s.slice(0, 160) + '…' : s;
		}
		return String(v);
	}

	$effect(() => {
		void refresh();
		return () => ctrl?.abort();
	});
</script>

<svelte:head><title>Admin · Farmacéutico Virtual</title></svelte:head>

<main class="min-h-dvh bg-bg p-4 text-ink">
	<header class="mb-3 flex flex-wrap items-center gap-3">
		<h1 class="text-2xl font-bold">Admin <span class="font-normal text-muted">· solo lectura</span></h1>
		<span class="rounded-full bg-cream px-3 py-1 text-sm">Demo · datos sintéticos</span>
		<div class="ml-auto flex items-center gap-2">
			{#if loadedAt}<span class="text-sm text-muted">Actualizado {loadedAt}</span>{/if}
			<button
				class="min-h-11 rounded-full bg-primary-strong px-5 font-semibold text-white disabled:opacity-60"
				onclick={refresh}
				disabled={loading}>{loading ? 'Cargando…' : 'Actualizar'}</button
			>
		</div>
	</header>

	<div class="mb-3 flex flex-wrap gap-2" role="tablist" aria-label="Servicios">
		{#each TABS as t (t.id)}
			<button
				role="tab"
				aria-selected={tab === t.id}
				class="min-h-11 rounded-full border-2 px-4 font-semibold {tab === t.id
					? 'border-primary-strong bg-primary-strong text-white'
					: 'border-line bg-card text-ink'}"
				onclick={() => select(t.id)}>{t.label}</button
			>
		{/each}
	</div>

	<div class="mb-3 flex items-center gap-3">
		<input
			class="min-h-11 w-full max-w-sm rounded-full border-2 border-line bg-card px-4 focus:border-primary-strong focus:outline-none"
			placeholder="Filtrar…"
			bind:value={filter}
		/>
		<span class="text-sm text-muted">{shown.length} de {rows.length} registros</span>
	</div>

	{#if tab === 'crm'}
		<p class="mb-3 rounded-card border-2 border-warning bg-cream p-3 text-sm">
			Las <b>condiciones probables</b> son un dato <b>interno, no visible al cliente</b>: solo filtran sugerencias en
			el servidor y nunca se verbalizan.
		</p>
	{/if}

	{#if error}
		<p class="rounded-card border-2 border-danger bg-card p-4" role="alert">{error}</p>
	{:else if !loading && rows.length === 0}
		<p class="rounded-card bg-card p-4 text-muted">Sin registros.</p>
	{:else}
		<div class="overflow-auto rounded-card bg-card shadow-card">
			<table class="w-full border-collapse text-left text-sm">
				<thead class="sticky top-0 bg-cream">
					<tr>
						{#each columns as c (c)}
							<th class="whitespace-nowrap border-b border-line px-3 py-2 font-semibold">
								{c}
								{#if isInternal(c)}<span class="block text-xs font-normal text-secondary"
										>interno, no visible al cliente</span
									>{/if}
							</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each shown as r, i (i)}
						<tr class="odd:bg-bg/50 align-top">
							{#each columns as c (c)}
								<td
									class="border-b border-line px-3 py-2 {isInternal(c) ? 'bg-cream italic text-secondary' : ''}"
									title={typeof r[c] === 'object' ? JSON.stringify(r[c]) : undefined}>{cell(r[c])}</td
								>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</main>
