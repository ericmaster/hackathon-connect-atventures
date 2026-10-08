<script lang="ts">
	import FakeQr from './FakeQr.svelte';
	let { orderNumber, pharmacy, pickupTime, qrValue }: { orderNumber: string; pharmacy?: string; pickupTime?: string; qrValue?: string } = $props();
</script>

<article class="rounded-card border-2 border-success bg-card p-4 shadow-card">
	<p class="text-xs font-semibold tracking-wider text-success-strong uppercase">Reserva confirmada</p>
	<div class="mt-1 flex items-center gap-3">
		<div class="flex-1">
			<p class="text-2xl font-bold">N.º {orderNumber}</p>
			{#if pharmacy}<p class="mt-1">Retira en <b>{pharmacy}</b></p>{/if}
			{#if pickupTime}<p class="text-muted">{pickupTime}</p>{/if}
			<p class="mt-2 text-sm font-semibold">Pagas al retirar. Muestra este QR.</p>
		</div>
		<FakeQr value={qrValue ?? orderNumber} size="size-[112px]" />
	</div>
</article>
