# opencode review (independent, read-only) — verified

- Reviewer: opencode `openai/gpt-6.1-sol#medium`, agent `plan` (read-only), scope `git diff fb48c98..b0100c8` (app/, services/api/, infra/api/, tests/) vs SPEC §7–§10 + CONTRACT.md. Ran Oct 8 ~13:23–13:29 (Bogotá).
- opencode ran only local commands: git diff/grep, offline unittests (18 API + 17 admin/voice PASS), in-memory repros. No AWS calls (boto3 only to print its retry config, fake creds). No files changed.
- Then I checked every P0/P1 claim against the code. Verdict = real / partly real / false; sev = my severity for the demo.

## P0 claims (opencode)

| # | Claim | Verdict | Note |
|---|---|---|---|
| O-P0-1 | `fsm.py:181-272` red flag doesn't stick: after "dolor de pecho", the next free turn shows ProductCards again | **REAL → P1** | `free_turn` never reads `s["blocked"]` (checkout intent goes to resumen/farmacias too). Commerce is still blocked: `fsm.py:377` returns 409 `blocked_red_flag`, so nothing gets sold, but a judge would see "Agregar" right after an ECU 911 alert. Fix: in `free_turn`, after the handoff/diagnosis checks, add `if s.get("blocked"): return red_flag(s, mode)` (or a handoff). The race where a lost revision save leaves `blocked=False` (`fsm.py:62`) is real but rare (the client sends one request at a time) → P2. |
| O-P0-2 | No allergy/other-medication safety question before suggesting products (`fsm.py:227`, `:266`) | **PARTLY REAL → P1 (spec gap, not a bug)** | No safety state in the backend, and the system prompt never asks about allergies. SPEC §7.2.2 and PLAN.md:13/36 expect it; §8 lists it as a "Propuesta". Plan B (`fake.ts` `safety()`/`safetyOk`) does ask, so live and `?demo` behave differently. Not demo-breaking; just don't promise it in the pitch, or add the question to the template. |
| O-P0-3 | Plan B: typing "multivitamínico"/"lo de siempre" adds to the cart with no A2UI action; `agregar_pedido`/`reservar` skip `confirm` (`fake.ts:459`, `:478-480`) | **REAL → P2** | Only in `?demo` (the fake transport). Same issue as Cursor P2-1, still not fixed. Reserving still needs `confirmar_reserva` with `confirm`. Becomes P1 only if Plan B is used live. |

## P1 claims (opencode)

| # | Claim | Verdict | Note |
|---|---|---|---|
| O-P1-1 | Anyone can get guest creds, spend AWS money and read `/admin/*` (`expose.sh:75`, `admin.py:104`, `deploy.sh:63`) | **REAL (by design) → P2 for demo** | Guest policy = `execute-api:Invoke` on `$default/*`. `allowed()` returns True when `FV_ADMIN_IDENTITIES` is unset, and deploy doesn't set it. Spend is capped by the stage throttle (5 rps / 10 burst) and the global Bedrock slot. Conditions are hidden on admin by default. What's exposed: billing name/ID/email typed in during the demo. Fix after the demo, or set `FV_ADMIN_IDENTITIES`. |
| O-P1-2 | Bedrock limiter: botocore `max_attempts:1` = 2 tries; the hidden retry takes no slot; `reserve_slot` gives up after 20 conflicts (`llm.py:36`, `store.py:186`) | **REAL → P1 (1-line fix)** | Checked: the client resolves to `{'mode':'standard','total_max_attempts':2}`, and standard mode retries ReadTimeout/5xx/throttling. If Bedrock hangs: 15 s + backoff + 15 s is more than the 29 s Lambda/APIGW limit → 503/504 and a generic error in the PWA (fails closed, but a ~29 s hang on stage). Same risk when a 15 s first try triggers the validation retry (`fsm.py:244` only needs 6 s left). Fix: `retries={"total_max_attempts":1,"mode":"standard"}` and `read_timeout≈10`. The `reserve_slot` fallback is real, but 20 straight conflicts won't happen with one user → P2. |
| O-P1-3 | Error responses wreck the UI: 4xx surfaces reuse the current surface id; a 500 returns `revision:null` and the shell takes it (`handler.py:108,117`, `http.ts:22`, `+page.svelte:94`) | **REAL → P1 (500 part) / P2 (4xx part)** | `T.stale`/`T.message(s["revision"])` reuse id `fv-{rev}` → `createSurface` overwrites the card on screen (e.g. confirmation QR/invoice after a duplicate tap). The client's `busy` flag + `inert` make that rare. 500 path: body `{messages:[], sessionId}` → `[]` is truthy, so http.ts accepts it and `handle()` sets `revision=null`/`state=null`/`mode=simulado`. The next tap gets 409, which replaces the surface with a plain message. Fix: in `handle()`, `if (res.revision != null) revision = res.revision` (same for state), or in http.ts require `typeof data.revision === 'number'`. Optional: error surfaces use id `fv-{rev}-e`. `qty:"abc"` → 500 is real, but the UI never sends qty. |
| O-P1-4 | A second identical cart can't be ordered: the idempotency key is only (session, cart, pharmacy) (`mock.py:230-245`, `fsm.py:359`) | **REAL → P2** | The same cart + pharmacy in the same session returns the old order, `created=False`. The session reloads with the cart still full, state `facturacion`, old confirmation shown. Reiniciar (`reset_sandbox` drops IDEM#) or a new session avoids it. Fix: add `s.get("lastOrder")` to `idem_key`. |

## P2 (opencode)
- `FakeQr.svelte` pickup QR is decorative and can't be scanned. Real; the comment says so. Label it "simulado" or don't let anyone scan it.

## Extra (mine, P2)
- A red flag during `cedula` moves to `consulta` with no cédula; `enviar_cedula` isn't allowed in `consulta` → stuck until Reiniciar (intended per CONTRACT "blocked until reset").
- `validate.py` only overrides actions on `ProductCard`. An LLM `Button`/`SugerenciaPersonalizada` can carry any action + `confirm:true` (the user still has to tap it, and the server still checks Rx/blocked/state).

## Verified OK (spot-checked)
- Rx: `validate.py` rejects Rx/out-of-context SKUs; `fsm.py:392` Rx goes to handoff on add; `guardrails.otc_only`; the server sets ProductCard price/`ventaLibre`/action.
- Conditions: `mock.public_customer` never includes `condiciones_probables`; LLM ctx uses `public_customer` and drops the `cedula` entity; `personalized_filter` only runs with consent; admin redacts by default; logs record route/state/intent/trace, not the user's text.
- Confirmation: `NEEDS_CONFIRM` needs `confirm is True` (`fsm.py:379`); `COMMERCE` blocked after a red flag (`:377`); revision check (`:373`); state allowlist per action.
- Idempotency of the same checkout: one DynamoDB transaction (IDEM/ORD/FAC not_exists + coupon status + session rev); a conflict returns the previous result.
- IAM: every route is AWS_IAM; CORS limited to the 2 Amplify origins + localhost; the guest role is trusted for this pool + unauthenticated only and can only call execute-api; Lambda role is minimal (table, gliner, Bedrock profile, Polly, Transcribe, own logs); `/internal/*` only works for `caller=="direct"`.
- Secrets: no AKIA/ASIA/private keys found in tracked HEAD (scoped grep).
- Bedrock: app throttle retries are capped (2) and checked against the deadline; the slot lock is a conditional DDB write (no mutex held); fails closed to the `T.products`/message template.
- Earlier Cursor fixes are in: request generation (`+page.svelte:110-122`), queued voice, 403/not_found → new identity + session, `clients.claim()`, deploy `.env`.

## Status (fixes Oct 8 ~13:30–13:45 Bogotá, workstream A)
- O-P0-1 **FIXED**: `free_turn` returns the fixed AlertaRoja when `s["blocked"]` (after handoff/diagnosis checks). Offline test `test_red_flag_sticks_on_next_free_turn`; live smoke step "free turn after red flag" → AlertaRoja.
- O-P0-2 **FIXED (template, no extra LLM call)**: one safety question per session before the first product suggestion ("¿Tienes alergia a algún medicamento o estás tomando otro?", buttons `seguridad {ok}` "No, ninguno"/"Sí", or free-text answer). Any answer continues with the pending query; the answer lives in the session only; "sí" adds a pharmacist note to each ProductCard and drops products the user named; the LLM gets only a boolean flag, never the user's words or a condition. Matches the `?demo` labels. CONTRACT.md updated; e2e smoke and Playwright helper answer it.
- O-P1-2 **FIXED**: Bedrock and GLiNER clients use `retries={"total_max_attempts":1,"mode":"standard"}`; Bedrock `read_timeout=10`; an LLM attempt (incl. the validation retry and throttle retry) only starts with ≥11 s left of the 25 s budget → fail closed to the template, well under 29 s.
- O-P1-3 **FIXED (500 part)**: `app/src/lib/api/http.ts` only accepts bodies with a numeric `revision` (non-2xx also need a non-empty surface), otherwise throws → shell shows "Uy, no pude responder…"; `+page.svelte handle()` never overwrites revision/state/mode/sessionId with null. Playwright `live/11-error-500.spec.ts` (mocked 500, then real tap succeeds without 409). 4xx surface-id reuse: still open (P2).
- O-P1-4 **FIXED**: idempotency key includes `lastOrder`; test `test_same_cart_can_be_ordered_again`.
- Verified: offline 22/22, `smoke.py --local handler` 12/12, live `tests/e2e/smoke.py` 12/12, `services/api/smoke.py` ALL OK, `npm run check` 0 errors, build + Amplify deploy OK, Playwright demo 9/9 + live 7/7. Lambda env still has `FV_TRANSCRIBE_VOCABULARY=connect-atv-meds` after deploy.
- Still open: O-P0-3 (Plan B only), O-P1-1 (admin open to guests unless `FV_ADMIN_IDENTITIES` set), FakeQr, extra P2s.

