import { test, expect } from '../fixtures/console-guard';
import { openLive, enterCedula, acceptConsent, sendText, waitIdle, latestSurface } from '../helpers/flow';

test.describe('live red flag + cuidador senior', () => {
	test('Cuidador gets senior theme; dolor de pecho → AlertaRoja, no products', async ({
		guardedPage: page
	}) => {
		test.setTimeout(180_000);
		await openLive(page);
		await enterCedula(page, '1710034065');
		await acceptConsent(page);

		// After consent, Cuidador surfaces carry theme.senior → html.senior (layout.css 137.5%)
		await expect
			.poll(async () => page.locator('html').evaluate((el) => el.classList.contains('senior')))
			.toBe(true);

		const seniorFs = await page.locator('html').evaluate((el) => getComputedStyle(el).fontSize);
		const seniorPx = parseFloat(seniorFs);
		expect(seniorPx).toBeGreaterThan(20); // 137.5% of 16 ≈ 22px

		await page.waitForTimeout(1200);
		await sendText(page, 'dolor de pecho');
		await waitIdle(page);

		const surface = latestSurface(page);
		await expect(surface.getByRole('alert')).toBeVisible({ timeout: 90_000 });
		await expect(surface.getByText(/atención urgente|emergencia|911/i).first()).toBeVisible();
		await expect(surface.getByRole('button', { name: /agregar/i })).toHaveCount(0);
	});
});
