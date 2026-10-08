import { test, expect } from '../fixtures/console-guard';
import { waitIdle, latestSurface } from '../helpers/flow';

const MIC_MSG =
	/no tengo permiso.*micr[oó]fono|no pude usar el micr[oó]fono|habil[ií]talo|puedes escribir/i;

/**
 * ?demo uses fake voice (never calls getUserMedia). Patch the fake startListening
 * in the page bundle so the shell's catch path still runs — same UI as a real
 * NotAllowedError from voice/mic.ts.
 */
test.describe('demo mic denied', () => {
	test('denied mic shows Spanish error; text input still works', async ({ browser }) => {
		const context = await browser.newContext({
			viewport: { width: 390, height: 844 },
			isMobile: true,
			hasTouch: true,
			locale: 'es-EC'
			// no microphone permission granted
		});

		const page = await context.newPage();
		const failures: string[] = [];
		page.on('pageerror', (e) => {
			const t = String(e?.message ?? e);
			if (!/NotAllowedError|Permission denied|mic-denied/i.test(t)) failures.push(t);
		});

		await page.addInitScript(() => {
			const deny = () =>
				Promise.reject(
					Object.assign(new DOMException('Permission denied', 'NotAllowedError'), {
						name: 'NotAllowedError'
					})
				);
			try {
				Object.defineProperty(navigator, 'mediaDevices', {
					configurable: true,
					value: {
						getUserMedia: deny,
						enumerateDevices: async () => []
					}
				});
			} catch {
				/* ignore */
			}
		});

		await page.route('**/_app/immutable/nodes/*.js', async (route) => {
			const res = await route.fetch();
			let body = await res.text();
			if (body.includes('startListening') && body.includes('simulated:!0')) {
				body = body.replace(
					/startListening\(e,t\)\{/,
					`startListening(e,t){throw Object.assign(new Error('mic-denied'),{userMessage:'No tengo permiso para usar tu micrófono. Para hablarme, toca el candado junto a la dirección del navegador y permite el micrófono. Mientras tanto, puedes escribirme abajo.',code:'mic-denied'});`
				);
			}
			await route.fulfill({
				status: res.status(),
				headers: { ...res.headers(), 'cache-control': 'no-store' },
				body
			});
		});

		await page.goto('/?demo');
		await expect(page.getByRole('heading', { name: /farmacéutico virtual/i })).toBeVisible();
		await waitIdle(page);

		await page.getByRole('button', { name: /^hablar$/i }).click();
		await expect(page.getByRole('alert').filter({ hasText: MIC_MSG })).toBeVisible({ timeout: 15_000 });

		// Text input still works: enter valid cédula via chat field or form
		// (the error bubble is now the last entry, so target the cédula field directly)
		await page.getByRole('textbox', { name: /número de cédula/i }).fill('1710034065');
		await page.getByRole('button', { name: /^continuar$/i }).last().click();
		await waitIdle(page);
		await expect(latestSurface(page).getByText(/privacidad|historial|gracias/i).first()).toBeVisible();

		expect(failures, failures.join('\n')).toEqual([]);
		await context.close();
	});
});
