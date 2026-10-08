<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { SurfaceStore } from '#lib/a2ui/surfaces.svelte.js';
	import SurfaceView from '#lib/a2ui/Surface.svelte';
	import { parseMessages } from '#lib/a2ui/surfaces.svelte.js';
	import type { A2uiAction } from '#lib/a2ui/types.js';
	import { pickTransport, fakeTransport, type Transport } from '#lib/api/index.js';
	import { toActionBody, type FvResponse } from '#lib/api/transport.js';
	import { FV_CACHE_KEY, fakeTranscript } from '#lib/api/fake.js';
	import { fakeVoice, loadVoice, setFakePhrase, type VoiceClient } from '#lib/voice-client.js';

	type Entry = { key: number; kind: 'user' | 'error' | 'surface'; text?: string; id?: string };

	let transport: Transport = $state(pickTransport());
	const store = new SurfaceStore();
	let entries: Entry[] = $state([]);
	let sessionId: string | null = null;
	let revision = 0;
	let fsmState = $state('');
	let mode: 'real' | 'simulado' = $state('simulado');
	let input = $state('');
	let busy = $state(false);
	let listening = $state(false);
	let partial = $state('');
	let senior = $state(false);
	let startError = $state('');
	let voice: VoiceClient = $state(fakeVoice);
	let list: HTMLElement;
	let ac: AbortController | null = null;
	let k = 0;

	const simulated = $derived(transport.kind === 'fake' || mode === 'simulado');
	const latestSurface = $derived([...entries].reverse().find((e) => e.kind === 'surface')?.id);

	$effect(() => {
		document.documentElement.classList.toggle('senior', senior);
	});

	onMount(async () => {
		voice = await loadVoice(transport.kind === 'http');
		await start();
	});

	async function start() {
		startError = '';
		busy = true;
		try {
			handle(await transport.start());
		} catch (e) {
			startError = `No pude conectar con la API (${(e as Error).message}).`;
		} finally {
			busy = false;
		}
	}

	async function useFake() {
		transport = fakeTransport;
		voice = fakeVoice;
		await start();
	}

	function handle(res: FvResponse) {
		sessionId = res.sessionId;
		revision = res.revision;
		fsmState = res.state;
		mode = res.mode ?? 'simulado';
		const msgs = parseMessages(res.messages);
		const { created, deleted } = store.apply(msgs);
		if (deleted.length) entries = entries.filter((e) => !(e.kind === 'surface' && deleted.includes(e.id!)));
		for (const id of created) entries.push({ key: k++, kind: 'surface', id });
		if (msgs.some((m) => m.createSurface?.theme?.senior === true || m.createSurface?.theme?.fontScale === 'large')) senior = true;
		if (res.error) entries.push({ key: k++, kind: 'error', text: res.error.message });
		setFakePhrase(fakeTranscript(res.state));
		if (res.spokenText) Promise.resolve(voice.speak(res.spokenText)).catch(() => undefined);
		scrollToLast();
	}

	async function call(fn: (signal: AbortSignal) => Promise<FvResponse>) {
		if (!sessionId) return;
		busy = true;
		ac = new AbortController();
		try {
			handle(await fn(ac.signal));
		} catch (e) {
			if ((e as Error).name !== 'AbortError')
				entries.push({ key: k++, kind: 'error', text: 'Uy, no pude responder. Intenta de nuevo. No se hizo ningún cambio.' });
		} finally {
			busy = false;
			ac = null;
			scrollToLast();
		}
	}

	async function send(text: string) {
		text = text.trim();
		if (!text || busy) return;
		entries.push({ key: k++, kind: 'user', text });
		input = '';
		await call((signal) => transport.turn(sessionId!, text, signal));
	}

	function onAction(a: A2uiAction) {
		if (busy) return;
		call((signal) => transport.action(sessionId!, revision, toActionBody(a), signal));
	}

	async function mic() {
		if (listening) {
			voice.stopListening();
			return;
		}
		if (busy) return;
		listening = true;
		partial = '';
		try {
			await voice.startListening(
				(p) => (partial = p),
				(f) => {
					listening = false;
					partial = '';
					if (f.trim()) send(f);
				}
			);
		} catch (e) {
			listening = false;
			partial = '';
			const msg = (e as { userMessage?: string }).userMessage ?? 'No pude usar el micrófono. Habilítalo en tu navegador; puedes escribir abajo.';
			entries.push({ key: k++, kind: 'error', text: msg });
		}
	}

	/** SPEC §7.8: cancela solicitudes/audio, limpia chat, carrito y caché FV y crea nueva sesión. */
	async function reset() {
		ac?.abort();
		voice.cancel?.();
		voice.stopListening();
		listening = false;
		partial = '';
		entries = [];
		store.clear();
		input = '';
		senior = false;
		localStorage.removeItem(FV_CACHE_KEY);
		sessionStorage.clear();
		busy = true;
		try {
			handle(await transport.reset(sessionId));
		} catch {
			startError = 'No pude reiniciar la sesión.';
		} finally {
			busy = false;
		}
	}

	async function scrollToLast() {
		await tick();
		const last = list?.querySelector('[data-entry]:last-of-type') as HTMLElement | null;
		if (last) list.scrollTo({ top: last.offsetTop - 8, behavior: 'smooth' });
	}
</script>

<div class="mx-auto flex h-dvh max-w-md flex-col bg-bg">
	<div class="h-1.5 bg-primary"></div>
	<header class="border-b border-line px-4 pt-3 pb-2">
		<div class="flex items-center gap-3">
			<span class="grid size-11 shrink-0 place-items-center rounded-2xl bg-primary text-white" aria-hidden="true">
				<svg viewBox="0 0 24 24" class="size-6" fill="currentColor"><path d="M10 4h4v6h6v4h-6v6h-4v-6H4v-4h6z" /></svg>
			</span>
			<h1 class="min-w-0 flex-1 text-xl leading-tight font-bold">Farmacéutico Virtual</h1>
			<button
				type="button"
				onclick={() => (senior = !senior)}
				aria-pressed={senior}
				aria-label="Letra grande"
				class="grid size-11 shrink-0 place-items-center rounded-full border-2 font-bold {senior ? 'border-ink bg-ink text-white' : 'border-line bg-card'}"
			>
				Aa
			</button>
		</div>
		<div class="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs font-semibold">
			<span class="rounded-full bg-cream px-2.5 py-0.5 text-secondary">Demo · datos simulados</span>
			{#if simulated}
				<span class="rounded-full bg-warning px-2.5 py-0.5 text-ink" data-testid="mode-badge">IA y servicios simulados</span>
			{:else}
				<span class="rounded-full bg-success-strong px-2.5 py-0.5 text-white" data-testid="mode-badge">IA real · datos sintéticos</span>
			{/if}
			<button type="button" onclick={reset} class="ml-auto rounded-full border-2 border-secondary px-3 py-1 text-sm font-bold text-secondary" data-testid="reset">
				↺ Reiniciar demo
			</button>
		</div>
		<p class="mt-1 text-xs text-muted">Solo productos de venta libre · No diagnostica · No reemplaza la consulta médica</p>
	</header>

	<main bind:this={list} class="relative flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
		{#if startError}
			<div class="rounded-card border-2 border-danger bg-card p-4">
				<p class="font-semibold">{startError}</p>
				<div class="mt-3 flex gap-2 *:flex-1">
					<button type="button" onclick={start} class="rounded-full bg-primary-strong py-2.5 font-semibold text-white">Reintentar</button>
					<button type="button" onclick={useFake} class="rounded-full border-2 border-primary-strong py-2.5 font-semibold text-primary-strong">Usar modo simulado</button>
				</div>
			</div>
		{/if}
		{#each entries as e (e.key)}
			{#if e.kind === 'surface' && store.surfaces[e.id!]}
				<div data-entry class="max-w-[96%] transition-opacity {e.id === latestSurface ? '' : 'opacity-60'}" inert={e.id !== latestSurface}>
					<SurfaceView surface={store.surfaces[e.id!]} {onAction} />
				</div>
			{:else if e.kind === 'user'}
				<div data-entry class="ml-auto w-fit max-w-[85%] rounded-bubble rounded-br-md bg-primary-strong px-4 py-2.5 text-lg leading-snug text-white">{e.text}</div>
			{:else if e.kind === 'error'}
				<div data-entry class="w-fit max-w-[85%] rounded-bubble rounded-bl-md border-2 border-danger bg-card px-4 py-2.5 text-lg" role="alert">{e.text}</div>
			{/if}
		{/each}
		{#if busy}<p class="text-muted">Pensando…</p>{/if}
	</main>

	<div class="flex flex-col items-center gap-2 border-t border-line bg-card p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]">
		{#if partial}<p class="w-full rounded-2xl bg-cream px-3 py-1.5 text-center text-lg italic">“{partial}”</p>{/if}
		<div class="flex w-full items-center gap-3">
			<button
				type="button"
				onclick={mic}
				aria-label={listening ? 'Dejar de escuchar' : 'Hablar'}
				aria-pressed={listening}
				class="flex size-20 shrink-0 items-center justify-center rounded-full text-white shadow-mic ring-8 transition {listening
					? 'animate-pulse bg-secondary ring-secondary/20'
					: 'bg-primary-strong ring-primary/25 active:scale-95'}"
			>
				<svg viewBox="0 0 24 24" class="size-10" fill="currentColor" aria-hidden="true">
					<path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2Z" />
				</svg>
			</button>
			<div class="min-w-0 flex-1">
				<p class="mb-1 text-sm font-semibold text-muted">
					{listening ? 'Te escucho…' : 'Toca para hablar'}{voice.simulated ? ' (voz simulada)' : ''}
				</p>
				<form class="flex gap-2" onsubmit={(ev) => (ev.preventDefault(), send(input))}>
					<input
						bind:value={input}
						placeholder="O escribe aquí…"
						aria-label="Escribe tu pregunta"
						class="min-w-0 flex-1 rounded-full border-2 border-line bg-bg px-4 py-2.5 text-lg outline-none placeholder:text-muted focus:border-primary-strong"
					/>
					<button type="submit" class="rounded-full bg-ink px-4 font-semibold text-white disabled:opacity-40" disabled={!input.trim() || busy}>Enviar</button>
				</form>
			</div>
		</div>
	</div>
</div>
