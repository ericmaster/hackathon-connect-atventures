import { test, expect } from '../fixtures/console-guard';
import { openDemo, enterCedula, acceptConsent, sendText, waitIdle, latestSurface } from '../helpers/flow';

test.describe('demo reiniciar', () => {
	test('Reiniciar demo clears chat state back to start', async ({ guardedPage: page }) => {
		await openDemo(page);
		await enterCedula(page, '1710034065');
		await acceptConsent(page);
		await sendText(page, 'algo para la gripe');

		await expect(page.getByText(/algo para la gripe/i).first()).toBeVisible();

		await page.getByTestId('reset').click();
		await waitIdle(page);

		await expect(latestSurface(page).getByText(/cédula/i).first()).toBeVisible();
		await expect(page.getByText(/algo para la gripe/i)).toHaveCount(0);
		await expect(page.getByRole('button', { name: /agregar/i })).toHaveCount(0);
		await expect(page.getByRole('alert')).toHaveCount(0);
	});

	test('Reiniciar mid-request discards the stale response', async ({ guardedPage: page }) => {
		await openDemo(page);
		await enterCedula(page, '1710034065');
		await acceptConsent(page);
		const box = page.getByRole('textbox', { name: /escribe tu pregunta/i });
		await box.fill('algo para la gripe');
		await page.getByRole('button', { name: /^enviar$/i }).click();
		await page.getByTestId('reset').click(); // while the turn is still pending
		await waitIdle(page);
		await page.waitForTimeout(1500); // let the stale fake turn resolve
		await expect(latestSurface(page).getByText(/cédula/i).first()).toBeVisible();
		await expect(page.getByText(/algo para la gripe/i)).toHaveCount(0);
		await expect(page.getByRole('button', { name: /agregar/i })).toHaveCount(0);
		// app still usable after reset
		await enterCedula(page, '1712456787');
		await expect(page.getByRole('alert')).toHaveCount(0);
	});
});
