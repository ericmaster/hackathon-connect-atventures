import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.BASE_URL ?? 'https://main.d2bloxc35rzfqy.amplifyapp.com';

export default defineConfig({
	testDir: '.',
	fullyParallel: false,
	workers: 1,
	retries: 1,
	timeout: 180_000,
	expect: { timeout: 30_000 },
	reporter: [['list'], ['html', { open: 'never' }]],
	use: {
		baseURL,
		...devices['Pixel 7'],
		browserName: 'chromium',
		viewport: { width: 390, height: 844 },
		isMobile: true,
		hasTouch: true,
		trace: 'on-first-retry',
		locale: 'es-EC'
	},
	projects: [
		{ name: 'demo', testMatch: /demo\/.*\.spec\.ts/ },
		{ name: 'live', testMatch: /live\/.*\.spec\.ts/ }
	]
});
