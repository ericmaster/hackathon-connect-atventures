# Playwright E2E — Farmacéutico Virtual (chromium, 390x844, serial)

```bash
cd tests/playwright && npm install && npx playwright install chromium
npm run test:demo          # ?demo Plan B, no backend (~30 s)
npm run test:live          # real API: 1 LLM flow + red flag + mic/403 recovery (route-mocked, no LLM) (~45 s; Bedrock ≤1 RPS)
BASE_URL=http://localhost:4173 npm run test:demo   # vs `npx vite preview` of app/build
```
Console errors / failed requests / 5xx fail the test (allowlist in fixtures/console-guard.ts).
