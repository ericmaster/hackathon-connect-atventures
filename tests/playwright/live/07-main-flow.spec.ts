import { test, expect } from '../fixtures/console-guard';
import {
	openLive,
	enterCedula,
	acceptConsent,
	completeOrderFromConsulta,
	assertConfirmation,
	latestSurface
} from '../helpers/flow';

test.describe('live main flow', () => {
	test('structural: products → resumen → confirmation/QR (LLM wording tolerant)', async ({
		guardedPage: page
	}) => {
		test.setTimeout(180_000);
		await openLive(page);
		await enterCedula(page, '1710034065');
		await acceptConsent(page);

		// Brief pause to respect Bedrock 1 RPS
		await page.waitForTimeout(1200);
		await completeOrderFromConsulta(page, 'algo para la gripe');

		const surface = latestSurface(page);
		await assertConfirmation(page);
		await expect(surface.getByText(/SIMULADA|simulada/i).first()).toBeVisible();
	});
});
