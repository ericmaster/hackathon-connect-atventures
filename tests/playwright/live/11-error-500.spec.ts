import { test, expect } from '@playwright/test';
import { openLive, enterCedula, latestSurface } from '../helpers/flow';

// Review O-P1-3: a 500 body with `messages: []` / `revision: null` must not wipe revision/state.
// No LLM turns: /session + deterministic cédula /turn. Plain `page` (the mocked 500 logs "Failed to load resource").
test('500 with empty messages → retry message, current card stays, next tap works', async ({ page }) => {
	const errs: string[] = [];
	page.on('pageerror', (e) => errs.push(String(e)));
	await openLive(page);
	let n = 0;
	await page.route('**/turn', (route) =>
		n++ === 0
			? route.fulfill({
					status: 500,
					contentType: 'application/json',
					body: JSON.stringify({ sessionId: null, state: null, revision: null, messages: [], spokenText: '', mode: 'simulado', error: { code: 'internal', message: 'X' } })
				})
			: route.fallback()
	);
	await enterCedula(page, '1710034065'); // mocked 500
	await expect(page.getByText(/no pude responder/i)).toBeVisible();
	// the error line is now the last entry; the cédula prompt above it must still be live (not inert)
	const card = page.locator('main [data-entry]:not([inert])').filter({ hasText: /cédula/i }).last();
	await expect(card).toBeVisible();
	await enterCedula(page, '1710034065'); // real request, preserved revision/state → no 409
	await expect(latestSurface(page).getByText(/privacidad|historial|consentimiento|autoriz/i).first()).toBeVisible();
	await expect(page.getByText(/ya no está vigente/i)).toHaveCount(0);
	expect(errs).toEqual([]);
});
