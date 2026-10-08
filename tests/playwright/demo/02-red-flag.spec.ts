import { test, expect } from '../fixtures/console-guard';
import { openDemo, enterCedula, acceptConsent, sendText, latestSurface } from '../helpers/flow';

test.describe('demo red flag', () => {
	test('dolor de pecho → AlertaRoja, no product cards', async ({ guardedPage: page }) => {
		await openDemo(page);
		await enterCedula(page, '1710034065');
		await acceptConsent(page);
		await sendText(page, 'dolor de pecho');

		const surface = latestSurface(page);
		await expect(surface.getByRole('alert')).toBeVisible();
		await expect(surface.getByText(/atención urgente|emergencia|911/i).first()).toBeVisible();
		await expect(surface.getByRole('button', { name: /agregar/i })).toHaveCount(0);
		await expect(surface.getByText(/venta libre/i)).toHaveCount(0);
	});
});
