import { test, expect } from '@playwright/test';
import { openLive, enterCedula, latestSurface } from '../helpers/flow';

// Load test (docs/LOAD-TEST.md): a burst of judges can hit the API Gateway stage throttle (429, rejected before the
// Lambda, so safe to retry). signedFetch retries 429 twice with backoff → the user never sees an error.
// No LLM turns: only /session and the deterministic cédula /turn. Plain `page` (mocked 429s log "Failed to load resource").
const THROTTLED = { status: 429, contentType: 'application/json', body: '{"message":"Too Many Requests"}' };

test('two 429s on /turn → transparent retry, consent surface, no error bubble', async ({ page }) => {
	const errs: string[] = [];
	page.on('pageerror', (e) => errs.push(String(e)));
	await openLive(page);
	let n = 0;
	await page.route('**/turn', (route) => (n++ < 2 ? route.fulfill(THROTTLED) : route.fallback()));
	await enterCedula(page, '1710034065');
	await expect(latestSurface(page).getByText(/privacidad|historial|consentimiento|autoriz/i).first()).toBeVisible();
	expect(n).toBe(3);
	await expect(page.locator('[role="alert"]')).toHaveCount(0);
	expect(errs).toEqual([]);
});
