# Load test — live jury on phones (8 oct 2026, ~13:43–13:55 Bogotá)

Tool: `tests/load/judges.py` (new). Each virtual judge = own Cognito guest identity + SigV4 → API Gateway `znpzz1wg21` →
`connect-atv-orchestrator`. Flow: `/session` → `enviar_cedula` (1710034065, 1712456787, then fresh módulo-10 synthetic
cédulas → new profiles) → `consentimiento` → free text (`algo para la gripe` / `tengo tos` / `vitaminas para mi mamá`,
→ safety-question template) → `seguridad {ok:true}` (**the LLM turn**: GLiNER + Haiku 4.5) → `agregar_pedido` →
`retirar_aqui` → billing (consumidor final + email) → `confirmar_reserva` → confirmación. Think time 2–5 s, start spread 0–3 s.
`--tts` also fires `POST /voice/tts` after every response, like the PWA (doubles API Gateway requests).
CloudWatch (read-only `filter_log_events`) gives per-request `llm` trace + `ThrottlingException` count.
Results JSON: `tests/load/results/`. Re-run: `python3 tests/load/judges.py -n 5 --tts --retry429 2`.

## Results

LLM = `seguridad` turn (latency seen by the phone). Template = all other steps (ms). "Bedrock fail" = LLM failed → safe template.
"GLiNER kw" = a GLiNER call hit a cold container (4 s read timeout) → keyword NLU (response `mode:"simulado"`, still correct;
Haiku still ran). Throttle = `ThrottlingException` lines in the orchestrator log group.

| scenario | done | LLM p50/p95/max s | template p50/p95/max ms | Bedrock fail | GLiNER kw | 429 | 5xx | 403 | Throttle | reqs |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 judges | 3/3 | 5.3 / 6.6 / 6.7 | 375 / 761 / 4320* | 0 | 1 | 0 | 0 | 0 | 0 | 33 |
| 5 judges | 5/5 | 5.7 / 6.7 / 6.9 | 372 / 776 / 4384* | 0 | 1 | 0 | 0 | 0 | 0 | 55 |
| 8 judges | 8/8 | 7.4 / 8.3 / 8.4 | 343 / 794 / 861 | 0 | 0 | 0 | 0 | 0 | 0 | 88 |
| 5 judges + TTS | 5/5 | 5.4 / 5.9 / 6.0 | 370 / 770 / 824 | 0 | 0 | 0 | 0 | 0 | 0 | 110 |
| **8 burst + TTS** (spread 0, think 1–2 s) — before | **6/8** | 7.7 / 8.5 / 8.6 | 375 / 774 / 824 | 0 | 0 | **4** | 0 | 0 | 0 | 138 |
| 5 judges + TTS — after | 5/5 | 6.2 / 8.5 / 8.9 | 344 / 752 / 817 | 0 | 1 | 0 | 0 | 0 | 0 | 110 |
| 8 burst + TTS — after | **8/8** | 7.9 / 11.1 / 11.2 | 349 / 749 / 837 | 0 | 0 | **0** | 0 | 0 | 0 | 176 |

\* the `/turn` step whose GLiNER call hit a cold container (+4 s, keyword NLU). All other `/turn` ≤ 0.9 s.

Findings
- Bedrock: 0 failures, 0 retries, 0 `ThrottlingException`, 0 validation retries in all 40 LLM turns. The 1.1 s global slot
  queues turns: LLM latency grows ~0.3–0.6 s per simultaneous judge (5.3 s @3 → ~8 s @8, 11 s p95 when 8 arrive together).
  Budget math: queued turns fit the 25 s budget up to ~12 simultaneous LLM turns; beyond that → safe template (`simulado`).
- The only failures were API Gateway **429 on template steps** (`enviar_cedula`, `/voice/tts`) when 8 judges tapped together
  with TTS on (≈2 req per step) against the 5 rps / burst 10 stage throttle. The PWA had no 429 retry → error bubble.
- GLiNER: the keep-warm loop keeps ONE container warm; a 2nd simultaneous GLiNER call can land on a cold container → 4 s
  timeout → keyword NLU (correct intent, badge `simulado` for that response). Seen 1× in 3 of 7 runs.

## Changes made
1. API Gateway stage `$default` throttle 5 rps / burst 10 → **20 rps / burst 40** (`aws apigatewayv2 update-stage`;
   `infra/api/expose.sh` + CONTRACT.md updated). Bedrock spend still capped by the global 1.1 s slot (unchanged).
2. PWA (`app/`): `signedFetch` retries **429** twice (0.7 s, 1.6 s + jitter; 429 is rejected before the Lambda so it's
   side-effect free; 5xx not retried). Busy indicator after 8 s: "Pensando… Hay varias personas probando, un momento…"
   (1.5 s: "Pensando tu respuesta, un momento…" unchanged). `npm run check` 0 errors, build, `app/deploy.sh` (job 12 SUCCEED).
   Playwright: demo 9/9, live 7/7 + new `live/12-throttle-429.spec.ts` (two mocked 429s → transparent retry) 1/1.
3. No backend (Lambda) change: Bedrock lock / budget not touched (no fallbacks observed).

## Verdict
Acceptable for live jury use: ≤5 judges → LLM p95 ≤ 8.9 s, 0 errors, 0 Bedrock fallbacks; 8 simultaneous → 8/8, p95 11 s.
Recommended: **up to 8 judges at once** comfortable; ~12 is the soft limit (≈17–18 s waits, then safe-template fallback).
Optional before the jury tries it: warm several GLiNER containers with a one-shot parallel burst
(e.g. 4 × `tests/e2e/warm_gliner.sh 1` in parallel, ~1–2 min before) to avoid the occasional +4 s / `simulado` badge.
