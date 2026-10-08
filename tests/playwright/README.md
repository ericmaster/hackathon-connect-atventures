# Playwright E2E — Farmacéutico Virtual (chromium, 390x844, serial)

```bash
cd tests/playwright && npm install && npx playwright install chromium
npm run test:demo          # ?demo Plan B, no backend (~30 s)
npm run test:live          # real API, 1 full LLM flow + red flag (~30 s; Bedrock ≤1 RPS, never parallel w/ demo)
BASE_URL=http://localhost:4173 npm run test:demo   # vs `npx vite preview` of app/build
```
Console errors / failed requests / 5xx fail the test (allowlist in fixtures/console-guard.ts).
