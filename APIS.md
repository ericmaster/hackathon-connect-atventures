# APIS.md — bem · Taxo · Mercately (para Connect atVentures 2026)

> Investigado el 7-oct-2026 leyendo la documentación oficial (y, en el caso de Mercately, el spec OpenAPI publicado).
> Leyenda: ✅ **verificado en docs** · ⚠️ **no verificado / ambiguo** (confirmar con los organizadores o con una llamada real) · 🧪 = smoke test de solo lectura.
> **No se hizo ninguna llamada autenticada**: no hay keys todavía.

## Resumen rápido

| | bem | Taxo Facturación | Taxo Extracción | Mercately |
|---|---|---|---|---|
| Qué hace | Archivo no estructurado (PDF, foto, audio, email…) → JSON según tu JSON Schema | Emite comprobantes electrónicos SRI (factura, NC, ND, retención, guía, liquidación) | Descarga comprobantes del SRI, consulta RUC, buzón tributario | CRM + WhatsApp/Messenger/IG, órdenes, catálogo, deals |
| Base URL | `https://api.bem.ai` (prefijo `/v3`) ✅ | `https://invoice.taxo.ws` ✅ | `https://staging-api.taxo.ws` (pruebas) / `https://api.taxo.ws` (prod) ✅ | `https://app.mercately.com` (`/retailers/api/v1/*`) y `https://mercately.shop` (`/api/v1/*` órdenes/productos) ✅ |
| Auth | Header `x-api-key` ✅ | `X-Key` (+ `X-Password` = clave del certificado de firma para emitir) ✅ | Header `x-api-key` ✅ | Header `api-key` ✅ |
| Sandbox | Sí: cada cuenta trae entornos `sandbox` y `production`; el entorno lo define la key ✅ | Campo `ambiente: 1` (pruebas SRI) vs `2` (producción) en cada comprobante ✅ | Servidor `staging-api` + keys `staging_…` ✅ | ⚠️ No hay sandbox documentado; se trabaja sobre una cuenta real (con número de WhatsApp conectado) |
| Keys | **Self-serve**: registro gratis en https://app.bem.ai/auth/sign-up → Settings → API Keys ✅ | **No self-serve**: "Solicitá tu API key al equipo de Taxo" ✅ (+ necesitas un certificado de firma electrónica del emisor ⚠️) | **No self-serve**: formulario "Solicitar cuenta" ✅ | Registro en https://app.mercately.com/register ("Empieza gratis"); API key la genera un **Administrador** en Configuración → API Key ✅. Planes pagos desde ~USD 225/mes; alcance del trial ⚠️ |
| Webhooks | Sí: suscripciones por función + firma HMAC `bem-signature` ✅ | Sí: `POST /webhooks` eventos `receipt-issued` / `issue-error` ✅ | Sí: `POST /webhooks` eventos `extraction.*` ✅ | Sí pero **solo** Cliente creado/actualizado y Orden creada/actualizada, se configuran en la UI, dependen del plan ✅. **No hay webhook de mensaje entrante de WhatsApp documentado** ⚠️ |
| Rate limits | No publicados; devuelve `429` (+`Retry-After` si aplica) ✅ | No publicados ⚠️ | No publicados ⚠️ | No publicados ⚠️ |

**Recomendación para mañana:** pedir a primera hora a los organizadores (1) API key de Taxo **staging/ambiente 1** + datos de un emisor de pruebas con certificado, (2) cuenta Mercately con WhatsApp conectado (QR o API oficial) y su API key + ID de una plantilla aprobada, (3) confirmar si bem da créditos extra. bem se puede activar hoy mismo (self-serve).

---

## 1. bem — https://docs.bem.ai

Fuentes: [Quickstart](https://docs.bem.ai/guide/quickstart) · [Authentication](https://docs.bem.ai/api/v3/authentication) · [Supported file types](https://docs.bem.ai/guide/file-types) · [Synchronous mode](https://docs.bem.ai/guide/synchronous-mode) · [Errors](https://docs.bem.ai/guide/errors) · [Webhooks](https://docs.bem.ai/guide/webhooks) · [Known limitations](https://docs.bem.ai/guide/known-limitations) · Índice completo: https://docs.bem.ai/llms.txt (cada página existe también como `.md`, p.ej. `https://docs.bem.ai/guide/webhooks.md`).

### Conceptos
- **Function**: unidad versionada. Tipos: `extract` (JSON Schema → JSON), `classify`, `split`, `join`, `enrich` (búsqueda semántica en una *Collection*), `parse`, `payload_shaping`, `send`, `render`, `evaluation`… ✅
- **Workflow**: DAG de funciones con un `mainNodeName`. Se invoca por nombre. ✅
- **Call**: una ejecución. El resultado está en `call.outputs[0].transformedContent` (extract) o `enrichedContent` (enrich). ✅
- **Collection**: catálogo para Enrich (p.ej. catálogo de productos/SKUs). ✅

### Auth, entornos, SDK
- Header `x-api-key: $BEM_API_KEY`. Keys en Settings → API Keys del dashboard. ✅
- Entornos `sandbox` y `production` en cada cuenta; **la key determina el entorno** (no hay header). ✅
- SDK npm: `bem-ai-sdk` (lee `BEM_API_KEY`). También CLI (`brew install bem-team/tools/bem`) y servidor MCP. ✅
- Paginación tipo Stripe: `limit` (def. 50, máx 100), `startingAfter`, `endingBefore`. ✅

### Tipos de archivo (`inputType`) ✅
`pdf, docx, email(.eml), text, jpeg(jpg/jfif), png, webp, heic, heif, csv, xls, xlsx, json, xml, html, mp3, wav, m4a, mp4`. ← fotos de recetas desde iPhone (`heic`) y notas de voz (`m4a`/`mp3`) están soportadas.
Envío: multipart (`file`) o JSON con base64 en `input.singleFile.inputContent` (sin prefijo `data:`).

### Endpoints más útiles

**1) Crear función extract** — `POST /v3/functions` ✅
```bash
curl -X POST https://api.bem.ai/v3/functions \
  -H "Content-Type: application/json" -H "x-api-key: $BEM_API_KEY" \
  -d '{
    "functionName": "receta-extractor",
    "type": "extract",
    "displayName": "Receta médica",
    "outputSchemaName": "Receta",
    "outputSchema": {
      "type": "object",
      "required": ["medicamentos"],
      "properties": {
        "paciente": {"type":"object","properties":{"nombre":{"type":"string"},"cedula":{"type":"string"}}},
        "medico": {"type":"object","properties":{"nombre":{"type":"string"},"registro":{"type":"string"}}},
        "fechaEmision": {"type":"string","description":"YYYY-MM-DD"},
        "medicamentos": {"type":"array","items":{"type":"object","properties":{
          "nombre":{"type":"string"},"principioActivo":{"type":"string"},"concentracion":{"type":"string"},
          "cantidad":{"type":"number"},"posologia":{"type":"string"},"duracionDias":{"type":"number"}}}}
      }
    }
  }'
```
Respuesta: `{"function":{"functionID":"fn_…","functionName":"receta-extractor","displayName":"…","type":"extract","currentVersionNum":1}}`

**2) Crear workflow** — `POST /v3/workflows` ✅
```bash
curl -X POST https://api.bem.ai/v3/workflows \
  -H "Content-Type: application/json" -H "x-api-key: $BEM_API_KEY" \
  -d '{"name":"receta-workflow","mainNodeName":"receta-extractor",
       "nodes":[{"name":"receta-extractor","function":{"name":"receta-extractor"}}]}'
```
Respuesta: `{"workflow":{"id":"wf_…","name":"receta-workflow","versionNum":1,"mainNodeName":"…","nodes":[…],"edges":[]}}`

**3) Llamar al workflow (síncrono)** — `POST /v3/workflows/{name}/call` ✅
```bash
# multipart (recomendado): wait va como form field
curl -X POST https://api.bem.ai/v3/workflows/receta-workflow/call \
  -H "x-api-key: $BEM_API_KEY" \
  -F "wait=true" -F "callReferenceID=sesion-123" -F "file=@receta.jpg"

# JSON + base64: wait va como query param
curl -X POST "https://api.bem.ai/v3/workflows/receta-workflow/call?wait=true" \
  -H "Content-Type: application/json" -H "x-api-key: $BEM_API_KEY" \
  -d '{"callReferenceID":"sesion-123","input":{"singleFile":{"inputType":"jpeg","inputContent":"'"$(base64 -w0 receta.jpg)"'"}}}'
```
Respuesta (200):
```json
{"call":{"callID":"wc_…","status":"completed","workflowName":"receta-workflow","callReferenceID":"sesion-123",
  "outputs":[{"eventID":"evt_…","eventType":"extract","transformedContent":{ "medicamentos":[…] }}],
  "errors":[],"url":"/v3/calls/wc_…","traceUrl":"/v3/calls/wc_…/trace"}}
```
- `wait=true` espera **máx. 30 s**: `200` completed · `500` failed (con `errors[]`) · `202` pending/running (no es error → hacer polling). ✅
- `callReferenceID` sirve de **clave de idempotencia** (mismo ID en ventana corta → devuelve el call existente). ✅
- Latencias típicas: extract de PDF corto = pocos segundos; extract→enrich ≈ 10 s. ✅

**4) Consultar un call (polling)** — `GET /v3/calls/{callID}` ✅ (status `pending|running|completed|failed`). Traza por nodo: `GET /v3/calls/{callID}/trace`.

**5) Inferir schema de un archivo** — `POST /v3/infer-schema` (multipart, máx 20 MB) ✅ — útil para arrancar rápido con una receta/factura de ejemplo.
```bash
curl -X POST https://api.bem.ai/v3/infer-schema -H "x-api-key: $BEM_API_KEY" -F "file=@receta.jpg"
```

**6) Catálogo para matching semántico** — `POST /v3/collections` + `POST /v3/collections/items` ✅ (items asíncronos, respuesta `{"status":"pending","eventID":…}`)
```bash
curl -X POST https://api.bem.ai/v3/collections -H "Content-Type: application/json" -H "x-api-key: $BEM_API_KEY" \
  -d '{"collectionName":"catalogo_medicity"}'
curl -X POST https://api.bem.ai/v3/collections/items -H "Content-Type: application/json" -H "x-api-key: $BEM_API_KEY" \
  -d '{"collectionName":"catalogo_medicity","items":[{"data":{"sku":"MED-001","name":"Paracetamol 500 mg x 20 tabletas","principioActivo":"paracetamol","precio":1.80}}]}'
```

**7) Función enrich (receta → SKU)** — `POST /v3/functions` con `type:"enrich"` ✅
```json
{"functionName":"sku-matcher","type":"enrich","config":{"steps":[{
  "sourceField":"medicamentos[*].nombre","collectionName":"catalogo_medicity",
  "targetField":"medicamentos[*].matchedProduct","topK":1,"searchMode":"semantic"}]}}
```
Encadenar con `PATCH /v3/workflows/{name}` enviando `nodes` + `edges` (`{"sourceNodeName":"receta-extractor","destinationNodeName":"sku-matcher"}`). El resultado trae `matchedProduct.data` + `cosineDistance` (menor = mejor; usar umbral). ✅

**8) Webhooks** — `POST /v3/webhook-secret` (genera secreto, se muestra una sola vez) + `POST /v3/subscriptions` ✅
```bash
curl -X POST https://api.bem.ai/v3/subscriptions -H "Content-Type: application/json" -H "x-api-key: $BEM_API_KEY" \
  -d '{"name":"receta-results","type":"transform","functionName":"receta-extractor","webhookURL":"https://<tu-tunel>/api/webhooks/bem"}'
```
Verificación: header `bem-signature: t=<unix>,v1=<hex>` = HMAC-SHA256(`"{t}.{rawBody}"`, secreto); rechazar si `t` > 5 min. El body es el evento tal cual (sin envoltorio). Solo eventos **terminales**. ✅

🧪 **Smoke test (solo lectura):**
```bash
curl -s "https://api.bem.ai/v3/workflows?limit=1" -H "x-api-key: $BEM_API_KEY" | jq .
```

### Gotchas bem
- Root del schema debe ser `object`; evitar >20 campos en raíz, anidación >3-4 niveles, enums >64 items (usar Enrich). ✅
- Campos ausentes en el documento vuelven `null` → pedir solo lo que el documento trae. ✅
- Reintentos: `429` (respetar `Retry-After`), `5xx`/`408` con backoff; no reintentar `400/401/404/422`. ✅
- Límites de tamaño en calls dependen del plan (infer-schema: 20 MB). ✅
- Pricing/créditos del plan gratis: ⚠️ no verificado.

---

## 2. Taxo — https://docs.taxo.ws

Taxo tiene **dos APIs separadas** con auth distinta. ⚠️ La página comercial https://taxo.co/ec/productos/taxo-api muestra un ejemplo con `https://api.taxo.ec/v1/invoices`, `Authorization: Bearer` y OAuth 2.0 que **no coincide** con la documentación técnica (docs.taxo.ws). Tomar docs.taxo.ws como fuente de verdad y confirmar con los organizadores cuál entregan.

### 2a. Taxo Facturación (emitir comprobantes SRI)
Fuentes: [Introducción](https://docs.taxo.ws/facturacion) · [Autenticación](https://docs.taxo.ws/facturacion/empezar/autenticacion) · [Facturas](https://docs.taxo.ws/facturacion/comprobantes/facturas) · [Autorización](https://docs.taxo.ws/facturacion/operaciones/autorizacion-de-comprobantes) · [Descarga](https://docs.taxo.ws/facturacion/operaciones/descarga-de-comprobantes) · [Envío por correo](https://docs.taxo.ws/facturacion/operaciones/envio-por-correo) · [Notificaciones](https://docs.taxo.ws/facturacion/operaciones/notificaciones) · [Catálogo](https://docs.taxo.ws/facturacion/referencia/catalogo) · [Consulta de catálogo](https://docs.taxo.ws/facturacion/referencia/consulta-de-catalogo) · [Errores](https://docs.taxo.ws/facturacion/referencia/errores)

- **Base:** `https://invoice.taxo.ws` ✅ · todo JSON (incluso errores). ✅
- **Auth:** `X-Key: <api key>` en todo request; `X-Password: <clave del certificado de firma>` solo para emitir/re-emitir (las lecturas no lo necesitan). Sin sesiones ni tokens que expiren. ✅
- **Ambiente:** `"ambiente": 1` = pruebas SRI (sin validez tributaria), `2` = producción. ✅ → **Usar siempre 1 en el hackathon.**
- **Idempotencia:** header `Idempotency-key` (16–48 chars, p.ej. UUID v4) en emisión/re-emisión. ✅
- **Proceso:** creación → firma → envío SRI → consulta de autorización → email. Normalmente **3–5 s**. Estados: `RECIBIDO, ENVIADO, AUTORIZADO, NO AUTORIZADO, DEVUELTO, ERROR`. ✅
- **Keys:** "Solicitá tu API key al equipo de Taxo". ✅ Necesitas además los datos de un **emisor** (RUC, establecimiento, punto de emisión) con certificado de firma cargado en Taxo ⚠️ (implícito por `X-Password`; pedir a organizadores un emisor de pruebas).

**Endpoints clave**

| # | Método y ruta | Uso |
|---|---|---|
| 1 | `POST /invoices/issue` | Emitir factura (crea+firma+envía+autoriza) ✅ |
| 2 | `GET /invoices/{id}` | Consultar factura y su estado ✅ |
| 3 | `POST /invoices` | Solo crear (sin emitir) ✅ |
| 4 | `POST /invoices/{id}/reissue` | Re-emitir (error si ya está AUTORIZADO) ✅ |
| 5 | `POST /edocs/{id}/issue` · `GET /edocs/{id}` | Autorizar / consultar cualquier comprobante ✅ |
| 6 | `GET /ver/{id}/pdf` · `GET /ver/{id}/xml` | RIDE (PDF) y XML ✅ (⚠️ no está claro si requieren `X-Key`; el ejemplo de respuesta los expone como URLs directas `url_formato_impresion` / `url_documento_electronico`) |
| 7 | `POST /edocs/send-email/{id}` | Reenviar por correo (opcional body `{"destinatarios":[…]}`) ✅ |
| 8 | `POST /credit-notes/issue` | Nota de crédito (devoluciones) ✅ |
| 9 | `POST /webhooks` | Suscribir `receipt-issued` / `issue-error` ✅ |
| 10 | `GET /catalog/id-types` · `GET /catalog/sales-tax-rates/2` · `GET /catalog/document-types` | Catálogos (lectura) ✅ |

**Emitir factura — request mínimo realista** (campos requeridos según docs: `secuencial, emisor, moneda, ambiente, totales, comprador, tipo_emision, items, pagos`) ✅
```bash
curl -X POST https://invoice.taxo.ws/invoices/issue \
  -H "Content-Type: application/json" \
  -H "X-Key: $TAXO_API_KEY" -H "X-Password: $TAXO_CERT_PASSWORD" \
  -H "Idempotency-key: $(uuidgen)" \
  -d '{
    "ambiente": 1, "tipo_emision": 1, "secuencial": 1001,
    "fecha_emision": "2026-10-08T15:00:00.000Z",
    "emisor": { "ruc": "'"$TAXO_EMISOR_RUC"'", "obligado_contabilidad": true,
      "razon_social": "EMISOR DE PRUEBAS", "nombre_comercial": "Demo Farmacia",
      "direccion": "Quito", "establecimiento": { "codigo": "001", "punto_emision": "001", "direccion": "Quito" } },
    "moneda": "USD",
    "comprador": { "razon_social": "Juan Pérez", "identificacion": "1712345678", "tipo_identificacion": "05",
      "email": "juan@example.com", "telefono": "0999999999", "direccion": "Quito" },
    "items": [
      { "cantidad": 2, "codigo_principal": "MED-001", "descripcion": "Paracetamol 500 mg x 20",
        "precio_unitario": 1.80, "descuento": 0, "precio_total_sin_impuestos": 3.60,
        "impuestos": [{ "codigo": "2", "codigo_porcentaje": "0", "tarifa": 0, "base_imponible": 3.60, "valor": 0 }] },
      { "cantidad": 1, "codigo_principal": "DER-010", "descripcion": "Protector solar FPS 50",
        "precio_unitario": 10.00, "descuento": 0, "precio_total_sin_impuestos": 10.00,
        "impuestos": [{ "codigo": "2", "codigo_porcentaje": "4", "tarifa": 15, "base_imponible": 10.00, "valor": 1.50 }] }
    ],
    "totales": { "total_sin_impuestos": 13.60, "descuento": 0, "propina": 0, "importe_total": 15.10,
      "impuestos": [
        { "codigo": "2", "codigo_porcentaje": "0", "base_imponible": 3.60, "valor": 0 },
        { "codigo": "2", "codigo_porcentaje": "4", "base_imponible": 10.00, "valor": 1.50 } ] },
    "pagos": [{ "medio": "tarjeta_credito", "total": 15.10 }]
  }'
```
Respuesta: el mismo objeto factura + `id` y `clave_acceso` (49 dígitos, la genera Taxo si no la envías). Luego `GET /invoices/{id}` → `estado`, `autorizacion{numero,fecha,estado,mensajes[]}`, `url_formato_impresion`, `url_documento_electronico`. ✅

Datos de referencia útiles ✅:
- `tipo_identificacion`: `04` RUC · `05` cédula · `06` pasaporte · `07` consumidor final · `08` exterior · `09` placa.
- IVA (`codigo: "2"`), `codigo_porcentaje`: `0`=0% · `2`=12% · `3`=14% · **`4`=15%** · `5`=5% · `6` no objeto · `7` exento · `8` diferenciado · `10`=13%. El catálogo en vivo (`/catalog/sales-tax-rates/2`) devuelve IVA 15% (`4`), 0% (`0`), no objeto (`6`).
- Medicamentos en Ecuador suelen ir con **IVA 0%**; cosméticos/otros con 15%. ⚠️ (regla tributaria general, validar por producto).
- `pagos[].medio`: `efectivo, cheque, debito_cuenta_bancaria, transferencia, deposito_cuenta_bancaria, tarjeta_debito, dinero_electronico_ec, tarjeta_prepago, tarjeta_credito, otros, endoso_titulos`.
- Consumidor final: el SRI usa identificación `9999999999999` con tipo `07` ⚠️ (convención SRI, no está en las docs de Taxo).

**Webhook de Taxo Facturación** ✅
```bash
curl -X POST https://invoice.taxo.ws/webhooks -H "Content-Type: application/json" \
  -H "X-Key: $TAXO_API_KEY" -H "X-Password: $TAXO_CERT_PASSWORD" \
  -d '{"event_name":"receipt-issued","webhook_url":"https://<tu-tunel>/api/webhooks/taxo"}'
```
Envía por POST el comprobante completo + `autorizacion`. `receipt-issued` → AUTORIZADO / NO AUTORIZADO; `issue-error` → CREADO (no se pudo firmar) / DEVUELTO. ⚠️ No se documenta firma/verificación del webhook (el payload de ejemplo incluye un campo `api-key`).

**Errores** ✅: HTTP 400/401/403/404/405/406/500/503 y body `{"message","code","details","parameter","value"}` con `code` ∈ `MISSING_PARAMETER, INVALID_PARAMETER, INVALID_VALUE, INVALID_DATA_TYPE, INVALID_FORMAT, INVALID_LENGTH`.

🧪 **Smoke test (solo lectura, no emite nada):**
```bash
curl -s https://invoice.taxo.ws/catalog/id-types -H "X-Key: $TAXO_API_KEY" | jq .
```

**Gotchas Taxo Facturación**
- `secuencial` debe ser único por establecimiento/punto de emisión (1–999999999) → llevar un contador; si se repite, el SRI rechaza. ⚠️ (regla SRI)
- Totales con 2 decimales y coherentes con la suma de items; un descuadre → `NO AUTORIZADO`/`DEVUELTO`.
- El ejemplo de la doc usa IVA 12% (antiguo); hoy la tarifa general es 15% (`codigo_porcentaje: "4"`).
- En la doc hay inconsistencias menores (p.ej. el ejemplo Python de autorización usa GET para `/edocs/{id}/issue`; la operación dice POST). Usar POST.

### 2b. Taxo Extracción (consultas al SRI)
Fuentes: [Primeros pasos](https://docs.taxo.ws/extraccion/getting-started/installation) · [RUC](https://docs.taxo.ws/extraccion/consultas/registro-publico-ruc) · [Webhooks](https://docs.taxo.ws/extraccion/webhooks) · [Contribuyentes](https://docs.taxo.ws/extraccion/taxpayers/create) · [Ventas/facturas](https://docs.taxo.ws/extraccion/extractions/ventas/invoices) · [Referencia OpenAPI](https://docs.taxo.ws/extraccion/referencia) (spec JSON en `https://docs.taxo.ws/openapi/extraccion.json`)

- Base: `https://staging-api.taxo.ws` (desarrollo) → `https://api.taxo.ws` (producción). Keys tipo `staging_evBmjgmR_XXXX`. Header `x-api-key`. ✅
- Cuenta: formulario "Solicitar Cuenta" (Zoho) enlazado en la página de Primeros pasos. ✅

| Método y ruta | Uso |
|---|---|
| `GET /taxpayer/{ruc}/registry` | Info pública del RUC (síncrono) — ideal para **autocompletar razón social en checkout B2B** ✅ |
| `POST /taxpayers` | Registrar contribuyente con `credential` = base64(`ruc:clave_SRI`) ✅ (⚠️ credenciales SRI reales: no usar en demo) |
| `POST /tasks` | Tarea de descarga, p.ej. `{"type":"SALE.INVOICE","taxpayerId":"…","startDownloadAt":"2025-02-03"}` → resultado por webhook ✅ |
| `POST /webhooks` | `{"url":"https://…"}`; eventos tipo `extraction.inprogress` con `data.status`, `taskType`, `content.summary` ✅ |

🧪 **Smoke test:**
```bash
curl -s https://staging-api.taxo.ws/taxpayer/0992712554001/registry -H "x-api-key: $TAXO_EXTRACTION_API_KEY" | jq .
```
Respuesta: `{"status":"success","data":{"numeroRuc":"…","razonSocial":"…","estadoContribuyenteRuc":"ACTIVO","tipoContribuyente":"…","regimen":"GENERAL",…}}` ✅

---

## 3. Mercately — https://mercately.redocly.app/apis

Fuentes: [API para desarrolladores](https://support.mercately.com/es/articles/16205397-api-para-desarrolladores-de-mercately) · [Portal API](https://mercately.redocly.app/apis) · **Spec OpenAPI 3.1 descargable:** `https://mercately.redocly.app/_spec/apis/index.yaml` · [Generar API Key](https://support.mercately.com/es/articles/9742287-como-generar-tu-api-key-en-mercately) · [Webhooks](https://support.mercately.com/es/articles/16112263-guia-funcional-modulo-de-webhooks-de-mercately) · [Webhook de clientes](https://support.mercately.com/es/articles/16112307-configuracion-de-webhooks-de-clientes) · [Webhook de órdenes](https://support.mercately.com/es/articles/16112776-configurar-un-webhook-de-ordenes-en-mercately)

- **Auth:** header `api-key: <API_KEY>` ✅. Se genera en *Usuario → Configuración → API Key → Generar una nueva API Key*; requiere rol **Administrador**; se muestra una sola vez; **generar otra invalida las anteriores** (¡no regenerar durante el hackathon si la key es compartida!). ✅
- **Servidores** ✅: `https://app.mercately.com` para `/retailers/api/v1/*`; `https://mercately.shop` para `/api/v1/*` (órdenes, productos, variantes, categorías).
- **Sandbox:** ⚠️ no documentado. La API opera sobre la cuenta real; para enviar WhatsApp se necesita un número conectado (API oficial o QR).

**Endpoints clave** (todos ✅ en el spec)

| # | Método y ruta | Uso |
|---|---|---|
| 1 | `POST /retailers/api/v1/whatsapp/send_message` | Enviar texto libre o media (JPG/PNG/**PDF**) — conexión **QR**. Requeridos: `phone_number` + `message` o `media_url` |
| 2 | `POST /retailers/api/v1/whatsapp/send_notification_by_id` | Enviar **plantilla** (WhatsApp Business API oficial). Requeridos: `phone_number`, `internal_id`, `template_params[]` |
| 3 | `GET /retailers/api/v1/whatsapp_templates` | Listar plantillas (`internal_id`, `text`, `status`) |
| 4 | `GET /retailers/api/v1/customers/{phone}/whatsapp_conversations` | Historial de WhatsApp de un cliente (`page`, `results_per_page`) — mensajes con `content.text`/`content.media_url` |
| 5 | `GET /retailers/api/v1/customers` | Listar clientes (`page, start_date, end_date, id_type, id_number, platform, order_by_last_interaction`) |
| 6 | `GET /retailers/api/v1/customers/{id|email|phone}` · `POST /retailers/api/v1/customers` · `PUT /retailers/api/v1/customers/{id|email|phone}` | Leer / crear / actualizar cliente (tags, `custom_fields`) |
| 7 | `POST /retailers/api/v1/customers/{id}/events` | Registrar evento en el timeline del cliente |
| 8 | `POST /retailers/api/v1/deals` | Crear negociación en un embudo (`funnel_name`, `stage`, `deal{…}`) |
| 9 | `POST https://mercately.shop/api/v1/orders` · `GET …/orders` | Crear/listar órdenes (crea el cliente si no existe) |
| 10 | `GET https://mercately.shop/api/v1/products?page=` · `GET …/products/{id_or_sku}` | Catálogo de productos |

**Enviar mensaje (QR)** ✅
```bash
curl -X POST https://app.mercately.com/retailers/api/v1/whatsapp/send_message \
  -H "Content-Type: application/json" -H "api-key: $MERCATELY_API_KEY" \
  -d '{"phone_number":"+593999999999","message":"Hola Ana 👋 Armamos tu página personalizada: https://demo.example/p/abc123",
       "tags":[{"name":"genui","value":true}]}'
```
**Enviar plantilla (API oficial)** ✅
```bash
curl -X POST https://app.mercately.com/retailers/api/v1/whatsapp/send_notification_by_id \
  -H "Content-Type: application/json" -H "api-key: $MERCATELY_API_KEY" \
  -d '{"phone_number":"+593999999999","internal_id":"'"$MERCATELY_TEMPLATE_ID"'","template_params":["Ana","https://demo.example/p/abc123"]}'
```
Respuesta (ambos): `{"message":"Ok","info":{"channel":"whatsapp","content":{"text":"…","media_url":"…"},"direction":"outbound","status":"submitted","destination":"+593…","country":"EC","created_time":"…","error":null}}`

**Crear orden** ✅
```bash
curl -X POST https://mercately.shop/api/v1/orders \
  -H "Content-Type: application/json" -H "api-key: $MERCATELY_API_KEY" \
  -d '{"order":{"sales_channel":"genui","delivery_method":"store_pickup","status":"pending",
       "customer_attributes":{"first_name":"Ana","last_name":"Pérez","phone":"593999999999","email":"ana@example.com"},
       "order_items_attributes":[{"product_id":"<web_id>","quantity":2,"unit_price":1.80}]}}'
```
Respuesta 201: `{"message":"Órden creada con éxito","order":{"web_id":"aAKpT9laN5","status":"pending","subtotal":"…","tax_amount":"…","total":"…","customer":{…},"order_items":[…]}}`

**Webhooks** ✅ (se configuran en la UI de Mercately, no por API): eventos **Cliente creado, Cliente actualizado, Orden creada, Orden actualizada**. Configuras *Target URL*, método de autenticación, **headers propios** y una **plantilla JSON con variables** (el payload lo defines tú). Debe responder `200`. "La disponibilidad depende del plan contratado".
- ⚠️ **No existe (documentado) un webhook por mensaje entrante de WhatsApp.** Alternativas: (a) el evento *Cliente creado* se dispara cuando un número nuevo escribe por primera vez (probable, no verificado); (b) usar un **Flow/chatbot** de Mercately que capture la intención y etiquete/actualice al cliente → dispara *Cliente actualizado*; (c) polling a `GET /customers?platform=whatsapp&order_by_last_interaction=desc` + `…/whatsapp_conversations`; (d) para la demo, disparar el flujo con un botón "simular WhatsApp entrante".

🧪 **Smoke test (solo lectura):**
```bash
curl -s https://app.mercately.com/retailers/api/v1/whatsapp_templates -H "api-key: $MERCATELY_API_KEY" | jq .
curl -s https://app.mercately.com/retailers/api/v1/agents -H "api-key: $MERCATELY_API_KEY" | jq .
```

**Gotchas Mercately**
- Formato de teléfono: los ejemplos usan `+593999999999` en envíos y `593996459124` en respuestas de órdenes → ⚠️ probar ambos en `GET /customers/{phone}`.
- Con API oficial de WhatsApp, fuera de la ventana de 24 h solo se pueden enviar **plantillas aprobadas** (regla de Meta) → pedir una plantilla genérica con variable de URL a los organizadores. Con QR se puede texto libre.
- Varias respuestas de error documentadas como `400 Unauthorized` (no 401). Manejar ambos.
- `send_message` crea/actualiza al cliente con los campos opcionales (nombre, email, tags, `custom_fields`, `funnel_name`+`stage` crea un deal) → útil para marcar conversiones en el CRM.
- Rate limits no publicados ⚠️.

---

## 4. Cómo encajan (para la idea de Generative UI)
1. **Mercately** = canal (WhatsApp) + CRM + órdenes. Entrada: webhook *Cliente creado/actualizado* (o polling); salida: link personalizado vía `send_message`/plantilla, y luego el RIDE en PDF vía `media_url`.
2. **bem** = convierte foto de receta / orden de compra / nota de voz en JSON tipado (+ Enrich contra catálogo para SKUs) → contexto para generar la UI.
3. **Taxo** = factura SRI autorizada en ~3–5 s al checkout (`ambiente: 1`), RIDE PDF reenviado por WhatsApp; `GET /taxpayer/{ruc}/registry` autocompleta datos de empresa (B2B).
