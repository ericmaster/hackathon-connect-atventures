import { test, expect } from '../fixtures/console-guard';
import {
	openDemo,
	enterCedula,
	acceptConsent,
	completeOrderFromConsulta,
	assertConfirmation,
	latestSurface,
	assertSimpleLanding
} from '../helpers/flow';

test.describe('demo full flow', () => {
	test('cédula → consent → gripe → pickup → billing → confirmation QR + SIMULADA', async ({
		guardedPage: page
	}) => {
		await openDemo(page);
		await assertSimpleLanding(page);
		await enterCedula(page, '1710034065');
		await expect(latestSurface(page).getByText(/privacidad|historial de compras/i).first()).toBeVisible();
		await acceptConsent(page);

		await completeOrderFromConsulta(page, 'algo para la gripe');
		await assertConfirmation(page);
		await expect(latestSurface(page).getByText(/SIMULADA/)).toBeVisible();
	});
});
