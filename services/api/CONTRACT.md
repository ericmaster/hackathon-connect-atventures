# Farmacéutico Virtual — API contract (workstream A)

Owner: A (backend). Readers: B (PWA/A2UI), C (voz/admin). Keep this EXACT; changes are announced in commits.

## Transport / auth
- Region: `us-east-1`. Lambda `connect-atv-orchestrator` (Python 3.12).
- Public access: **API Gateway HTTP API `connect-atv-api`, IAM (SigV4) auth on every route**, browser credentials from a
  **Cognito Identity Pool (guest/unauthenticated identities, no login, classic flow OFF)**.
  - Browser: `cognito-identity` `GetId({IdentityPoolId})` → `GetCredentialsForIdentity({IdentityId})` → sign each request
    with `aws4fetch` (`service: 'execute-api'`, `region: 'us-east-1'`). Cache the IdentityId in localStorage; refresh creds on expiry.
  - API URL / Identity Pool ID: see **Deployed values** at the bottom (filled when created).
- The guest `identityId` owns the session: a session created by one identity is rejected (403) for any other.
- CORS: `https://main.d2bloxc35rzfqy.amplifyapp.com`, `https://main.dfsvbpju4hwi2.amplifyapp.com`, `http://localhost:5173`.
- All bodies JSON (`Content-Type: application/json`). Spanish copy, synthetic data only.

## Standard response (POST /session, /turn, /action, /demo/reset)
```json
{
  "sessionId": "s_8f3c2a...",
  "state": "consulta",
  "revision": 4,
  "messages": [ /* A2UI v0.9.1 message objects, in order */ ],
  "spokenText": "Te muestro tres opciones para la gripe.",
  "mode": "real"
}
```
- `messages`: always ONE new surface per response: first `createSurface` (`surfaceId` = `fv-<revision>`, catalogId
  `https://farmaenlace.ec/a2ui/fv/v1`), then `updateComponents` (one or more, one has id `root`), optional `updateDataModel`.
  Append surfaces to the chat history; older surfaces are stale (their buttons fail the revision check).
- `createSurface.theme`: `{"senior": true}` on EVERY surface once a **Cuidador** profile has **accepted consent**
  (PWA enables large text). Absent otherwise (no consent → no archetype UI, §6.5). Cleared by `/demo/reset`.
- `spokenText`: short phrase for TTS (send to `/voice/tts`), never contains conditions.
- `mode`: `"real"` = server/AI pipeline ran for real (GLiNER + Haiku, or a deterministic template step);
  `"simulado"` = a fallback was used (GLiNER cold/timeout → keyword intent, or Bedrock failed → safe template).
- Errors: HTTP 4xx/5xx with the same shape plus `"error": {"code": "...", "message": "..."}`. `messages` then holds a
  small surface you can render (or ignore). Codes: `bad_request`, `not_found`, `forbidden`, `stale_revision` (409),
  `action_not_allowed` (409), `confirmation_required` (400), `blocked_red_flag` (409), `internal`.

## States (server FSM)
`saludo` → `cedula` → `consentimiento` → `consulta` → `productos` → `farmacia` → `resumen` → `facturacion` → `confirmacion`
- `/session` runs `saludo` and returns state `cedula` directly (welcome + QR coupon + cédula field in one surface).
- `consulta`: free-text questions (`/turn`). `productos`: ProductCards shown. `farmacia`: cart has items, choose pharmacy.
  `resumen`: ResumenPedido. `facturacion`: one billing question at a time. `confirmacion`: reservation done.
- Red flag at any point: AlertaRoja surface, state stays (`consulta`), commerce actions blocked for the session until
  `/demo/reset` (409 `blocked_red_flag`).
- 3rd invalid cédula: hand-off surface (HandoffCard) is offered; you may keep trying.

## Routes
### POST /session
Body: `{"qr": "BIENVENIDA"}` (optional, default coupon). → standard response, state `cedula`.

### POST /turn
Body: `{"sessionId": "...", "text": "algo para la gripe"}` (text ≤ 500 chars; typed or final STT transcript).
- In `cedula`: digits in text are taken as the cédula (same as `enviar_cedula`).
- In `facturacion`: text is the answer to the pending field (email / nombre / identificación) or "consumidor final".
- Otherwise: GLiNER → guardrails → read-only dispatcher → Haiku 4.5 → validated A2UI (or safe template).
- Turn latency: template steps < 1 s; LLM turns ~3–10 s warm (budget 25 s).

### POST /action
Body:
```json
{"sessionId": "...", "revision": 4,
 "action": {"name": "agregar_pedido", "surfaceId": "fv-4", "sourceComponentId": "p1", "context": {"sku": "FV-1001"}}}
```
- `revision` MUST equal the current session revision, else 409 `stale_revision` (body = current state re-rendered).
- Context values that are A2UI bindings (`{"path": "/cedula"}`) MUST be resolved by the renderer against the surface data
  model before sending (send the literal value).
- Commercial actions require `context.confirm === true` (templates already put it in the button's event context; forward it).
- Server recomputes prices, stock, IVA, coupon and cashback; it never trusts client prices.

| action name | context | allowed in state(s) | effect |
|---|---|---|---|
| `enviar_cedula` | `{cedula}` | cedula | módulo 10; valid → `consentimiento` (new profile if unknown); 3rd invalid → HandoffCard |
| `consentimiento` | `{acepta: bool}` | consentimiento | stores bool + timestamp → `consulta` (Reposicion card if consent + due product) |
| `agregar_pedido` | `{sku, qty?, confirm:true}` | consulta, productos, farmacia | OTC only (Rx → HandoffCard); → `farmacia` (PharmacyCards with stock) |
| `reservar` | `{sku, confirm:true}` | consulta, productos | reposición: adds frequent product (double cashback) → `farmacia` |
| `por_que` | `{sku}` | any after consent | explanation by behavior only (never conditions) |
| `seguir_comprando` | `{}` | farmacia, resumen | → `consulta` (cart kept) |
| `retirar_aqui` | `{pharmacyId}` | farmacia | checks stock → `resumen` (ResumenPedido) |
| `confirmar_reserva` | `{confirm:true}` | resumen, facturacion | if billing incomplete → `facturacion` question; else idempotent reservation → `confirmacion` |
| `facturacion_tipo` | `{tipo: "consumidor_final"\|"datos"}` | facturacion | `consumidor_final` only if total incl. IVA ≤ $50 |
| `facturacion_dato` | `{campo: "email"\|"nombre"\|"identificacion", valor}` | facturacion | validates; next missing field or billing confirm card |
| `handoff` | `{}` | any | HandoffCard (nearest pharmacy) |
| `como_llegar`, `llamar` | — | — | **client-side only** (`openUrl` with `mapsUrl` / `tel:`); do not send |

Billing rule: email ALWAYS required. Total incl. IVA (15%) ≤ $50 → offer "Consumidor final" (07 / 9999999999999) + email;
> $50 → nombre/razón social + cédula/RUC/pasaporte + email (only missing ones, one per surface). No address/phone.
Double tap of `confirmar_reserva` never duplicates: same order/invoice/coupon returned.

### POST /demo/reset
Body `{"sessionId": "..."}` → wipes only that session's sandbox (profiles copy, coupon, cart, orders, invoices) and
returns state `cedula` (same sessionId, revision keeps increasing).

### POST /voice/tts  (delegates to `voice.py`, by C)
Body `{"text": "..."}` → `{"audio": "<base64 mp3>", "format": "mp3", "contentType": "audio/mpeg", "engine", "voice", "chars", "ms"}`. 501 if voice.py missing.
### POST /voice/stt-url
Body `{"language": "es-US", "sampleRate": 16000}` → `{"url": "wss://...", "expiresAt", "language", "sampleRate", "mediaEncoding": "pcm"}`. Never log the url.

### GET /admin/{service}  (read-only)
`service` ∈ `crm | catalogo | inventario | farmacias | smartclub | pedidos | facturacion` → `{"service": "crm", "items": [...]}`.
`crm` items never include `condiciones_probables` (redacted). `GET /admin/logs` → `{"items": [{ts, route, state, ms, mode, intent, status}]}` (last 100).

## Components (catalogId `https://farmaenlace.ec/a2ui/fv/v1`)
Basic: Text, Image, Icon, Video, AudioPlayer, Row, Column, List, Card, Tabs, Modal, Divider, Button, CheckBox, TextField,
DateTimeInput, ChoicePicker, Slider. Functions: required, regex, length, numeric, email, formatString, formatCurrency, openUrl, cedulaEc, rucEc.
Custom FV (flat props, as in `tests/llm/system_prompt.md`):
- `ProductCard`: sku, name, detail, price, cashback, stock, ventaLibre, note?, action{event:{name:"agregar_pedido",context:{sku,confirm:true}}}
- `PharmacyCard`: pharmacyId, name, distance, hours, stock, phone, mapsUrl, action (retirar_aqui {pharmacyId})
- `SugerenciaPersonalizada` / `Reposicion`: message, product{sku,name,price,cashback}, why, action (reservar {sku,confirm:true}).
  The server sends NO separate "¿Por qué…?" Button: the PWA card renders it from `why` (or may send `por_que {sku}`).
- `AvisoSalud`: text
- `ResumenPedido`: items[{name,qty,price}], total, cashback, pharmacy, subtotal?, iva?, coupon?, action (confirmar_reserva {confirm:true})
- `ConfirmacionPedido`: orderNumber, pharmacy, pickupTime, qrValue
- `FacturaMock`: number, customerName, customerId, items, subtotal, iva, total, label "SIMULADA", email
- `Cupon`: title, code, until, note
- `HandoffCard`: summary, pharmacy, phone, mapsUrl
- `AlertaRoja`: text, phone "911", action (handoff)
Prices are pre-formatted strings (`"$4,50"`).

## Template surfaces (deterministic) — examples
Cédula (state `cedula`):
```json
{"version":"v0.9.1","createSurface":{"surfaceId":"fv-1","catalogId":"https://farmaenlace.ec/a2ui/fv/v1"}}
{"version":"v0.9.1","updateComponents":{"surfaceId":"fv-1","components":[
 {"id":"root","component":"Column","children":["t1","t2","cup","f1","b1"]},
 {"id":"t1","component":"Text","text":"¡Hola! Soy tu Farmacéutico Virtual de Farmaenlace.","variant":"h2"},
 {"id":"t2","component":"Text","text":"¿Me ayudas con tu número de cédula?","variant":"body"},
 {"id":"cup","component":"Cupon","title":"Cupón de bienvenida $3 en tu primera reserva","code":"BIENVENIDA3","until":"31/12/2026","note":"Se aplica solo a tu primera reserva"},
 {"id":"f1","component":"TextField","label":"Cédula","variant":"number","value":{"path":"/cedula"},
  "checks":[{"call":"required","args":{"value":{"path":"/cedula"}},"message":"Escribe tu cédula"},
            {"call":"cedulaEc","args":{"value":{"path":"/cedula"}},"message":"¿Me la repites? Revisa los 10 dígitos"}]},
 {"id":"b1","component":"Button","child":"b1l","variant":"primary","action":{"event":{"name":"enviar_cedula","context":{"cedula":{"path":"/cedula"}}}}},
 {"id":"b1l","component":"Text","text":"Continuar"}]}}
{"version":"v0.9.1","updateDataModel":{"surfaceId":"fv-1","path":"/cedula","value":""}}
```
(Templates may put several components in one `updateComponents`; LLM output uses one per line. Both are valid A2UI.)

Consent: Text + CheckBox(label "Acepto que Farmaenlace use mi historial de compras para darme sugerencias personalizadas",
value {path:"/consent"}) + Button `consentimiento` {acepta:{path:"/consent"}}.
Billing question: Text + TextField(value {path:"/factura/<campo>"}) + Button `facturacion_dato` {campo, valor:{path:"/factura/<campo>"}};
≤$50 also a Button `facturacion_tipo` {tipo:"consumidor_final"}.
Confirmación: ConfirmacionPedido + FacturaMock (label SIMULADA) + Cupon (if applied) + Text cashback.

## Demo data (synthetic)
- Cuidador: cédula `1710034065` (don Luis, voz primero, letra extra grande, Multivitamínico 50+ mensual → reposición due).
- Práctico: cédula `1712456787` (Andrea, una tarjeta directa).
- Any other valid cédula (e.g. `1729876548`) → new profile. Invalid example: `1710034066`.
- Pharmacies: 5 in Quito (`MED-UIO-014` Medicity La Carolina etc.). Coupon `BIENVENIDA3` ($3, first reservation).
- Rx decoys (`requiere_receta`): Oseltamivir 75 mg, Amoxicilina 500 mg → never in ProductCard.

## Deployed values (live since 8 oct ~12:40)
- Region: `us-east-1`
- API URL: `https://znpzz1wg21.execute-api.us-east-1.amazonaws.com` (stage `$default`, so no path prefix: `POST {API_URL}/session`)
- Identity Pool ID: `us-east-1:8434d4ed-e17e-4082-ad26-42b59e004e3e` (guest only, classic flow OFF; role `connect-atv-guest-role`
  can only `execute-api:Invoke` this API)
- Sign with service `execute-api`, region `us-east-1`. Unsigned → 403 `{"message":"Forbidden"}` from API Gateway (not our shape).
- Stage throttling: 5 rps, burst 10 → 429 from API Gateway.
- Browser sketch:
```js
import { CognitoIdentityClient, GetIdCommand, GetCredentialsForIdentityCommand } from '@aws-sdk/client-cognito-identity';
import { AwsClient } from 'aws4fetch';
const ci = new CognitoIdentityClient({ region: 'us-east-1' });
const IdentityId = localStorage.fvIdentityId ||= (await ci.send(new GetIdCommand({ IdentityPoolId: POOL }))).IdentityId;
const { Credentials: c } = await ci.send(new GetCredentialsForIdentityCommand({ IdentityId }));
const aws = new AwsClient({ accessKeyId: c.AccessKeyId, secretAccessKey: c.SecretKey, sessionToken: c.SessionToken,
                            service: 'execute-api', region: 'us-east-1' });
const res = await aws.fetch(`${API_URL}/turn`, { method: 'POST', headers: { 'content-type': 'application/json' },
                                                 body: JSON.stringify({ sessionId, text }) });
```
  (GetId/GetCredentialsForIdentity are unsigned calls; no AWS keys in the bundle. Creds last ~1 h; refresh on 403/expiry.
  Keep the same IdentityId: the session is bound to it, a different identity gets 403 `forbidden`.)
- Direct invoke (ops/tests): `aws lambda invoke --function-name connect-atv-orchestrator --cli-binary-format raw-in-base64-out
  --payload '{"route":"POST /session","body":{}}' out.json` → same body plus `_status`, `_ms`, `_trace`.
