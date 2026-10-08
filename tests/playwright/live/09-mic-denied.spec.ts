import { test, expect } from '../fixtures/console-guard';
import { openLive, enterCedula, latestSurface } from '../helpers/flow';

// Real voice module (http transport) with getUserMedia denied. No LLM turn (cédula is deterministic).
test.describe('live mic denied', () => {
	test('real voice: NotAllowedError → Spanish message; text still works', async ({ guardedPage: page }) => {
		await page.addInitScript(() => {
			const md = navigator.mediaDevices;
			if (md) md.getUserMedia = () => Promise.reject(new DOMException('Permission denied', 'NotAllowedError'));
		});
		await openLive(page);
		await expect(page.getByText(/voz simulada/i)).toHaveCount(0); // real voice loaded
		await page.getByRole('button', { name: /^hablar$/i }).click();
		await expect(page.getByRole('alert').filter({ hasText: /permiso para usar tu micr[oó]fono/i })).toBeVisible({ timeout: 15_000 });
		await expect(page.getByRole('button', { name: /^hablar$/i })).toBeVisible(); // not stuck listening
		await page.getByRole('textbox', { name: /c[eé]dula/i }).fill('1710034065');
		await page.getByRole('button', { name: /^continuar$/i }).last().click();
		await expect(latestSurface(page).getByText(/privacidad|historial|consentimiento|autoriz/i).first()).toBeVisible();
	});
});
