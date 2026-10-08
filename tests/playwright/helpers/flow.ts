import { expect, type Page, type Locator } from '@playwright/test';

/** Latest (non-stale) surface: not inert / opacity-60. */
export function latestSurface(page: Page): Locator {
	return page.locator('main [data-entry]:not([inert])').last();
}

export async function waitIdle(page: Page) {
	await expect(page.getByTestId('busy')).toHaveCount(0, { timeout: 120_000 });
}

export async function openDemo(page: Page) {
	await page.goto('/?demo');
	await expect(page.getByRole('heading', { name: /farmacéutico virtual/i })).toBeVisible();
	await waitIdle(page);
	await expect(latestSurface(page).getByText(/cédula/i).first()).toBeVisible({ timeout: 60_000 });
}

export async function openLive(page: Page) {
	await page.goto('/');
	await expect(page.getByRole('heading', { name: /farmacéutico virtual/i })).toBeVisible();
	// Live may show start error; prefer real API
	const startErr = page.getByText(/no pude conectar/i);
	if (await startErr.isVisible().catch(() => false)) {
		throw new Error('Live API failed to start session');
	}
	await waitIdle(page);
	await expect(latestSurface(page).getByText(/cédula/i).first()).toBeVisible({ timeout: 60_000 });
}

export async function enterCedula(page: Page, cedula: string) {
	const surface = latestSurface(page);
	const input = surface.locator('input').first();
	await input.fill(cedula);
	await surface.getByRole('button', { name: /^continuar$/i }).click();
	await waitIdle(page);
}

export async function acceptConsent(page: Page) {
	const surface = latestSurface(page);
	const checkbox = surface.locator('input[type="checkbox"]').first();
	await checkbox.check();
	await surface.getByRole('button', { name: /^continuar$/i }).click();
	await waitIdle(page);
}

export async function sendText(page: Page, text: string) {
	const box = page.getByRole('textbox', { name: /escribe tu pregunta/i });
	await box.fill(text);
	await page.getByRole('button', { name: /^enviar$/i }).click();
	await waitIdle(page);
}

export async function clickInLatest(page: Page, name: RegExp | string) {
	await latestSurface(page).getByRole('button', { name }).click();
	await waitIdle(page);
}

/** Full happy path from consulta through confirmation (after consent). */
export async function completeOrderFromConsulta(page: Page, query = 'algo para la gripe') {
	await sendText(page, query);

	// Safety question (demo / live templates)
	const noAlergia = latestSurface(page).getByRole('button', { name: /no,?\s*ninguno/i });
	if (await noAlergia.isVisible().catch(() => false)) {
		await noAlergia.click();
		await waitIdle(page);
	}

	// Add product — práctico uses "Agregar y retirar…"; others "Agregar al pedido"
	const add = latestSurface(page)
		.getByRole('button', { name: /agregar( al pedido| y retirar)?/i })
		.first();
	await expect(add).toBeVisible({ timeout: 60_000 });
	await add.click();
	await waitIdle(page);

	// Pharmacy pickup (skipped on práctico one-tap path that jumps to resumen)
	const retirar = latestSurface(page).getByRole('button', { name: /retirar aquí/i }).first();
	if (await retirar.isVisible().catch(() => false)) {
		await retirar.click();
		await waitIdle(page);
	}

	// Resumen: cupón + continuar / confirmar
	const resumen = latestSurface(page);
	await expect(resumen.getByText(/tu pedido|total/i).first()).toBeVisible();
	await expect(resumen.getByText(/cup[oó]n/i).first()).toBeVisible();
	const cont = resumen.getByRole('button', { name: /continuar|confirmar (pedido|reserva)/i }).first();
	await cont.click();
	await waitIdle(page);

	// Billing: consumidor final + email (or email only if tipo already chosen)
	const surface = latestSurface(page);
	const cf = surface.getByRole('button', { name: /consumidor final/i });
	if (await cf.isVisible().catch(() => false)) {
		await cf.click();
		await waitIdle(page);
	}

	const emailField = latestSurface(page).locator('input').first();
	if (await emailField.isVisible().catch(() => false)) {
		await emailField.fill('demo@example.com');
		await latestSurface(page).getByRole('button', { name: /^continuar$/i }).click();
		await waitIdle(page);
	}

	const confirmar = latestSurface(page).getByRole('button', { name: /confirmar (y )?reserva/i });
	if (await confirmar.isVisible().catch(() => false)) {
		await confirmar.click();
		await waitIdle(page);
	}
}

export async function assertConfirmation(page: Page) {
	const surface = latestSurface(page);
	await expect(surface.getByText(/reserva confirmada|reserva lista/i).first()).toBeVisible();
	await expect(surface.getByRole('img', { name: /c[oó]digo qr|qr/i }).first()).toBeVisible();
	await expect(surface.getByText(/simulada/i).first()).toBeVisible();
	await expect(surface.getByText(/factura/i).first()).toBeVisible();
}
