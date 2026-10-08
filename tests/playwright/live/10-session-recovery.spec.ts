import { test, expect } from '@playwright/test';
import { openLive, enterCedula, latestSurface, waitIdle } from '../helpers/flow';

// No LLM turns: only /session and the deterministic cédula /action.
// Uses plain `page` (simulated 403s make Chrome log "Failed to load resource"), but still fails on pageerror.
const FORBIDDEN = { status: 403, contentType: 'application/json', body: '{"message":"Forbidden"}' };

test.describe('live session recovery', () => {
	test.beforeEach(({ page }) => {
		const errs: string[] = [];
		page.on('pageerror', (e) => errs.push(String(e)));
		test.info().annotations.push({ type: 'pageerrors', description: '' });
		(page as unknown as { _errs: string[] })._errs = errs;
	});
	test.afterEach(({ page }) => {
		expect((page as unknown as { _errs: string[] })._errs).toEqual([]);
	});

	test('403 on /action → fresh guest identity + new session, app keeps working', async ({ page }) => {
		await openLive(page);
		const before = await page.evaluate(() => localStorage.getItem('fv-identity'));
		let n = 0;
		await page.route('**/action', (route) => (n++ < 2 ? route.fulfill(FORBIDDEN) : route.fallback()));
		await enterCedula(page, '1710034065'); // 403 (signedFetch retries once → 403 again) → relogin
		await expect(page.getByText(/tu sesión expiró/i)).toBeVisible();
		await expect(page.getByText(/no pude conectar/i)).toHaveCount(0);
		await expect(latestSurface(page).getByText(/cédula/i).first()).toBeVisible();
		const after = await page.evaluate(() => localStorage.getItem('fv-identity'));
		expect(after).toBeTruthy();
		expect(after).not.toBe(before);
		await enterCedula(page, '1710034065'); // real request on the new session
		await expect(latestSurface(page).getByText(/privacidad|historial|consentimiento|autoriz/i).first()).toBeVisible();
	});

	test('Cognito GetId failure at start → one retry succeeds', async ({ page }) => {
		let failed = false;
		await page.route('https://cognito-identity.*.amazonaws.com/**', (route) => {
			const t = route.request().headers()['x-amz-target'] || '';
			if (!failed && t.endsWith('GetId')) {
				failed = true;
				return route.fulfill({ status: 400, contentType: 'application/json', body: '{"__type":"InternalErrorException"}' });
			}
			return route.fallback();
		});
		await openLive(page); // throws if "No pude conectar" shows
		expect(failed).toBe(true);
		await expect(page.getByText(/no pude conectar/i)).toHaveCount(0);
	});

	test('persistent 403 on /session → Reintentar / Usar modo simulado, simulado works', async ({ page }) => {
		await page.route('**/session', (route) => route.fulfill(FORBIDDEN));
		await page.goto('/');
		await expect(page.getByText(/no pude conectar/i)).toBeVisible({ timeout: 60_000 });
		await expect(page.getByRole('button', { name: /reintentar/i })).toBeVisible();
		await page.getByRole('button', { name: /usar modo simulado/i }).click();
		await waitIdle(page);
		await expect(page.getByTestId('mode-badge')).toHaveText(/simulados/i);
		await expect(latestSurface(page).getByText(/cédula/i).first()).toBeVisible();
	});
});
