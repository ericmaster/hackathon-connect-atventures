# Connect atVentures 2026 — kit de preparación (Eric Aguayo)

Hackathon de **BuenTrip Ventures + Endeavor Ecuador**, jueves **8-oct-2026**, un solo día. Retos de **Farmaenlace**: operar mejor · vender más · ampliar acceso. APIs obligatorias: **bem**, **Taxo**, **Mercately**. Premio: USD 1.000 + gift cards (USD 500 y 250). Entregables y criterios: **desconocidos** → asumimos demo en vivo + pitch corto.

> **Regla:** el código del producto se escribe **durante** el hackathon. Este repo hoy solo tiene investigación y plan. (Un borrador de código hecho antes del cambio de regla quedó aparte en `/workspace/hackathon-prep-scratch/` — **no copiarlo** al proyecto del hackathon.)

## Archivos
| Archivo | Contenido |
|---|---|
| [APIS.md](APIS.md) | Auth, base URLs, sandbox, cómo obtener keys, endpoints clave con request/response y curl, webhooks, gotchas — con fuentes y marcas ✅/⚠️ |
| [IDEAS.md](IDEAS.md) | Concepto **Generative UI** para Farmaenlace: 4 variantes rankeadas, plan de demo solo en ~6 h, verificación de la cifra de penetración digital |
| [PITCH.md](PITCH.md) | Guion de 3 min, Q&A y checklist de demo |
| [TOOLING.md](TOOLING.md) | Qué está instalado, logins y keys pendientes, URLs de registro |
| `.env.example` | Variables que necesita cada API |

## Plan para mañana (resumen)
1. **0:00–0:30** — Keys del día → smoke tests con curl (APIS.md) → `npx create-next-app@latest` + Tailwind → `vercel` deploy vacío / `cloudflared tunnel`.
2. **0:30–1:30** — bem: `infer-schema` con receta → función extract + colección catálogo + enrich + workflow → ruta de subida de foto.
3. **1:30–3:00** — Generative UI: schema de UI (zod) + componentes whitelisted + `streamText`/`Output.object` → `useObject` en `/p/[id]`.
4. **3:00–4:00** — Checkout → Taxo `POST /invoices/issue` (ambiente 1) → estado AUTORIZADO + RIDE.
5. **4:00–4:45** — Mercately: link personalizado y RIDE por WhatsApp; webhook Cliente/Orden o botón "simular".
6. **4:45–6:00** — Bonus B2B si sobra tiempo; ensayo, video de respaldo, slides.

## Antes de empezar
- Confirmar con organizadores: credenciales Taxo (ambiente 1 + emisor de pruebas), cuenta Mercately con WhatsApp, créditos bem, entregables/criterios.
- **Marcas correctas:** Medicity y Farmacias Económicas (Fybeca/SanaSana son de la competencia, FEMSA/GPF).
