<script lang="ts">
	import type { Card } from './types.js';
	import ProductCard from './ProductCard.svelte';
	import PharmacyCard from './PharmacyCard.svelte';
	import SugerenciaPersonalizada from './SugerenciaPersonalizada.svelte';
	import ResumenPedido from './ResumenPedido.svelte';
	import Cupon from './Cupon.svelte';
	import AlertaRoja from './AlertaRoja.svelte';

	let { card }: { card: Card } = $props();
</script>

{#if card.kind === 'product'}<ProductCard {...card} />
{:else if card.kind === 'pharmacy'}<PharmacyCard {...card} />
{:else if card.kind === 'sugerencia'}<SugerenciaPersonalizada {...card} />
{:else if card.kind === 'resumen'}<ResumenPedido {...card} />
{:else if card.kind === 'cupon'}<Cupon {...card} />
{:else if card.kind === 'alerta'}<AlertaRoja {...card} />
{/if}
