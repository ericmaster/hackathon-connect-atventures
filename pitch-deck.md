# Pitch deck — outline (3 min)

Farmacéutico Virtual · Connect atVentures 2026 · reto Fidelización transversal (Farmaenlace).
Solo outline. Diseño: DESIGN.md (paleta SmartClub, Source Sans 3, sin logo oficial, badge "Demo · datos simulados").

## Fuentes y reglas aplicadas
- **Andino** (NEST.Lab, *Workshop x Startups: Pitch para levantar capital* + *Deep-dive: Estructura de deck*): orden Cover → Elevator → Problema → Solución → (Tracción) → Ask → Cierre. Deck corto 5–10 slides. Sin plantilla ni timing para 3 min → segundos = nuestros.
- **Andino**: abrir con nombre + empresa; quick hook emocional en el 1er minuto; gran POR QUÉ; high concept; historia ascendente.
- **Andino**: "Show, don't tell". 1 pregunta por slide. Menos texto. 3Ds: Double check, Diseño, Datos. Sin fecha en portada.
- **Andino**: solución = demo breve o screenshots, **no video**. No leer slides. Hablar despacio. Pocos acrónimos.
- **Andino**: validadores reales; no inflar soft traction sin hard traction. Ask atado a hitos. Cierre activo: "¿Cuál es el siguiente paso?". Errores: deck saturado, sin métricas, cierre débil.
- **Montero** (*Establecer la propuesta de valor*, NEST 2025): W3 (Who/What/Why) + fórmula "Para [cliente] que enfrentan [problema], ofrecemos [solución], que a diferencia de [alternativa], logra [beneficio]". <20 s. Beneficios > features. Palabras del cliente. Comparar contra status quo.
- **Reto Farmaenlace** (docs/drive): p.24 compra única; p.32 ~2% online; p.12 Medicity / p.13 Económicas (arquetipos); p.17 SmartClub 75.377 socios. **Rúbrica**: valor 30 · técnica 25 · novedad 20 · viabilidad 15 · claridad 10.

## Slides

### 1. Portada + hook — 15 s
- **Mensaje:** Tu farmacéutico más cercano, en el celular.
- Eric Aguayo (solo). "Farmacéutico Virtual". High concept grande.
- Visual: foto/mock de celular con botón mic. Sin fecha.

### 2. Problema — 20 s
- **Mensaje:** el cliente compra una vez y no vuelve; lo digital no le sirve.
- Número grande: **"4 de 5 marcas: más de la mitad compra una sola vez"** (deck p.24). Medicity 50,38% · Económicas 38,77%.
- **~2%** ventas online (deck p.32).
- Status quo: catálogos, filtros, formularios → no lo usa → va o llama a la farmacia.

### 3. Propuesta de valor — 15 s
- **Mensaje:** le hablas y te arma la pantalla justa.
- Fórmula Montero (1 frase, <20 s): "Para clientes de Económicas y Medicity que evitan las apps por complicadas, ofrecemos un farmacéutico virtual al que le hablas y te arma la pantalla que necesitas; a diferencia de catálogos y formularios, comprar es tan fácil como preguntarle a tu farmacéutico más cercano."
- Visual: antes (catálogo) vs después (1 tarjeta).

### 4. DEMO en vivo — 50 s
- **Mensaje:** hablas → UI generada en segundos → reservas.
- Flujo: QR + cupón → cédula → "algo para la gripe" → tarjetas OTC (precio, cashback SmartClub, stock cercano) → Cuidador vs Práctico (misma pregunta, 2 UIs) → reposición "como sueles llevar…" doble cashback → reservar y retirar.
- PWA real: https://main.d2bloxc35rzfqy.amplifyapp.com
- Antes: warm-up GLiNER; 2 perfiles precargados (2 pestañas o 2 celulares); reset.
- **Fallback (en orden):** `?demo` (simulado, decirlo) → grabación pre-hecha 40 s → 3 screenshots en el deck. Andino prefiere screenshots a video: tenerlos en slide oculta.

### 5. Diferenciador — 20 s
- **Mensaje:** no es un chatbot: la interfaz se arma para cada persona.
- Interfaz de Usuario Generativa y Conversacional (A2UI), voz primero, sin formularios.
- CRM por arquetipo (Medicity p.12, Económicas p.13). Personaliza por comportamiento, **nunca nombra condición**.
- Guardrails: solo OTC, sin diagnóstico, alarma → alerta roja ECU 911, hand-off a farmacéutico humano.
- Visual: 3 íconos. Máx. 3 bullets en pantalla.

### 6. Real vs simulado — 15 s
- **Mensaje:** IA real hoy; datos sintéticos.
- Real: Claude Haiku 4.5 (Bedrock) genera A2UI · GLiNER (Lambda) intención/entidades · Transcribe + Polly.
- Simulado: catálogo, stock, SmartClub, CRM, pedidos, factura (marcada SIMULADA).
- Prueba: 100% checks en 6 fixtures (A2UI válido, OTC, alarma, sin condición), ~4 s, ~USD 0,005/respuesta (tests/llm/results/BENCHMARK.md). Es hard evidence técnica, no tracción comercial: no venderla como tracción.
- Repo: https://github.com/ericmaster/hackathon-connect-atventures · web híbrida: https://main.dfsvbpju4hwi2.amplifyapp.com

### 7. Ruta a piloto + métrica — 25 s
- **Mensaje:** no reemplaza nada; escala solo con datos.
- App nueva opt-in sobre APIs actuales de Farmaenlace. No reemplaza la app actual.
- Fases: canario 1% web → piloto QR en tienda vs control → A/B web 10–50%.
- Métrica norte: **recompra 30/60 días vs control**. Tempranas: reservas completadas, retorno 7 días, instalaciones PWA.
- Facturación lista para SRI. Backlog: pago en app, domicilio, WhatsApp.
- Visual: timeline 3 pasos.

### 8. Ask + cierre — 15 s
- **Mensaje:** piloto con Farmaenlace. ¿Siguiente paso?
- Ask: acceso a APIs (catálogo, stock, SmartClub) + pocas farmacias Económicas/Medicity para QR. Hito: recompra 30/60 días vs control.
- High concept otra vez. Repo + URL demo + contacto. Pregunta activa: "¿Cuál es el siguiente paso?"

## Tiempos
| # | Slide | s |
|---|---|---|
| 1 | Portada + hook | 15 |
| 2 | Problema | 20 |
| 3 | Propuesta de valor | 15 |
| 4 | Demo | 50 |
| 5 | Diferenciador | 20 |
| 6 | Real vs simulado | 15 |
| 7 | Ruta a piloto | 25 |
| 8 | Ask + cierre | 15 |
| | **Total** (+5 s colchón) | **175** |

## Abierto (Eric)
- Ask exacto: ¿cuántas farmacias / qué APIs / plazo? (fuentes dicen "pocas"; no hay número).
- Modelo de ingresos: canvas = "por definir" (candidato SaaS o fee por sesión). Andino lo pide; en 3 min se omite.
- Cargo/empresa para la portada.
- Equipo: solo Eric → 1 línea en portada, sin slide.
