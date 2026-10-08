<script lang="ts">
	import { tick } from 'svelte';
	import { fly, fade } from 'svelte/transition';
	import Card from '#lib/cards/Card.svelte';
	import Cupon from '#lib/cards/Cupon.svelte';
	import type { Card as CardT } from '#lib/cards/types.js';
	import { respond, MOCK_TRANSCRIPT } from '#lib/mock/respond.js';

	const CHIPS = ['Algo para la gripe', 'Farmacia más cercana con stock', 'Mis cupones SmartClub', 'Reponer mis productos frecuentes'];
	const BRANDS = ['Medicity', 'Farmacias Económicas', 'Wellderma', 'Ambiente', 'Mascotas', 'BYD'];

	let input = $state('');
	let prompt = $state(''); // última pregunta
	let phase: 'idle' | 'thinking' | 'streaming' | 'done' = $state('idle');
	let text = $state('');
	let cards: CardT[] = $state([]);
	let follow: string[] = $state([]);
	let listening = $state(false);
	let senior = $state(false);
	let results: HTMLElement | undefined = $state();
	let heroForm: HTMLElement | undefined = $state();
	let headerH = $state(64);
	let stuck = $state(false); // barra compacta fija bajo el header cuando el prompt del hero sale de vista
	let run = 0;

	const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));

	$effect(() => {
		document.documentElement.classList.toggle('senior', senior);
	});

	$effect(() => {
		const onScroll = () => {
			if (heroForm) stuck = heroForm.getBoundingClientRect().bottom < headerH;
		};
		onScroll();
		window.addEventListener('scroll', onScroll, { passive: true });
		window.addEventListener('resize', onScroll);
		return () => {
			window.removeEventListener('scroll', onScroll);
			window.removeEventListener('resize', onScroll);
		};
	});

	// Deep link: /?q=... (p. ej. desde el QR de la farmacia)
	$effect(() => {
		const q = new URLSearchParams(location.search).get('q');
		if (q) ask(q);
	});

	// Simula streaming: pensando → texto palabra a palabra → tarjetas escalonadas.
	async function ask(q: string) {
		q = q.trim();
		if (!q) return;
		const id = ++run;
		input = '';
		prompt = q;
		text = '';
		cards = [];
		follow = [];
		phase = 'thinking';
		await tick();
		results?.scrollIntoView({ behavior: 'smooth', block: 'start' });
		const r = respond(q);
		await wait(450);
		if (id !== run) return;
		phase = 'streaming';
		for (const w of r.text.split(' ')) {
			text += (text ? ' ' : '') + w;
			await wait(28);
			if (id !== run) return;
		}
		for (const c of r.cards) {
			cards.push(c);
			await wait(220);
			if (id !== run) return;
		}
		follow = r.follow ?? [];
		phase = 'done';
	}

	async function mic() {
		if (listening || phase === 'thinking' || phase === 'streaming') return;
		listening = true; // MOCK: sin STT real todavía
		await wait(1300);
		listening = false;
		ask(MOCK_TRANSCRIPT);
	}

	const STEPS = [
		{ n: '1', t: 'Pregunta o habla', d: 'Escribe o toca el micrófono: "algo para la gripe", "mis cupones". Sin formularios ni catálogos.' },
		{ n: '2', t: 'Te armamos la pantalla', d: 'El asistente genera solo lo que necesitas: productos de venta libre, farmacia con stock y tu beneficio smart.' },
		{ n: '3', t: 'Retira y gana cashback', d: 'Reserva en la farmacia más cercana, retira y acumula cashback SmartClub en todas las marcas.' }
	];
</script>

{#snippet bar(v: 'hero' | 'compact')}
	{@const big = v === 'hero'}
	<input
		bind:value={input}
		placeholder={listening ? 'Te escucho…' : '¿Qué necesitas hoy?'}
		aria-label="Escribe tu pregunta"
		tabindex={big && stuck ? -1 : 0}
		class="min-w-0 flex-1 bg-transparent outline-none placeholder:text-muted {big ? 'py-3 text-lg md:text-xl' : 'py-1.5 text-lg'}"
	/>
	<button
		type="button"
		onclick={mic}
		aria-label={listening ? 'Escuchando' : 'Hablar (demo)'}
		aria-pressed={listening}
		class="grid shrink-0 place-items-center rounded-full text-white transition {big ? 'size-12 ring-4 md:size-14' : 'size-11 ring-2'} {listening
			? 'animate-pulse bg-secondary ring-secondary/20'
			: 'bg-primary-strong ring-primary/25 ' + (big ? 'shadow-mic' : '')}"
	>
		<svg viewBox="0 0 24 24" class={big ? 'size-6 md:size-7' : 'size-6'} fill="currentColor" aria-hidden="true">
			<path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3Zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2Z" />
		</svg>
	</button>
	<button type="submit" disabled={!input.trim()} class="hidden shrink-0 rounded-full bg-ink px-6 font-semibold text-white disabled:opacity-40 sm:block {big ? 'h-12 md:h-14' : 'h-11'}">
		Preguntar
	</button>
{/snippet}

<div class="min-h-dvh bg-bg">
	<div class="h-1.5 bg-primary"></div>

	<header bind:offsetHeight={headerH} class="sticky top-0 z-30 border-b border-line bg-bg/90 backdrop-blur">
		<div class="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3 md:px-6">
			<span class="grid size-10 shrink-0 place-items-center rounded-2xl bg-primary text-white" aria-hidden="true">
				<svg viewBox="0 0 24 24" class="size-6" fill="currentColor"><path d="M10 4h4v6h6v4h-6v6h-4v-6H4v-4h6z" /></svg>
			</span>
			<div class="min-w-0 flex-1 md:flex-none">
				<p class="text-lg leading-tight font-bold">Farmacéutico Virtual</p>
				<span class="inline-block rounded-full bg-cream px-2.5 py-0.5 text-xs font-semibold text-secondary">Demo · datos simulados</span>
			</div>
			<nav class="ml-auto hidden items-center gap-6 font-semibold text-muted md:flex">
				<a href="#como-funciona" class="hover:text-primary-strong">Cómo funciona</a>
				<a href="#qr" class="hover:text-primary-strong">QR en farmacia</a>
				<a href="#smartclub" class="hover:text-primary-strong">SmartClub</a>
			</nav>
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
	</header>

	{#if stuck}
		<div
			class="fixed inset-x-0 z-20 border-b border-line bg-bg/95 px-4 py-2 shadow-[0_6px_16px_rgb(29_29_31/0.08)] backdrop-blur md:px-6"
			style="top: {headerH}px"
			transition:fly={{ y: -8, duration: 150 }}
		>
			<form class="mx-auto flex max-w-3xl items-center gap-2 rounded-full border-2 border-line bg-card p-1.5 pl-4 focus-within:border-primary-strong" onsubmit={(e) => (e.preventDefault(), ask(input))}>
				{@render bar('compact')}
			</form>
		</div>
	{/if}

	<main>
		<!-- HERO + prompt generativo -->
		<section class="relative overflow-hidden px-4 pt-10 pb-12 md:px-6 md:pt-16">
			<div class="pointer-events-none absolute -top-40 left-1/2 size-[42rem] -translate-x-1/2 rounded-full bg-primary/10 blur-3xl" aria-hidden="true"></div>
			<div class="relative mx-auto max-w-3xl text-center">
				<p class="text-sm font-semibold tracking-wider text-accent-strong uppercase">Farmaenlace · SmartClub · demo</p>
				<h1 class="mt-3 text-4xl leading-tight font-bold md:text-6xl">Tu farmacéutico <span class="text-primary-strong">más cercano</span></h1>
				<p class="mx-auto mt-4 max-w-2xl text-lg text-muted md:text-xl">No busques en catálogos. Pregunta y te armamos la pantalla que necesitas: productos de venta libre, la farmacia con stock y tu beneficio smart.</p>

				<form
					bind:this={heroForm}
					class="mt-8 flex items-center gap-2 rounded-full border-2 border-line bg-card p-2 pl-5 shadow-card focus-within:border-primary-strong"
					onsubmit={(e) => (e.preventDefault(), ask(input))}
				>
					{@render bar('hero')}
				</form>

				<div class="mt-4 flex flex-wrap justify-center gap-2">
					{#each CHIPS as c (c)}
						<button type="button" onclick={() => ask(c)} class="min-h-11 rounded-full border border-line bg-cream px-4 py-2 font-semibold text-ink hover:border-primary-strong hover:text-primary-strong">
							{c}
						</button>
					{/each}
				</div>
				<p class="mt-4 text-sm text-muted">Solo productos de venta libre · No diagnostica · No reemplaza la consulta médica</p>
			</div>

			<!-- UI generada -->
			<div bind:this={results} class="relative mx-auto max-w-6xl scroll-mt-40" aria-live="polite">
				{#if phase !== 'idle'}
					<div class="mt-10 rounded-[2rem] border border-line bg-card/60 p-4 md:p-6" in:fade>
						<div class="flex flex-wrap items-center gap-2">
							<span class="rounded-bubble rounded-br-md bg-primary-strong px-4 py-2 text-lg text-white">{prompt}</span>
							<span class="text-xs font-semibold tracking-wider text-muted uppercase">UI generada · respuesta simulada</span>
						</div>
						{#if phase === 'thinking'}
							<div class="mt-4 grid gap-3 md:grid-cols-3" aria-label="Generando">
								{#each [0, 1, 2] as i (i)}<div class="h-40 animate-pulse rounded-card bg-cream"></div>{/each}
							</div>
						{:else}
							<p class="mt-4 max-w-3xl rounded-bubble rounded-bl-md border border-line bg-card px-4 py-3 text-lg leading-snug">
								{text}{#if phase === 'streaming' && cards.length === 0}<span class="ml-0.5 inline-block h-5 w-1.5 animate-pulse bg-primary-strong align-middle"></span>{/if}
							</p>
							{#if cards.length}
								<div class="mt-4 grid items-start gap-4 md:grid-cols-2 lg:grid-cols-3">
									{#each cards as c, i (i)}
										<div class={c.kind === 'alerta' ? 'md:col-span-2 lg:col-span-2' : ''} in:fly={{ y: 16, duration: 300 }}>
											<Card card={c} />
										</div>
									{/each}
								</div>
							{/if}
							{#if follow.length}
								<div class="mt-4 flex flex-wrap gap-2" in:fade>
									<span class="self-center text-sm font-semibold text-muted">También puedes:</span>
									{#each follow as f (f)}
										<button type="button" onclick={() => ask(f)} class="min-h-11 rounded-full border border-primary-strong px-4 py-2 font-semibold text-primary-strong hover:bg-cream">{f}</button>
									{/each}
								</div>
							{/if}
						{/if}
					</div>
				{/if}
			</div>
		</section>

		<!-- Cómo funciona -->
		<section id="como-funciona" class="scroll-mt-40 border-t border-line bg-card px-4 py-16 md:px-6">
			<div class="mx-auto max-w-6xl">
				<p class="text-sm font-semibold tracking-wider text-accent-strong uppercase">Cómo funciona</p>
				<h2 class="mt-2 text-3xl font-bold text-secondary md:text-4xl">Simple, rápido y a tu ritmo</h2>
				<ol class="mt-8 grid gap-4 md:grid-cols-3">
					{#each STEPS as s (s.n)}
						<li class="rounded-card border border-line bg-bg p-6">
							<span class="grid size-11 place-items-center rounded-full bg-primary text-xl font-bold text-ink">{s.n}</span>
							<h3 class="mt-4 text-xl font-bold">{s.t}</h3>
							<p class="mt-2 text-muted">{s.d}</p>
						</li>
					{/each}
				</ol>
			</div>
		</section>

		<!-- QR en farmacia → cupón -->
		<section id="qr" class="scroll-mt-40 px-4 py-16 md:px-6">
			<div class="mx-auto grid max-w-6xl items-center gap-10 md:grid-cols-2">
				<div>
					<p class="text-sm font-semibold tracking-wider text-accent-strong uppercase">En la farmacia</p>
					<h2 class="mt-2 text-3xl font-bold text-secondary md:text-4xl">Escanea el QR y llévate un cupón</h2>
					<ul class="mt-6 space-y-3 text-lg">
						<li class="flex gap-3"><span class="font-bold text-primary-strong">→</span>Escanea el QR en caja o en la vitrina.</li>
						<li class="flex gap-3"><span class="font-bold text-primary-strong">→</span>Ingresa solo tu cédula y acepta con un toque.</li>
						<li class="flex gap-3"><span class="font-bold text-primary-strong">→</span>Recibe tu cupón smart al instante y úsalo hoy o en tu próxima compra.</li>
					</ul>
					<button type="button" onclick={() => ask('Mis cupones SmartClub')} class="mt-6 rounded-full bg-primary-strong px-6 py-3 font-semibold text-white">Ver mis cupones</button>
				</div>
				<div class="mx-auto w-full max-w-md">
					<Cupon title="$2 de bienvenida" code="DEMO-QR-BIENV" until="Beneficio de ejemplo · lo define Farmaenlace" />
				</div>
			</div>
		</section>

		<!-- Marcas SmartClub (solo texto) -->
		<section id="smartclub" class="scroll-mt-40 border-t border-line bg-cream px-4 py-16 md:px-6">
			<div class="mx-auto max-w-6xl text-center">
				<p class="text-sm font-semibold tracking-wider text-accent-strong uppercase">Fidelización transversal</p>
				<h2 class="mt-2 text-3xl font-bold text-secondary md:text-4xl">Un solo cashback smart en todas las marcas</h2>
				<p class="mx-auto mt-3 max-w-2xl text-lg text-muted">Hasta 5% de cashback y beneficios en las marcas integradas a SmartClub. Tu farmacéutico virtual te avisa cuándo aprovecharlos.</p>
				<ul class="mt-8 flex flex-wrap justify-center gap-3">
					{#each BRANDS as b (b)}<li class="rounded-full border border-line bg-card px-5 py-2.5 text-lg font-semibold">{b}</li>{/each}
				</ul>
				<p class="mt-4 text-sm text-muted">Nombres solo como texto de referencia. Sin logos oficiales.</p>
			</div>
		</section>
	</main>

	<footer class="bg-ink px-4 py-10 text-white/80 md:px-6">
		<div class="mx-auto max-w-6xl space-y-2 text-sm">
			<p class="text-base font-bold text-white">Farmacéutico Virtual · Demo · datos simulados</p>
			<p><b class="text-white">No reemplaza la consulta médica.</b> No emite diagnósticos ni sugiere medicamentos con receta. Ante una emergencia llama al ECU 911.</p>
			<p>Prototipo de hackathon (Connect atVentures 2026). Todos los productos, precios, farmacias, cupones e historial son sintéticos. No afiliado ni respaldado por Farmaenlace, SmartClub ni las marcas mencionadas.</p>
		</div>
	</footer>
</div>
