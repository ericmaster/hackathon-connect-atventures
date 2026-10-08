import { test, expect } from '../fixtures/console-guard';
import { openDemo, enterCedula, acceptConsent, waitIdle } from '../helpers/flow';

// Fake clock makes the fake transport's 350 ms turn delay and fake-voice timers deterministic.
test.describe('demo mic while thinking', () => {
	test('mic disabled with hint while a request is pending', async ({ guardedPage: page }) => {
		await openDemo(page);
		await enterCedula(page, '1710034065');
		await acceptConsent(page);
		await page.clock.install();
		const mic = page.getByRole('button', { name: /^hablar$/i });
		await expect(mic).toBeEnabled();
		await page.getByRole('textbox', { name: /escribe tu pregunta/i }).fill('algo para la tos');
		await page.getByRole('button', { name: /^enviar$/i }).click();
		await expect(mic).toBeDisabled();
		await expect(page.getByText(/espera un momento/i)).toBeVisible();
		await page.clock.runFor(2000);
		await waitIdle(page);
		await expect(mic).toBeEnabled();
		await expect(page.getByText(/toca para hablar/i)).toBeVisible();
	});

	test('speech final that lands while thinking is queued, not dropped', async ({ guardedPage: page }) => {
		await openDemo(page);
		await enterCedula(page, '1710034065');
		await acceptConsent(page);
		await page.clock.install();
		await page.getByRole('button', { name: /^hablar$/i }).click(); // fake voice: 'algo para la gripe' final at 1600 ms
		await page.clock.runFor(1400);
		await page.getByRole('textbox', { name: /escribe tu pregunta/i }).fill('algo para la tos');
		await page.getByRole('button', { name: /^enviar$/i }).click(); // turn resolves at +350 ms
		await page.clock.runFor(250); // final arrives while busy → queued
		await expect(page.getByText('algo para la gripe', { exact: true })).toHaveCount(0);
		await page.clock.runFor(3000); // first turn ends → queued phrase sent → second turn ends
		await waitIdle(page);
		await expect(page.getByText('algo para la gripe', { exact: true })).toHaveCount(1);
	});
});
