# TOOLING.md — qué instalar/conectar HOY (sin escribir código de producto)

> Estado revisado el 7-oct-2026 ~19:50 (Quito) en el **box** de Grok Bot (máquina Linux compartida de agentes), **no** en tu laptop. Si mañana programas en tu laptop, repite esta lista allí.

## Estado del box

| Herramienta | Estado | Nota |
|---|---|---|
| Node.js | ✅ v20.19.2 | Next.js 16 pide ≥ 20.9 → OK. (Opcional: Node 22 LTS en tu laptop.) |
| npm | ✅ 9.2.0 | |
| pnpm | ✅ 10.33.4 | corepack 0.24.0 disponible |
| git | ✅ 2.47.3 | repo local `git init` en `/workspace/hackathon-connect` (sin remoto) |
| gh (GitHub CLI) | ✅ 2.46.0 — **sin login** | `gh auth login` cuando decidas (no se hizo) |
| Vercel CLI | ✅ instalado hoy, v62.7.0 (`npm i -g vercel`, enlazado en `/usr/local/bin`) — **sin login** | `vercel login` pendiente |
| cloudflared | ✅ instalado hoy, 2026.10.0 | túneles rápidos para webhooks sin cuenta: `cloudflared tunnel --url http://localhost:3000` |
| jq | ✅ 1.7 | para los curl de APIS.md |
| ngrok | ❌ no instalado | no hace falta (usar cloudflared) |

## Pendiente: logins (hazlos tú)
- [ ] `gh auth login` (si quieres repo/PR en GitHub; el repo local ya existe).
- [ ] `vercel login` y, mañana, `vercel link` + `vercel env add …` para deploy público (los webhooks de Mercately/Taxo/bem necesitan URL HTTPS pública: Vercel o cloudflared).
  - ⚠️ En Vercel serverless el estado en memoria no persiste entre invocaciones; para la demo, app local + cloudflared es más seguro, o usar Vercel KV/Upstash.

## Keys necesarias

| Servicio | ¿Self-serve? | Dónde | Qué guardar en `.env` |
|---|---|---|---|
| **bem** | ✅ Sí, registro gratis | https://app.bem.ai/auth/sign-up → Settings → API Keys (crear key de **sandbox**) | `BEM_API_KEY` (+ `BEM_WEBHOOK_SECRET` si usas webhooks) |
| **Taxo Facturación** | ❌ No — "Solicitá tu API key al equipo de Taxo" | Pedir a organizadores/Taxo; contacto comercial en https://taxo.co/ec/productos/taxo-api ("Solicitar API Key") | `TAXO_API_KEY`, `TAXO_CERT_PASSWORD` + datos del emisor de pruebas (`TAXO_EMISOR_*`) |
| **Taxo Extracción** (opcional, consulta RUC) | ❌ No — formulario "Solicitar Cuenta" | https://docs.taxo.ws/extraccion/getting-started/installation | `TAXO_EXTRACTION_API_KEY` (formato `staging_…`) |
| **Mercately** | 🟡 Registro sí ("Empieza gratis": https://app.mercately.com/register), pero necesitas número de WhatsApp conectado (QR o API oficial), rol Admin para la API key, y los webhooks dependen del plan | Lo más realista: **cuenta provista por organizadores** | `MERCATELY_API_KEY`, `MERCATELY_TEMPLATE_ID` (si es API oficial), `MERCATELY_WEBHOOK_TOKEN` (header que tú defines) |
| **LLM para Generative UI** | ✅ Sí | OpenAI: https://platform.openai.com/api-keys · o Vercel AI Gateway (una key para varios modelos): https://vercel.com/ai-gateway | `OPENAI_API_KEY` **o** `AI_GATEWAY_API_KEY`; `GENUI_MODEL` |

**Mensaje sugerido a organizadores (hoy):** "Hola, compito solo en Connect atVentures. ¿Mañana entregan credenciales de sandbox para Taxo (API key + clave de certificado + RUC/establecimiento de pruebas, ambiente 1) y una cuenta Mercately con WhatsApp conectado y su API key? ¿Hay créditos de bem? ¿Cuáles son los entregables y criterios de evaluación? Gracias."

## Stack a usar mañana (versiones vistas en npm hoy)
- `next` 16.4 (App Router, Turbopack; ojo: viene con `cacheComponents` en el template — leer `node_modules/next/dist/docs` si algo raro pasa).
- `ai` 7.0.x + `@ai-sdk/react` 4.0.x + `@ai-sdk/openai` 4.0.x, `zod` 4.x. Patrón: `streamText` + `Output.object()` → `useObject`. (`@ai-sdk/rsc`/`streamUI` = experimental.)
- `tailwindcss` 4.x · `typescript` 5.9 (TS 7 ya salió en npm; quedarse en 5.9 por compatibilidad).
- SDK opcional bem: `bem-ai-sdk` (o fetch nativo).

## Checklist de esta noche (sin código)
- [ ] Crear cuenta bem y key sandbox; correr el smoke test de APIS.md.
- [ ] Key de OpenAI o AI Gateway con saldo.
- [ ] Mensaje a organizadores (arriba).
- [ ] `vercel login`, `gh auth login`.
- [ ] Preparar datos de demo: 3–4 fotos de recetas ficticias, lista de ~40 productos (precio, principio activo, IVA 0 %/15 %), logos/colores Medicity y Económicas.
- [ ] Leer IDEAS.md (variante #1) y PITCH.md; ensayar el gancho en voz alta.
