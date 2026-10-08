# IDEAS.md — Generative UI para Farmaenlace

**Tesis de Eric:** el canal digital de Farmaenlace pesa ~2 % de las ventas. Un e-commerce "de catálogo" igual para todos no convierte en farmacia (la gente llega con *una receta, un síntoma o una urgencia*, no a "navegar"). **Generative UI websites** = una página generada al vuelo para *esa* persona y *esa* intención, que nace en WhatsApp (donde ya está el cliente) y cierra con factura SRI en segundos.

## ⚠️ Dos correcciones antes de pitchear
1. **Fybeca y SanaSana NO son de Farmaenlace.** Son de Corporación GPF / FEMSA Salud Ecuador (competencia directa; FEMSA compró GPF en 2019 — [FEMSA](https://femsa.gcs-web.com/news-releases/news-release-details/femsa-comercio-completes-acquisition-corporacion-gpf-ecuador-0)). Las marcas de Farmaenlace son **Farmacias Económicas** (1.154 locales), **Medicity** (211), Farmacias Coral, Comisariato de las Mascotas, Wellderma, Ambiente, Difarmes, Mayorista, Especialidad ([Informe de Sostenibilidad 2025](https://www.farmaenlace.com/wp-content/uploads/2026/07/Informe-de-Sostenibilidad-2025-Farmaenlace-WEB.pdf), p. 9). **Usar Medicity (premium) y Económicas (masivo/precio) en la demo.**
2. **La cifra de "~2 % de penetración digital" no la pude verificar con una fuente pública.** Lo más cercano:
   - Junio 2022: *"Las ventas por el e-commerce de Medicity actualmente es 0.5% mensual de la venta de la cadena, prevén alcanzar el 1% en este año y … de 3 al 5% [en tres años], el promedio del mercado"* — Chiquinquirá Polo, Farmaenlace ([IT Ahora, 23-jun-2022](https://itahora.com/2022/06/23/medicity-estrategias-para-potenciar-el-canal-digital/)).
   - El perfil público de la jefa de canales digitales reporta "+100 % en ventas e-commerce" (sin base).
   - → **Decir en el pitch:** "Farmaenlace venía de 0,5 % en 2022 con meta de 3–5 %; hoy se habla de ~2 %" y, si un juez de Farmaenlace da el número real, usar ese. No presentarlo como dato auditado.

### Números verificados para dimensionar (Informe de Sostenibilidad 2025 de Farmaenlace)
- Ventas netas 2025: **USD 645,59 M** (+11 %); línea Farma USD 306 M (+13 %).
- **1.422 puntos de venta**, **7,3 M de clientes** atendidos en 2025.
- Canal de distribución: **2.615 clientes B2B**, de ellos **1.838 farmacias independientes**.
- Cuenta rápida (supuesto): si digital = 2 % → ~USD 12,9 M/año; **cada +1 pp de penetración ≈ USD 6,5 M/año**. Llegar a la meta del 5 % ≈ +USD 19 M/año.

Mapeo a retos: **(1) operar mejor · (2) vender más · (3) ampliar acceso.**

---

## Variantes del concepto (rankeadas)

### 🥇 1. "Tu farmacia, armada para ti" — de la receta en WhatsApp a una página personalizada (B2C · retos 2 y 3)
- **Problema:** quien tiene una receta escribe por WhatsApp, espera a un asesor, recibe precios por chat y muchas veces termina yendo (o no) a una farmacia. Fricción = venta perdida; el e-commerce genérico no resuelve "¿tienen *esto* que me recetaron?".
- **Flujo:**
  1. Cliente escribe al WhatsApp de Medicity/Económicas (Mercately) y manda foto de la receta.
  2. **bem** (`POST /v3/workflows/receta-workflow/call`, `wait=true`) extrae paciente, médico, medicamentos, posología, duración → **Enrich** contra colección `catalogo` → SKUs + `cosineDistance`.
  3. El LLM genera la **UI** (spec JSON validada por schema → componentes whitelisted): tarjeta de la receta "entendida", productos equivalentes/genéricos (Económicas = precio; Medicity = conveniencia), tratamiento completo calculado (posología × días = cajas), recordatorio de recompra, retiro en tienda vs domicilio, chat con químico farmacéutico.
  4. **Mercately** `send_message` / plantilla con el link `…/p/{sesión}`; al pagar → `POST mercately.shop/api/v1/orders` (queda en el CRM).
  5. **Taxo** `POST /invoices/issue` (`ambiente: 1`, IVA 0 % medicinas / 15 % resto) → `GET /invoices/{id}` → RIDE PDF enviado por WhatsApp (`send_message` con `media_url`).
- **APIs/endpoints:** bem (`/v3/functions`, `/v3/workflows`, `/v3/workflows/{n}/call`, `/v3/collections(+items)`), Mercately (`send_message` o `send_notification_by_id`, `/api/v1/orders`, webhook *Cliente creado/actualizado*), Taxo (`/invoices/issue`, `/invoices/{id}`, `/ver/{id}/pdf`).
- **Demoable en ~6 h (solo):** sí — 3 recetas de prueba (foto de celular), catálogo mock de ~40 SKUs, página generada en streaming, factura en ambiente de pruebas, mensajes reales por WhatsApp si hay cuenta Mercately; si no, simulador.
- **Wow:** el jurado ve la página *armarse sola* en vivo a partir de una foto, con el tratamiento completo calculado, y a los segundos le llega la factura SRI autorizada al celular.
- **Riesgos:** letra de médico ilegible (mitigar: confirmación humana + "químico farmacéutico valida"); medicamentos controlados/psicotrópicos (excluir y derivar a tienda); normativa ARCSA de venta online de medicamentos con receta y **LOPDP** (datos de salud = datos sensibles → consentimiento explícito) ⚠️ no es asesoría legal; Mercately sin webhook de mensaje entrante (mitigar: webhook *Cliente* + Flow, o botón "simular WhatsApp").

### 🥈 2. "Vitrina de reposición generativa" para farmacias independientes (B2B · retos 1 y 2)
- **Problema:** Farmaenlace distribuye a 1.838 farmacias independientes. Los pedidos llegan por WhatsApp, fotos de listas escritas a mano, Excel o facturas del proveedor anterior; un vendedor los digita.
- **Flujo:** la farmacia manda foto/Excel/nota de voz de su pedido → **bem** (extract + Enrich a SKU, soporta `xlsx`, `m4a`, `jpeg`) → página B2B generada para *esa* farmacia: pedido pre-armado, faltantes sugeridos por temporada, precios por volumen, crédito disponible → confirma → **Mercately** orden + deal en embudo B2B → **Taxo** factura con RUC; `GET /taxpayer/{ruc}/registry` (Taxo Extracción) autocompleta razón social y valida RUC ACTIVO.
- **Demoable:** sí, mismo motor que #1 con otro "skin" y otro schema. Ideal como **segundo acto** del pitch: "un motor, dos canales".
- **Wow:** de una foto de un cuaderno a un pedido facturado; reduce digitación del equipo comercial.
- **Riesgos:** precios/crédito reales no disponibles (mock); requiere `TAXO_EXTRACTION_API_KEY` adicional.

### 🥉 3. "Recompra proactiva" para pacientes crónicos (B2C · reto 2)
- **Problema:** hipertensos/diabéticos compran cada mes, pero la recompra depende de que se acuerden; se van a la competencia.
- **Flujo:** bem lee la receta o una factura anterior (PDF/XML de Taxo) → calcula fecha de fin de tratamiento → **Mercately** plantilla de recordatorio con link → página generada con "tu pedido de siempre", adherencia, promo de fidelidad, opción de retiro en el local más cercano → orden + factura **Taxo**.
- **Demoable:** sí (se puede mostrar como extensión de #1 con "avanzar el reloj 28 días").
- **Wow:** convierte una venta en suscripción; métrica clara (LTV).
- **Riesgos:** la plantilla debe estar aprobada por Meta; consentimiento de recordatorios.

### 4. "Landing por intención" para campañas (B2C · retos 2 y 3)
- **Problema:** el tráfico de Ads/WhatsApp cae en páginas genéricas.
- **Flujo:** la palabra clave/mensaje de entrada ("dengue", "bebé", "temporada de lluvias", "Quito vs Guayaquil") + perfil del cliente en Mercately (tags, ciudad) → página generada con kit, guía y precios en el tono de la marca (Económicas vs Medicity); **bem** ingiere PDFs de promociones de proveedores para poblarla; checkout con **Taxo**.
- **Demoable:** sí, pero menos "mágico" sin receta; bueno como diapositiva de visión.
- **Riesgos:** difícil demostrar impacto en 1 día; sin datos reales de campañas.

> Recomendación: construir **#1** como demo principal y mostrar **#2** (y #3 como "próximo paso") reutilizando el mismo motor de Generative UI. Los otros conceptos de respaldo (sin GenUI) quedan en el apéndice.

---

## Plan de demo solo en ~6 h (variante #1, con #2 como bonus)

**Arquitectura (decidir mañana, se escribe mañana):** Next.js (App Router) + Tailwind + **Vercel AI SDK v7** — servidor `streamText({ output: Output.object({ schema }) })` → `createTextStreamResponse(toTextStream(...))`; cliente `useObject` de `@ai-sdk/react` que renderiza un **registro de componentes whitelisted** (Hero, RecetaCard, ProductGrid, TratamientoCompleto, RetiroEnTienda, Recordatorio, Checkout, ChatFarmaceutico). El LLM elige bloques y props; nunca HTML/JS crudo. `streamUI` de `@ai-sdk/rsc` existe pero las docs de AI SDK v7 lo marcan **experimental** y recomiendan AI SDK UI → evitarlo. Estado en memoria (Map) y túnel `cloudflared` para webhooks.

| Hora | Bloque | Resultado verificable |
|---|---|---|
| 0:00–0:30 | Keys + smoke tests con curl (APIS.md) · `create-next-app` · deploy vacío en Vercel | 3 APIs responden; URL pública |
| 0:30–1:30 | bem: `infer-schema` con una receta → función `receta-extractor` + colección `catalogo` + `sku-matcher` + workflow; ruta de upload | foto → JSON con SKUs |
| 1:30–3:00 | **Generative UI**: schema de UI + 6–8 componentes + `useObject` en `/p/[id]`; prompt con contexto (receta, perfil, marca) | la página se arma en streaming |
| 3:00–4:00 | Checkout → Taxo `invoices/issue` (ambiente 1) + polling `GET /invoices/{id}` + link RIDE | factura AUTORIZADA en pantalla |
| 4:00–4:45 | Mercately: `send_message`/plantilla con el link y el RIDE PDF; webhook *Cliente*/*Orden* o botón "simular WhatsApp" | mensaje llega al celular |
| 4:45–5:15 | Bonus #2 B2B (otro schema/skin) **solo si todo lo anterior funciona** | foto de cuaderno → pedido B2B |
| 5:15–6:00 | Ensayo x3, video de respaldo, slides, congelar código | demo grabada + pitch cronometrado |

**Cortes de alcance si se atrasa (en este orden):** quitar #2 → quitar webhook (usar botón) → Mercately solo para el mensaje final → Taxo con un comprobante pre-emitido de respaldo.

**Datos a preparar hoy (no es código):** 3 fotos de recetas ficticias legibles + 1 difícil; lista de ~40 productos con precio, principio activo e IVA (0 %/15 %); textos de marca Medicity/Económicas; número de WhatsApp de prueba.

---

## Apéndice — ideas de respaldo (sin Generative UI, combinan ≥2 APIs)
- **Conciliación de facturas de proveedores** (reto 1): bem lee facturas PDF/XML de proveedores + Taxo Extracción descarga los comprobantes recibidos del SRI → cruce automático y alertas por WhatsApp (Mercately) al área de compras.
- **Devoluciones y notas de crédito por WhatsApp** (reto 1): foto del ticket/RIDE → bem → Taxo `POST /credit-notes/issue` → confirmación por Mercately.
- **Farmacia comunitaria rural** (reto 3): pedidos por nota de voz (bem transcribe `m4a`) para parroquias sin local cercano, consolidados para retiro en la Económicas más próxima, factura Taxo.
