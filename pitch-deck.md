# Pitch deck — outline (3 min, hackathon)

Farmacéutico Virtual · Connect atVentures 2026 · reto **Fidelización transversal** (Farmaenlace).
Jurado: BuenTrip/Endeavor + Farmaenlace. Meta: validar el MVP y mover KPIs de Farmaenlace (recompra/fidelización). Modelo de negocio = el de Farmaenlace; no se discute. Detalles faltantes: después, si ganamos.
Solo outline. Diseño: DESIGN.md (paleta SmartClub, Source Sans 3, sin logo oficial, badge "Demo · datos simulados").

## Fuentes y reglas aplicadas
- **Andino** (NEST.Lab, *Workshop x Startups* + *Deep-dive: Estructura de deck*), adaptado a hackathon (sin marco inversionista): Cover → Elevator → Problema → Solución → Prueba → Siguiente paso → Cierre. Deck corto. Sin timing para 3 min → segundos = nuestros.
- **Andino**: nombre al abrir; quick hook emocional en el 1er minuto; gran POR QUÉ; high concept; historia ascendente.
- **Andino**: "Show, don't tell". 1 pregunta por slide. Menos texto. 3Ds (Double check, Diseño, Datos). Sin fecha.
- **Andino**: demo breve o screenshots, **no video**. No leer slides. Hablar despacio. Pocos acrónimos.
- **Andino**: prueba real, no inflar soft traction. Cierre activo: "¿Cuál es el siguiente paso?". Errores: deck saturado, sin métricas, cierre débil.
- **Montero** (*Establecer la propuesta de valor*, NEST 2025): W3 + "Para [cliente] que enfrentan [problema], ofrecemos [solución], que a diferencia de [alternativa], logra [beneficio]". <20 s. Beneficios > features. Palabras del cliente. Contra el status quo.
- **Reto Farmaenlace** (docs/drive, deck): p.24 compra única + "CX hace que el cliente quiera volver; la fidelización (smartclub) le da razones para elegirnos más veces y quedarse"; p.25 "De la transacción a la relación" · "Fidelizar con datos: personalizar por marca y arquetipo" · "Medir retención, abandono y valor de vida"; p.13 "Más confianza y recompra", "Tecnología con trato cercano"; p.32 ~2% online; p.17 SmartClub.

## Rúbrica → slides
Valor 30 → 2, 3, 7 · Técnico 25 → 4, 6 · Novedad 20 → 5 · Factibilidad 15 → 7, 8 · Claridad 10 → 1, 4, 8 (y ≤180 s).

## Slides

### 1. Portada + hook — 15 s · claridad
- **Mensaje:** Tu farmacéutico más cercano, en el celular.
- Eric Aguayo, Co-fundador y Director de IA Aplicada, Nimblersoft (solo). "Farmacéutico Virtual". Reto: Fidelización transversal.
- Visual: celular con botón mic. Sin fecha.

### 2. Problema (en palabras de Farmaenlace) — 20 s · valor
- **Mensaje:** compran una vez y no vuelven; lo digital no les sirve.
- Número grande: **"En 4 de 5 marcas, más de la mitad de los clientes compra una sola vez"** (p.24). Medicity 50,38% · Farmacias Económicas 38,77%.
- **~2%** ventas online (p.32).
- Status quo: catálogos, filtros, formularios → no lo usan → van o llaman a la farmacia.

### 3. Propuesta de valor — 15 s · valor
- **Mensaje:** le hablas y te arma la pantalla justa.
- Fórmula Montero (1 frase, <20 s): "Para clientes de Farmacias Económicas y Medicity que evitan las apps por complicadas, ofrecemos un farmacéutico virtual al que le hablas y te arma la pantalla que necesitas; a diferencia de catálogos y formularios, comprar —y volver a comprar— es tan fácil como preguntarle a tu farmacéutico."
- Visual: antes (catálogo) vs después (1 tarjeta).

### 4. DEMO en vivo — 50 s · técnico, claridad
- **Mensaje:** hablas → UI generada en segundos → reservas → vuelves.
- Flujo: QR + cupón → cédula → "algo para la gripe" → tarjetas OTC (precio, cashback SmartClub, stock cercano) → Cuidador vs Práctico (misma pregunta, 2 UIs) → reposición "como sueles llevar…" con doble cashback → reservar y retirar.
- PWA real: https://main.d2bloxc35rzfqy.amplifyapp.com
- Antes: warm-up GLiNER; 2 perfiles precargados (2 pestañas o 2 celulares); reset.
- **Fallback (en orden):** `?demo` (simulado, decirlo) → grabación de 40 s → 3 screenshots en slide oculta (Andino prefiere screenshots).

### 5. Diferenciador — 20 s · novedad
- **Mensaje:** no es un chatbot: la interfaz se arma para cada persona.
- Interfaz de Usuario Generativa y Conversacional (A2UI), voz primero, sin formularios.
- "Fidelizar con datos" (p.25): UI por arquetipo (Medicity p.12, Farmacias Económicas p.13); personaliza por comportamiento, **nunca nombra condición**.
- Guardrails: solo OTC, sin diagnóstico, alarma → alerta roja ECU 911, hand-off a farmacéutico humano.
- Visual: 3 íconos. Máx. 3 bullets.

### 6. Real vs simulado — 15 s · técnico
- **Mensaje:** IA real hoy; datos sintéticos.
- Real: Claude Haiku 4.5 (Bedrock) genera A2UI · GLiNER (Lambda) intención/entidades · Transcribe + Polly.
- Simulado: catálogo, stock, SmartClub, CRM, pedidos, factura (SIMULADA).
- Prueba: 100% checks en 6 fixtures (A2UI válido, OTC, alarma, sin condición), ~4 s, ~USD 0,005/respuesta (tests/llm/results/BENCHMARK.md). Evidencia técnica, no tracción.
- Repo: https://github.com/ericmaster/hackathon-connect-atventures · web híbrida: https://main.dfsvbpju4hwi2.amplifyapp.com

### 7. Piloto contra sus KPIs — 25 s · factibilidad, valor
- **Mensaje:** no reemplaza nada; se mide contra control y escala solo con datos.
- App nueva opt-in sobre las APIs actuales de Farmaenlace; no reemplaza la app actual.
- Fases: canario 1% web → piloto QR en unas pocas Farmacias Económicas/Medicity vs control → A/B web 10–50%.
- KPI norte: **recompra 30/60 días vs control** ("Más confianza y recompra", p.13; "Medir retención, abandono…", p.25). Tempranas: reservas completadas, retorno 7 días, instalaciones PWA.
- Encaje operativo: reserva y retiro en farmacia, facturación lista para SRI, SmartClub. Backlog: pago en app, domicilio, WhatsApp.
- Visual: timeline 3 pasos.

### 8. Siguiente paso + cierre — 15 s · factibilidad, claridad
- **Mensaje:** validemos el MVP en un piloto con Farmaenlace.
- Propuesta: piloto opt-in sobre sus APIs + QR en unas pocas farmacias; criterio de éxito = recompra 30/60 días vs control. Detalles se definen juntos después.
- High concept otra vez. Repo + URL demo. Pregunta activa: "¿Cuál es el siguiente paso?"

## Tiempos
| # | Slide | s | Rúbrica |
|---|---|---|---|
| 1 | Portada + hook | 15 | claridad |
| 2 | Problema | 20 | valor |
| 3 | Propuesta de valor | 15 | valor |
| 4 | Demo | 50 | técnico, claridad |
| 5 | Diferenciador | 20 | novedad |
| 6 | Real vs simulado | 15 | técnico |
| 7 | Piloto contra KPIs | 25 | factibilidad, valor |
| 8 | Siguiente paso + cierre | 15 | factibilidad, claridad |
| | **Total** (+5 s colchón) | **175** | |

## Abierto (Eric)
- Cargo/empresa para la portada.
- Hook: cerrado — señora adulta de Farmacias Económicas + "Pensemos… Según ella…"
