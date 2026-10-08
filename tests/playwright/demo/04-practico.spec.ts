import { test, expect } from '../fixtures/console-guard';
import {
	openDemo,
	enterCedula,
	acceptConsent,
	sendText,
	waitIdle,
	latestSurface
} from '../helpers/flow';

test.describe('demo práctico persona', () => {
	test('1712456787 → one-card recommendation path', async ({ guardedPage: page }) => {
		await openDemo(page);
		await enterCedula(page, '1712456787');
		await acceptConsent(page);
		await sendText(page, 'algo para la gripe');

		const noAlergia = latestSurface(page).getByRole('button', { name: /no,?\s*ninguno/i });
		if (await noAlergia.isVisible().catch(() => false)) {
			await noAlergia.click();
			await waitIdle(page);
		}

		const surface = latestSurface(page);
		const addButtons = surface.getByRole('button', { name: /agregar/i });
		await expect(addButtons).toHaveCount(1);
		await expect(surface.getByText(/lo más rápido|opción más rápida/i).first()).toBeVisible();
	});
});
