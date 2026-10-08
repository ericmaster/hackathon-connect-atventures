import { test, expect } from '../fixtures/console-guard';
import { openDemo, enterCedula, latestSurface } from '../helpers/flow';

test.describe('demo invalid cédula', () => {
	test('3 invalid attempts → hand-off to human', async ({ guardedPage: page }) => {
		await openDemo(page);
		const bad = '1710034066';

		for (let i = 0; i < 3; i++) {
			await enterCedula(page, bad);
		}

		const surface = latestSurface(page);
		await expect(surface.getByText(/habla con un farmacéutico|farmacéutico humano/i).first()).toBeVisible({
			timeout: 60_000
		});
	});
});
