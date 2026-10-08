# Cursor review (demo readiness)

## P0 (breaks demo)

- [P0-1] `app/deploy.sh:10` — `npm run build` no carga `app/.env`; sin `VITE_FV_API_URL` + `VITE_FV_TRANSPORT=http` embebidos, `pickTransport()` cae en fake aunque la URL sea Amplify — exportar env antes del build o `set -a && source .env && set +a`.
- [P0-2] `app/src/lib/api/index.ts:10-13` — con bundle sin `API_URL`, `?transport=http` no activa HTTP (`want === 'http' && API_URL` falla) — mismo fix de build; en vivo usar `?demo` solo como Plan B consciente.
- [P0-3] `app/src/lib/api/fake.ts:524-525` — `turn`/`action` ignoran `AbortSignal` y usan `delay()`; tras **Reiniciar**, un turno fake pendiente sigue y `+page.svelte` `handle()` repinta chat/`sessionId` obsoleto — token de generación en el shell o cancelar delays + ignorar respuestas stale.

## P1

- [P1-1] `app/src/routes/+page.svelte:100-106` + `stt.ts:165` — `onFinal` → `send()` sale si `busy`; voz durante turno LLM largo pierde la frase — encolar último final o reintentar al bajar `busy`.
- [P1-2] `app/src/routes/+page.svelte:68-82` — `handle()` sin id de petición; carrera rara post-`abort()` en HTTP podría aplicar JSON viejo — incrementar `reqGen` en `call`/`reset` y descartar si no coincide.
- [P1-3] `app/src/lib/api/auth.ts:77-79` — retry 403 solo limpia creds, no `identityId`; 403 `forbidden` de sesión no se recupera — `clearAuth()` + nuevo `/session` o mensaje que pida borrar `fv-identity`.
- [P1-4] `app/src/lib/api/http.ts:18-20` — 403 con cuerpo sin `messages` lanza `Error` genérico (p. ej. sesión de otra identidad) — mapear `error.code === 'forbidden'` a copy accionable.
- [P1-5] `app/src/service-worker/index.ts:15-18` — `activate` no llama `clients.claim()`; tras deploy manual, pestañas abiertas pueden seguir JS viejo hasta recarga — hard refresh antes del pitch o añadir `claim()`.

## P2

- [P2-1] `app/src/lib/api/fake.ts:478-479` — `agregar_pedido` no exige `context.confirm === true` (el backend sí) — alinear fake con `NEEDS_CONFIRM` por paridad de demo offline.
- [P2-2] `app/src/lib/a2ui/Node.svelte:63-69` — `surfaceValid()` valida todos los `TextField` de la surface en cualquier botón — superficies multi-campo futuras pueden bloquear acciones — validar solo ancestros o el campo del botón.
- [P2-3] `app/src/lib/a2ui/checks.ts:65-66` — checks desconocidos devuelven `true` — no defiende contra plantillas LLM con `call` raro — solo server-side hoy.
- [P2-4] `services/api/handler.py:131` — respuestas Lambda sin cabeceras CORS (dependen de API Gateway) — verificar `infra/api/expose.sh` en el stage desplegado; OPTIONS ya probado en `infra/api/test_guest.py`.
- [P2-5] `app/src/routes/+page.svelte:80` — fallos TTS se tragan con `.catch(() => undefined)` — demo sigue muda sin pista — toast opcional si `VoiceError`.

## Checked OK

- Contrato A2UI FV: `KNOWN`/`CATALOG_ID`, acciones `enviar_cedula`…`handoff`, `toActionBody` reenvía `confirm` desde eventos — alineado con `CONTRACT.md`.
- Guardrails server: `guardrails.check_text`, `validate.validate` (Rx, `AlertaRoja`, `leaks`), `fsm.action` (`blocked_red_flag`, `confirmation_required`, Rx en `agregar_pedido`) — `services/api/fsm.py`, `validate.py`, `guardrails.py`.
- Renderer: `ProductCard` oculta `ventaLibre === false`; server sobrescribe acciones/precios en `ProductCard` — `Node.svelte`, `validate.py`.
- CRM al cliente: `mock.public_customer` sin `condiciones_probables`; admin redacta vía `admin.py` / placeholder en `mock.admin_list` — no filtra al PWA.
- Auth: creds solo en memoria, `fv-identity` en localStorage, refresh ~2 min antes de expirar, retry 401/403 en creds — `auth.ts`.
- HTTP: `AbortSignal` en `post`, errores con surface (`stale_revision`) se renderizan — `http.ts`.
- UI demo: surfaces antiguas `inert` + atenuadas; doble tap acciones bloqueado con `busy` — `+page.svelte`.
- `?demo` / fake FSM: red flag, Rx, consentimiento, facturación, idempotencia `confirmar_reserva` — `fake.ts`.
- SW: solo GET same-origin; POST API no interceptados — `service-worker/index.ts`, comentario en `auth.ts`.
- Secretos en fuentes rastreadas: sin `AKIA…` en `app/src` / `services/api`; `app/.env` gitignored; `app/.env.example` solo IDs/URL públicos del contrato.
- Voz: módulo real exporta `voice` + `cancel`; fallback a fake si falla carga — `voice-client.ts`, `voice/index.ts`.
- Fail closed LLM: reintento + plantilla `T.products` — `fsm.free_turn`.

## Triage (orchestrator, verified)
- P0-1, P0-2: false positive → P2. Vite auto-loads `app/.env` on build; bundle embeds `VITE_FV_TRANSPORT=http` + API URL. Risk only on fresh clone without `.env` (gitignored).
- P0-3 + P1-2: real → fix with request generation token in `+page.svelte` (discard stale responses after Reiniciar; reset owns `busy`).
- P1-5: trivial → `clients.claim()` in SW activate.
- Rest: not fixed (time box).
- Fixed in da964d2 (deployed Amplify job 9). Regression: tests/playwright demo/05 "mid-request" (failed on old build, passes now).
