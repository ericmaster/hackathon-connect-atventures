// Backup demo video (NOT part of the normal suite): npm run record (?demo) | npm run record:real (live API, 1 run).
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
	testDir: './record',
	workers: 1,
	retries: 0,
	timeout: 180_000,
	expect: { timeout: 60_000 },
	reporter: 'list',
	outputDir: 'test-results-record',
	use: {
		baseURL: process.env.BASE_URL ?? 'https://main.d2bloxc35rzfqy.amplifyapp.com',
		...devices['Pixel 7'],
		browserName: 'chromium',
		viewport: { width: 390, height: 844 },
		isMobile: true,
		hasTouch: true,
		locale: 'es-EC',
		video: { mode: 'on', size: { width: 390, height: 844 } }
	}
});
