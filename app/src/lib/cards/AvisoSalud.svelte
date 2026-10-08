<script lang="ts">
	let { text }: { text?: string } = $props();
</script>

<p class="flex gap-2 rounded-2xl border border-warning bg-cream p-3 text-sm" role="note">
	<span aria-hidden="true">ⓘ</span>
	<span>{text || 'Si persiste, consulta a un médico. No reemplaza la consulta con un profesional de salud.'}</span>
</p>
