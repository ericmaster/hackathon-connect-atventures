// Records the main demo at human pace. REAL=1 → live API (no ?demo). Synthetic data only.
import { test, expect, type Page } from '@playwright/test';
import { latestSurface, waitIdle } from '../helpers/flow';

const REAL = !!process.env.REAL;
const beat = (page: Page, ms = 1200) => page.waitForTimeout(ms);

async function tap(page: Page, name: RegExp) {
	const b = latestSurface(page).getByRole('button', { name }).first();
	await expect(b).toBeVisible();
	await b.click();
	await waitIdle(page);
	await beat(page);
}

async function say(page: Page, text: string) {
	const box = page.getByRole('textbox', { name: /escribe tu pregunta/i });
	await box.click();
	await box.pressSequentially(text, { delay: 35 });
	await page.getByRole('button', { name: /^enviar$/i }).click();
	await waitIdle(page);
	await beat(page);
}

async function cedula(page: Page) {
	await expect(latestSurface(page).getByText(/cédula/i).first()).toBeVisible();
	await latestSurface(page).locator('input').first().pressSequentially('1710034065', { delay: 40 });
	await beat(page, 500);
	await tap(page, /^continuar$/i);
}

test('demo video', async ({ page }) => {
	await page.goto(REAL ? '/' : '/?demo');
	await waitIdle(page);
	await beat(page);

	// Cuidador → consentimiento → reposición + "¿Por qué…?"
	await cedula(page);
	await latestSurface(page).locator('input[type="checkbox"]').first().check();
	await beat(page, 600);
	await tap(page, /^continuar$/i);
	await tap(page, /por qué me sugieres esto/i);

	// Consulta → pregunta de seguridad → agregar → retirar → resumen con cupón
	await say(page, 'algo para la gripe');
	const no = latestSurface(page).getByRole('button', { name: /no,?\s*ninguno/i });
	if (await no.isVisible().catch(() => false)) await tap(page, /no,?\s*ninguno/i);
	await tap(page, /agregar( al pedido| y retirar)?/i);
	const retirar = latestSurface(page).getByRole('button', { name: /retirar aquí/i }).first();
	if (await retirar.isVisible().catch(() => false)) await tap(page, /retirar aquí/i);
	await expect(latestSurface(page).getByText(/cup[oó]n/i).first()).toBeVisible();
	await beat(page, 600);
	await tap(page, /continuar|confirmar (pedido|reserva)/i);

	// Facturación: consumidor final + email → confirmar
	const cf = latestSurface(page).getByRole('button', { name: /consumidor final/i });
	if (await cf.isVisible().catch(() => false)) await tap(page, /consumidor final/i);
	const email = latestSurface(page).locator('input').first();
	if (await email.isVisible().catch(() => false)) {
		await email.pressSequentially('demo@example.com', { delay: 30 });
		await tap(page, /^continuar$/i);
	}
	const conf = latestSurface(page).getByRole('button', { name: /confirmar (y )?reserva/i });
	if (await conf.isVisible().catch(() => false)) await tap(page, /confirmar (y )?reserva/i);
	await expect(latestSurface(page).getByText(/SIMULADA/).first()).toBeVisible();
	await beat(page, 1800);

	// Reiniciar → señal de alarma
	await page.getByTestId('reset').click();
	await waitIdle(page);
	await beat(page, 800);
	await cedula(page);
	await latestSurface(page).locator('input[type="checkbox"]').first().check();
	await tap(page, /^continuar$/i);
	await say(page, 'dolor de pecho');
	await expect(latestSurface(page).getByRole('alert')).toBeVisible();
	await beat(page, 2000);
});
