# PITCH.md — 3 minutos + checklist de demo

**Nombre tentativo:** *Receta → Página* / "Farmacia Generativa" (definir mañana).
**Una línea:** "Convertimos cada conversación de WhatsApp en una farmacia online hecha a la medida de esa persona — y la cerramos con factura SRI en segundos."

## Guion (3:00)

| Tiempo | Bloque | Qué decir / mostrar |
|---|---|---|
| 0:00–0:20 | **Gancho** | "Farmaenlace atiende 7,3 millones de clientes en 1.422 farmacias. Pero en digital vende muy poco: en 2022 Medicity estaba en 0,5 % de las ventas con meta de 3–5 %; hoy se habla de alrededor de 2 %." (Si un juez da la cifra real, usar esa.) |
| 0:20–0:45 | **Problema** | "Nadie entra a una farmacia online a *navegar*. Llegas con una receta, un síntoma o una urgencia. Un catálogo igual para todos no convierte; por eso la gente escribe por WhatsApp… y espera." |
| 0:45–1:00 | **Insight / solución** | "Generative UI: una página que se genera al momento para *esa* persona y *esa* receta, nace en WhatsApp y termina con la factura en el celular." |
| 1:00–2:10 | **Demo en vivo (70 s)** | 1) Mando foto de receta al WhatsApp (o simulador). 2) **bem** la convierte en JSON y la empareja con el catálogo. 3) Llega el link por **Mercately**; la página se arma en streaming: receta entendida, genérico vs marca, tratamiento completo calculado, retiro en la Económicas más cercana. 4) Pago → **Taxo** emite la factura SRI (ambiente de pruebas) → el RIDE llega por WhatsApp. (Bonus 10 s: misma tecnología, foto del cuaderno de una farmacia independiente → pedido B2B.) |
| 2:10–2:35 | **Impacto** | "Ventas netas 2025: USD 645 M. Cada punto de penetración digital ≈ USD 6,5 M al año. Atacamos los tres retos: **vender más** (conversión desde WhatsApp y recompra), **ampliar acceso** (quien no llega a una farmacia, recibe/retira), **operar mejor** (menos digitación de pedidos y facturas)." |
| 2:35–2:50 | **Por qué ahora / por qué yo** | "Los tres APIs ya existen y conversan: canal (Mercately), entendimiento de documentos (bem), cumplimiento SRI (Taxo). Yo construyo Generative UI en producción; esto se puede pilotear en una semana con una marca." |
| 2:50–3:00 | **Cierre / ask** | "Piloto de 30 días con Medicity o Económicas en una ciudad, medido en conversión WhatsApp→compra y ticket promedio." |

**Frases a evitar:** decir que Fybeca/SanaSana son de Farmaenlace (son de la competencia); prometer venta de medicamentos controlados; presentar el 2 % como dato oficial.

## Preguntas probables del jurado (respuestas cortas)
- **¿Y si bem lee mal la receta?** → Confirmación del cliente en la página + validación del químico farmacéutico antes de despachar; umbral de `cosineDistance` para el match de SKU.
- **¿Regulación?** → Medicamentos controlados quedan fuera (derivación a tienda); consentimiento explícito por tratarse de datos de salud (LOPDP); la factura se emite en ambiente de pruebas en la demo.
- **¿Por qué no un e-commerce normal?** → Porque la intención llega por WhatsApp y es individual; la página generada reduce pasos a cero (no hay que buscar ni armar carrito).
- **¿Costo por página?** → Una llamada a LLM + una a bem por sesión (centavos); se cachea por intención.
- **¿Cómo se integra con su stack?** → Farmaenlace usa SAP S/4HANA retail ([SAP News, ene-2025](https://news.sap.com/latinamerica/2025/01/farmaenlace-avanza-en-su-transformacion-digital-apoyada-por-sap-y-sybven/)); catálogo y stock vendrían de ahí; las órdenes ya caen en Mercately.

## Checklist de demo

**Antes de presentar (T-30 min)**
- [ ] Smoke tests de APIS.md pasan (bem, Taxo, Mercately) con las keys del día.
- [ ] `ambiente: 1` en Taxo (¡nunca 2!) y `secuencial` nuevo sin usar.
- [ ] Workflow de bem "calentado" (una llamada previa) y < 30 s con la foto de demo.
- [ ] Celular con WhatsApp abierto en el chat de la cuenta Mercately; notificaciones visibles; modo no molestar OFF para ese chat.
- [ ] Laptop: brillo al máximo, zoom del navegador 125 %, pestañas: app, WhatsApp Web (respaldo), dashboard bem (call trace), RIDE.
- [ ] Túnel (`cloudflared`) o deploy Vercel activo; URL corta lista.
- [ ] Tres fotos de receta en el celular y en la laptop (una "perfecta", una real-difícil, una B2B de cuaderno).
- [ ] **Video de respaldo** (60–70 s) de toda la demo grabado y en el escritorio.
- [ ] Botón "simular WhatsApp entrante" por si falla el webhook.
- [ ] Factura de respaldo ya emitida (ID y RIDE a mano) por si el SRI de pruebas está lento.
- [ ] Hotspot del celular como red de respaldo.
- [ ] Cronómetro: pitch completo ≤ 3:00 ensayado 3 veces.

**Durante la demo**
- [ ] Narrar mientras carga (la página en streaming es parte del show).
- [ ] Mostrar 1 segundo el JSON de bem (credibilidad técnica) y volver a la UI.
- [ ] Mostrar el estado AUTORIZADO + clave de acceso de 49 dígitos.
- [ ] Si algo tarda > 10 s → pasar al video sin disculparse.

**Después**
- [ ] Dejar link/QR de la demo y repo (si lo piden) en la última slide.
