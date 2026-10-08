import { test as base, expect, type Page, type ConsoleMessage, type Request, type Response } from '@playwright/test';

/** Paths/hosts we ignore for failed network (expected noise). */
const ALLOW_URL =
	/favicon|manifest\.webmanifest|apple-touch-icon|service-worker|\.map(\?|$)|fonts\.googleapis|fonts\.gstatic/i;

/** Console / pageerror messages that are expected in some specs. */
const ALLOW_CONSOLE =
	/favicon|AbortError|The play\(\) request was interrupted|NotAllowedError|Permission denied|mic-denied|NotSupportedError|service.?worker/i;

function sameOriginOrApi(url: string, pageUrl: string): boolean {
	try {
		const u = new URL(url);
		const p = new URL(pageUrl);
		if (u.origin === p.origin) return true;
		// Amplify PWA talks to API Gateway / Cognito
		if (/execute-api|cognito-identity|amazonaws\.com/i.test(u.hostname)) return true;
		return false;
	} catch {
		return false;
	}
}

type Guard = { failures: string[] };

async function attachGuard(page: Page, guard: Guard) {
	page.on('console', (msg: ConsoleMessage) => {
		if (msg.type() !== 'error') return;
		const text = msg.text();
		if (ALLOW_CONSOLE.test(text) || ALLOW_URL.test(text)) return;
		guard.failures.push(`console.error: ${text}`);
	});
	page.on('pageerror', (err) => {
		const text = String(err?.message ?? err);
		if (ALLOW_CONSOLE.test(text)) return;
		guard.failures.push(`pageerror: ${text}`);
	});
	page.on('requestfailed', (req: Request) => {
		const url = req.url();
		if (ALLOW_URL.test(url)) return;
		const failure = req.failure()?.errorText ?? '';
		// Aborted on navigation / intentional cancel is normal
		if (/NS_BINDING_ABORTED|net::ERR_ABORTED|AbortError|cancelled|canceled/i.test(failure)) return;
		if (!sameOriginOrApi(url, page.url())) return;
		guard.failures.push(`requestfailed: ${req.method()} ${url} (${failure})`);
	});
	page.on('response', (res: Response) => {
		if (res.status() < 500) return;
		const url = res.url();
		if (ALLOW_URL.test(url)) return;
		if (!sameOriginOrApi(url, page.url())) return;
		guard.failures.push(`http ${res.status()}: ${res.request().method()} ${url}`);
	});
}

export const test = base.extend<{ guardedPage: Page }>({
	guardedPage: async ({ page }, use, testInfo) => {
		const guard: Guard = { failures: [] };
		await attachGuard(page, guard);
		await use(page);
		if (guard.failures.length) {
			const detail = guard.failures.map((f) => `  - ${f}`).join('\n');
			expect(guard.failures, `Unexpected page faults in ${testInfo.title}:\n${detail}`).toEqual([]);
		}
	}
});

export { expect };
