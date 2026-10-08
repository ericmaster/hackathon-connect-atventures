<script lang="ts">
	import Node from './Node.svelte';
	import type { OnAction, Surface } from './types.js';
	let { surface, onAction }: { surface: Surface; onAction: OnAction } = $props();
</script>

{#if surface.comps.root}
	<div class="a2ui-surface" data-surface={surface.id}>
		<Node {surface} id="root" {onAction} />
	</div>
{/if}
