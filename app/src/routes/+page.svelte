<script lang="ts">
	import { tick } from 'svelte';
	import { listen, reply } from '#lib/mock/assistant.js';
	import { DEMO } from '#lib/mock/demo.js';
	import Card from '#lib/cards/Card.svelte';
	import type { Msg } from '#lib/cards/types.js';

	let messages: Msg[] = $state(new URLSearchParams(location.search).has('demo') ? [...DEMO] : []);
	let input = $state('');
	let busy = $state(false);
	let listening = $state(false);
	let senior = $state(false);
	let list: HTMLElement;

	$effect(() => {
		document.documentElement.classList.toggle('senior', senior);
	});

	async function send(text: string) {
		text = text.trim();
		if (!text || busy) return;
		messages.push({ role: 'user', text });
		input = '';
		busy = true;
		await scroll();
		messages.push({ role: 'assistant', text: await reply(text) });
		busy = false;
		await scroll();
	}

	async function mic() {
		if (listening || busy) return;
		listening = true;
		const text = await listen();
		listening = false;
		send(text);
	}

	async function demo() {
		messages = [...DEMO];
		await scroll();
	}

	async function scroll() {
		await tick();
		list?.scrollTo({ top: list.scrollHeight, behavior: 'smooth' });
	}
</script>

<div class="mx-auto flex h-dvh max-w-md flex-col bg-bg">
	<div class="h-1.5 bg-primary"></div>
	<header class="flex items-center gap-3 border-b border-line px-4 py-3">
		<span class="grid size-11 shrink-0 place-items-center rounded-2xl bg-primary text-white" aria-hidden="true">
			<svg viewBox="0 0 24 24" class="size-6" fill="currentColor"><path d="M10 4h4v6h6v4h-6v6h-4v-6H4v-4h6z" /></svg>
		</span>
		<div class="min-w-0 flex-1">
			<h1 class="text-xl leading-tight font-bold">Farmacéutico Virtual</h1>
			<span class="mt-0.5 inline-block rounded-full bg-cream px-2.5 py-0.5 text-xs font-semibold text-secondary">Demo · datos simulados</span>
		</div>
		<button
			type="button"
			onclick={() => (senior = !senior)}
			aria-pressed={senior}
			aria-label="Letra grande"
			class="grid size-11 place-items-center rounded-full border-2 font-bold {senior ? 'border-ink bg-ink text-white' : 'border-line bg-card'}"
		>
			Aa
		</button>
	</header>

	<main bind:this={list} class="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
		{#if messages.length === 0}
			<div class="mt-8 text-center">
				<p class="text-3xl font-bold">¡Hola! 👋</p>
				<p class="mt-2 text-xl">Soy tu farmacéutico más cercano.</p>
				<p class="mt-1 text-lg text-muted">Toca el micrófono y dime qué necesitas.</p>
				<button type="button" onclick={demo} class="mt-6 rounded-full border-2 border-primary-strong px-5 py-2 font-semibold text-primary-strong">
					Ver un ejemplo
				</button>
			</div>
		{/if}
		{#each messages as m, i (i)}
			{#if m.card}
				<div class="max-w-[92%]"><Card card={m.card} /></div>
			{:else}
				<div
					class="w-fit max-w-[85%] rounded-bubble px-4 py-2.5 text-lg leading-snug {m.role === 'user'
						? 'ml-auto rounded-br-md bg-primary-strong text-white'
						: 'rounded-bl-md border border-line bg-card'}"
				>
					{m.text}
				</div>
			{/if}
		{/each}
		{#if busy}<p class="text-muted">Escribiendo…</p>{/if}
	</main>

	<div class="flex flex-col items-center gap-3 border-t border-line bg-card p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
		<button
			type="button"
			onclick={mic}
			aria-label={listening ? 'Escuchando' : 'Hablar'}
			aria-pressed={listening}
			class="flex size-24 items-center justify-center rounded-full text-white shadow-mic ring-8 transition {listening
				? 'animate-pulse bg-secondary ring-secondary/20'
				: 'bg-primary-strong ring-primary/25 active:scale-95'}"
		>
			<svg viewBox="0 0 24 24" class="size-11" fill="currentColor" aria-hidden="true">
				<path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2Z" />
			</svg>
		</button>
		<p class="font-semibold text-muted">{listening ? 'Te escucho…' : 'Toca para hablar'}</p>

		<form class="flex w-full gap-2" onsubmit={(e) => (e.preventDefault(), send(input))}>
			<input
				bind:value={input}
				placeholder="O escribe aquí…"
				aria-label="Escribe tu pregunta"
				class="min-w-0 flex-1 rounded-full border-2 border-line bg-bg px-4 py-3 text-lg outline-none placeholder:text-muted focus:border-primary-strong"
			/>
			<button type="submit" class="rounded-full bg-ink px-5 font-semibold text-white disabled:opacity-40" disabled={!input.trim() || busy}>
				Enviar
			</button>
		</form>
	</div>
</div>
