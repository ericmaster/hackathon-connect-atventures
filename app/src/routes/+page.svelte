<script lang="ts">
	import { tick } from 'svelte';
	import { listen, reply } from '#lib/mock/assistant.js';

	type Msg = { role: 'user' | 'assistant'; text: string };

	let messages: Msg[] = $state([]);
	let input = $state('');
	let busy = $state(false);
	let listening = $state(false);
	let list: HTMLElement;

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

	async function scroll() {
		await tick();
		list?.scrollTo({ top: list.scrollHeight, behavior: 'smooth' });
	}
</script>

<div class="mx-auto flex h-dvh max-w-md flex-col bg-white text-slate-900">
	<header class="bg-teal-700 px-4 py-3 text-white">
		<h1 class="text-lg font-semibold">Farma Asistente</h1>
	</header>

	<main bind:this={list} class="flex-1 space-y-3 overflow-y-auto p-4" aria-live="polite">
		{#if messages.length === 0}
			<div class="mt-10 text-center text-slate-600">
				<p class="text-2xl font-semibold text-slate-800">¡Hola! 👋</p>
				<p class="mt-2 text-lg">Toca el micrófono y dime qué necesitas.</p>
			</div>
		{/if}
		{#each messages as m, i (i)}
			<div
				class="max-w-[85%] rounded-2xl px-4 py-2 text-lg {m.role === 'user'
					? 'ml-auto bg-teal-700 text-white'
					: 'bg-slate-100'}"
			>
				{m.text}
			</div>
		{/each}
		{#if busy}<p class="text-slate-500">Escribiendo…</p>{/if}
	</main>

	<div class="flex flex-col items-center gap-3 border-t border-slate-200 p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
		<button
			type="button"
			onclick={mic}
			aria-label={listening ? 'Escuchando' : 'Hablar'}
			aria-pressed={listening}
			class="flex size-24 items-center justify-center rounded-full text-white shadow-lg transition {listening
				? 'animate-pulse bg-red-600'
				: 'bg-teal-700 active:scale-95'}"
		>
			<svg viewBox="0 0 24 24" class="size-10" fill="currentColor" aria-hidden="true">
				<path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2Z" />
			</svg>
		</button>
		<p class="text-sm text-slate-600">{listening ? 'Escuchando…' : 'Toca para hablar'}</p>

		<form class="flex w-full gap-2" onsubmit={(e) => (e.preventDefault(), send(input))}>
			<input
				bind:value={input}
				placeholder="Escribe tu pregunta…"
				aria-label="Escribe tu pregunta"
				class="min-w-0 flex-1 rounded-full border border-slate-300 px-4 py-3 text-lg outline-none focus:border-teal-700"
			/>
			<button type="submit" class="rounded-full bg-slate-800 px-5 text-white disabled:opacity-40" disabled={!input.trim() || busy}>
				Enviar
			</button>
		</form>

		<span class="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-900">Demo · datos simulados</span>
	</div>
</div>
