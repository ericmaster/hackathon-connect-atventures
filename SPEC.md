# Farmacéutico Virtual: especificación de producto

> Estado: borrador del 8 oct 2026. **Decidido** = acordado con Eric. **Propuesta** = falta que Eric lo confirme. **Por definir** = no está decidido. **En prueba** = se está probando.
> Fuentes: `PITCH.md`, `services/dashboard/canvas.json`, `services/dashboard/value-prop.json` y `docs/DRIVE-SUMMARY.md`.

## 1. Resumen
El Farmacéutico Virtual es un asistente de Farmaenlace al que le hablas o le escribes y que **arma en el momento la pantalla que necesitas**: productos, la farmacia más cercana y tu beneficio SmartClub, sin catálogos ni formularios. Está pensado para los clientes que hoy evitan las apps y la web. Entran por un QR en la farmacia que les da un beneficio y se identifican solo con su cédula. Los datos de facturación se piden una sola vez, justo antes de la primera compra.

**High-concept:** *"Tu farmacéutico más cercano, en el celular."*

## 2. Reto y problema
- **Reto (decidido):** Programas de fidelización transversal. Beneficio secundario: servicio al cliente.
- **Problema (validado por Eric):** muchos clientes de Farmaenlace evitan las apps y la web porque les resultan complejas o porque no se manejan con la tecnología. **Meta: bajar las barreras de entrada.**
- **Contexto (deck del reto):**
  - ~2% de las ventas son online.
  - En 4 de 5 marcas, más de la mitad de los clientes compra una sola vez (por ejemplo, Medicity 50,38% y Económicas 38,77%).
  - SmartClub: **75.377 socios** y 6 marcas integradas (Medicity, Económicas, Wellderma, Ambiente, Mascotas, BYD). Cashback de hasta 5%.
  - ⚠️ La "meta de 100k socios" de `PITCH.md` **no está verificada**. Para cifras oficiales, usar solo 75.377.
- **Alternativas de hoy:** ir a la farmacia y preguntarle al farmacéutico, llamar a la farmacia, o usar las apps y la web actuales con catálogo.

## 3. Usuario
| Rol | Definición | Estado |
|---|---|---|
| Segmento | Clientes de Farmaenlace que evitan apps/web por complejidad o poca familiaridad con la tecnología | Decidido |
| Early adopters | Adultos mayores o cuidadores que ya compran en la farmacia física | Borrador (hipótesis) |
| Decisor / comprador | Farmaenlace (canal digital / SmartClub) | Decidido |

## 4. Propuesta de valor
Versiones y checklist del método Montero: pestaña **Propuesta de valor** del dashboard (`https://connect-atventures-dash.ericmaster.ninja/#propuesta`, datos en `services/dashboard/value-prop.json`).

**Fórmula, versión cliente (borrador):**
> "Para la audiencia objetivo de Farmaenlace que evitan las apps porque les resultan complicadas o poco familiares, ofrecemos un asistente al que simplemente le hablas y te arma en el momento la pantalla que necesitas, que a diferencia de las tiendas online llenas de catálogos y formularios, hace que comprar sea tan fácil como preguntarle a tu farmacéutico más cercano."

**Para Farmaenlace:** una capa conversacional sobre web y móvil que no exige rediseñar el e-commerce ni cambiar su core. Apunta a subir frecuencia, ticket y share of wallet entre marcas.

## 5. Diferenciador: Interfaz de Usuario Generativa y Conversacional
- **No es "solo un chatbot".** Un chatbot responde con texto. Aquí **la interfaz se arma sola para cada persona**: letra grande, pocos botones y tarjetas (producto, beneficio, farmacia, cupón) con acciones directas.
- Es **audio-first**: un botón grande para hablar (push-to-talk). Escribir es la alternativa.
- **No hay formularios**: los datos se piden uno a uno, dentro de la conversación.
- La misma capa sirve para la PWA móvil y para la web híbrida. El formato de la UI generada es A2UI (§9).
- La UI se adapta al **arquetipo del cliente** (insights CRM, §6).
- **Regla de demo:** la UI generada tiene que verse **en los primeros 10 s**.

## 6. Inteligencia de cliente desde CRM (decidido, innovación)
Asumimos que el CRM de Farmaenlace ya tiene insights por cliente. El mock los incluye. Sirven para personalizar la UI, reponer y sugerir — siempre bajo la capa de guardrails (§8). Solo datos sintéticos.

**Campos del CRM mock (además de identidad y facturación):** preferencias, condiciones/enfermedades probables, productos frecuentes, arquetipo de cliente.

### 6.1 UI generativa adaptada al arquetipo
La UI no solo cambia las sugerencias: **se adapta al arquetipo** (letra, prioridad de voz, cantidad de opciones, tipo de productos).
- Adulto mayor: letra grande, voz primero, pocas opciones.
- Mamá joven: productos infantiles / combos.
**Momento de demo:** la misma pregunta hecha por dos clientes distintos → dos UIs distintas.

### 6.2 Reposición proactiva
Desde productos frecuentes, p. ej. "Tu losartán se acaba en ~3 días, ¿te lo reservo en tu farmacia?". Recompra + adherencia = fidelización.
→ UI: tarjeta `SugerenciaPersonalizada` / `Reposicion` con acción de reservar y affordance "¿por qué me sugieres esto?" (§9).

### 6.3 Volante (flywheel)
Las conversaciones enriquecen el perfil CRM y generan señales de demanda para la planificación de Farmaenlace (contacto: **Diego Alarcón**, jefe de planificación de demanda).

### 6.4 Sugerencias personalizadas
Basadas en estos insights, siempre bajo guardrails (§8). Sin diagnóstico.

### 6.5 Privacidad (LOPDP Ecuador)
Los datos de salud son sensibles → hace falta **consentimiento explícito** para usar "condiciones probables". Nunca afirmar una condición ("usted tiene X"); hablar por comportamiento ("como sueles llevar X…"). Incluir la explicación "¿por qué me sugieres esto?". Posicionamiento: **personalización transparente**. Solo datos sintéticos. Momento del consentimiento: por definir (§18).

## 7. Flujos (decidido)
Cada paso indica lo que hace el usuario y, después de "→ UI:", lo que genera la interfaz. Recorrido completo: onboarding → consulta → pedido y retiro → datos de facturación → compra completada. El hand-off está disponible en todo momento.

### 7.1 Onboarding: QR + cédula (pseudo-FSM guiado por IA)
La IA conversa, pero una máquina de estados decide el paso y no avanza hasta cumplirlo: `saludo → pedir_cedula → validar → buscar_crm → (confirmar_datos) → listo`.
1. En la farmacia, el cliente ve un QR con un beneficio por instalar la app. **El beneficio queda abierto: lo define Farmaenlace** (ej. descuento o bonificación en la próxima compra). → UI: ninguna (material físico).
2. Escanea el QR y se abre la PWA, sin pasar por la tienda de apps. → UI: saludo del Farmacéutico Virtual, botón grande para hablar y la opción de instalar en la pantalla de inicio.
3. El asistente pide la cédula; el usuario la dice o la escribe. **Es el único dato del onboarding.** → UI: una pregunta y un campo numérico grande (o la captura por voz).
4. Se valida el dígito verificador (módulo 10) **en el dispositivo** y otra vez **en el backend**. Si falla, la pide de nuevo sin culpar ("¿me la repites?"); al tercer intento ofrece el hand-off. → UI: aviso corto en el mismo campo.
5. Busca la cédula en el CRM. Si hay datos cruzados, los muestra para confirmar ("¿Eres …?", Sí/No). **El MVP asume que no hay datos cruzados**: este paso se salta.
6. El beneficio del QR queda asociado a la cédula en SmartClub y se entrega al completar la compra (§7.5). → UI: "Listo, ya tienes tu beneficio" y pasa a la consulta.

**Módulo 10 (cédula):** 10 dígitos; provincia 01–24 (30 = registrados en el exterior); tercer dígito < 6; coeficientes 2-1-2-1-2-1-2-1-2 sobre los 9 primeros (si el producto pasa de 9, se resta 9); verificador = (10 − suma mód 10) mód 10. Ejemplo sintético válido: `1710034065`.

En el demo todo esto es simulado con datos sintéticos: ninguna cédula ni dato personal es real.

### 7.2 Consulta conversacional
1. El usuario toca el botón y habla, por ejemplo: "algo para la gripe". → UI: la transcripción en vivo y un indicador de que el asistente está escuchando o pensando.
2. La capa de guardrails revisa el pedido antes de generar la respuesta (§8). Si es una consulta de síntomas, hace preguntas mínimas de seguridad. → UI: una pregunta con botones grandes.
3. Sugiere opciones. → UI: 1–3 tarjetas de producto con precio, beneficio SmartClub (cashback o descuento), stock en la farmacia más cercana y el botón "Agregar al pedido". Cuando aplica, una nota visible: "si persiste, consulta a un médico".

### 7.3 Pedido y retiro
1. El usuario agrega productos. → UI: resumen del pedido (productos, cantidades, total y cashback).
2. Elige retirar en la farmacia más cercana (u otra). → UI: tarjeta de farmacia con stock, distancia y horario, y botones "Retirar aquí", "Cómo llegar" y "Llamar".
3. Sin entrega a domicilio.

### 7.4 Datos de facturación (solo antes del checkout)
1. Antes de pagar, el asistente pide **solo los datos que falten**, una pregunta a la vez: nombre o razón social, cédula o RUC, email, dirección y teléfono. → UI: una pregunta y un campo grande por dato; al final, una tarjeta para confirmar.
2. Se guardan **de forma permanente en el CRM** y en **caché en el dispositivo**. La próxima vez no se piden.
3. **Requisitos SRI (verificado):** la factura electrónica exige nombre o razón social e identificación (cédula, RUC o pasaporte) del comprador. Dirección, email y teléfono son opcionales en el comprobante, pero el email sirve para enviar la factura. Se puede facturar a **"consumidor final"** (ID `9999999999999`) solo hasta **USD 50 con IVA**; sobre ese monto hay que identificar al comprador. Desde 2026 una factura a consumidor final no se puede anular, y no sirve para deducir gastos personales (las medicinas son deducibles).
4. **Decidido:** si el total es ≤ USD 50 con IVA, ofrecer "consumidor final" como opción rápida; si supera, pedir nombre + identificación + email.

### 7.5 Compra completada
1. → UI: confirmación del pedido (número, farmacia, hora y código QR de retiro).
2. → UI: factura (mock, marcada **SIMULADA**).
3. → UI: cupón o beneficio con el texto "Muéstralo al farmacéutico". El beneficio lo define Farmaenlace.
4. Cómo se paga está **por definir** (§18).

### 7.6 Hand-off a un farmacéutico humano
1. Está disponible en todo momento. Hay tres disparadores: el usuario lo pide, el producto requiere receta, o aparece un síntoma de alarma (ver §8).
2. → UI: tarjeta "Habla con un farmacéutico" con la farmacia cercana y los botones Llamar / Cómo llegar. Si hay una señal de alarma, la UI muestra en cambio una **alerta roja** de atención médica urgente (ECU 911).
3. La conversación queda resumida para que el cliente no tenga que repetir nada. El canal real está por definir; en el demo es simulado.

## 8. Farmacéutico Virtual: alcance y guardrails
**Decidido:**
- El cliente puede preguntar cualquier cosa y el asistente puede sugerir.
- **Nunca emite un diagnóstico.**
- Ante un "¿qué tomo para…?", sugiere y recomienda ver a un médico si el problema persiste.
- Debe ser flexible y no un muro de negativas. Contexto: en la permacrisis de Ecuador, mucha gente no tiene tiempo de ir al médico.
- **Los guardrails son una capa propia, no solo el prompt.** Corren antes de generar la respuesta, sobre lo que dijo el usuario y sobre los productos que devuelve el catálogo. Detectan síntomas de alarma, pedidos de diagnóstico y medicamentos con receta. Si se activan, la respuesta usa un componente fijo (alerta roja, hand-off) y no la decide el LLM.

**Propuesta — confirmar con Eric** (guardrails mínimos que mantienen esa flexibilidad):
- Solo sugiere productos **OTC / de venta libre** (el catálogo marca venta libre vs receta).
- Ante medicamentos **con receta**, no sugiere: remite al farmacéutico o a la receta médica.
- **Síntomas de alarma → recomendar atención urgente o un médico de inmediato.** Ejemplos: dolor de pecho, dificultad para respirar, fiebre alta en bebés, embarazo.
- **Antes de sugerir, pregunta siempre** por alergias y por otros medicamentos que la persona esté tomando.
- Muestra un **aviso visible**: "No reemplaza la consulta con un profesional de salud."
- Ofrece **hand-off a un farmacéutico humano** en cualquier momento (§7.6).

## 9. UI generativa: A2UI (decidido)
- **Versión: A2UI v0.9.1**, la versión estable de producción (spec cerrada). v1.0 es release candidate y v0.8 es legacy. Repo: `github.com/a2ui-project/a2ui` (antes `google/A2UI`), docs en a2ui.org.
- **Mensajes agente → cliente** (JSONL; cada uno lleva `"version": "v0.9.1"` y una sola clave): `createSurface` (surfaceId, catalogId, theme), `updateComponents` (lista plana de componentes con `id` y `component`, enlazados por id, uno con id `root`), `updateDataModel` (path JSON Pointer + value) y `deleteSurface`. **Cliente → agente:** `action` (name, surfaceId, sourceComponentId, timestamp, context) y `error`.
- **Basic Catalog (18):** Text, Image, Icon, Video, AudioPlayer, Row, Column, List, Card, Tabs, Modal, Divider, Button, CheckBox, TextField, DateTimeInput, ChoicePicker, Slider. Funciones: required, regex, length, numeric, email, formatString, formatNumber, formatCurrency, formatDate, pluralize, openUrl, and/or/not.
- **Catálogo propio:** un JSON Schema con su `catalogId` (una URI que no necesita resolver). El cliente lo anuncia en `supportedCatalogIds`. Cada surface usa un solo catálogo, así que el nuestro = Basic + componentes FV + funciones `cedulaEc` y `rucEc` (validación en el dispositivo).
- **Renderers oficiales:** React, Lit y Angular (`@a2ui/*`), Flutter (GenUI SDK); Jetpack Compose en alpha. **Svelte no tiene renderer oficial** (hay uno comunitario `svelte-a2ui` hacia v1.0 RC; no lo usamos).
- **Renderer PWA (decidido, lo más simple):** renderer Svelte mínimo propio de los componentes que usamos (Basic Catalog + catálogo FV). Sin librería comunitaria.
- El botón de micrófono, la entrada de texto y el historial son el shell de la app, no A2UI.
- `nimblersoft-web` solo es referencia: usa un formato anterior.

| Paso | Basic Catalog | Catálogo FV (custom) |
|---|---|---|
| Onboarding: pedir y validar cédula | Text, TextField (`number`, checks `required` + `cedulaEc`), Button | `cedulaEc` (función) |
| Onboarding: confirmar datos cruzados (fuera del MVP) | Card, Text, Row, Button Sí/No | — |
| Onboarding: beneficio asociado | Text, Icon | — |
| Consulta: preguntas de seguridad | Text, ChoicePicker o Row de Buttons | — |
| Consulta: sugerencias | List, Column | `ProductCard` (precio, beneficio SmartClub, stock en farmacia cercana, venta libre, "Agregar") |
| Consulta: nota de salud | — | `AvisoSalud` ("si persiste…", "no reemplaza…") |
| Consulta: sugerencia personalizada / reposición | Text, Button | `SugerenciaPersonalizada` / `Reposicion` (mensaje, producto, reservar, affordance "¿por qué me sugieres esto?") |
| Pedido: resumen | Button | `ResumenPedido` (ítems, total, cashback) |
| Retiro: elegir farmacia | List, Button (`openUrl` para Cómo llegar / Llamar) | `PharmacyCard` (distancia, horario, stock) |
| Facturación: un dato a la vez | Text, TextField (checks `required`, `email`, `regex`, `rucEc`), Button, ChoicePicker ("consumidor final") | `rucEc` (función) |
| Facturación: confirmar datos | Card, Column, Text, Button | — |
| Compra completada | Column, Text | `ConfirmacionPedido` (n.º, farmacia, QR de retiro), `FacturaMock`, `Cupon` (código + QR) |
| Hand-off | Text, Button | `HandoffCard` (resumen + farmacia) |
| Señal de alarma | — | `AlertaRoja` (urgencia, ECU 911, hand-off) |

## 10. IA y voz
- **Turno:** voz → STT → **GLiNER2.5-Decide** (intención + tool calling contra la API mock) → **guardrails** → **LLM de Bedrock** que genera la respuesta en A2UI → se valida contra el schema → TTS de la frase corta.
- **GLiNER2.5-Decide** (decidido, **en prueba**): detecta la intención y llama funciones. Alojado en AWS.
- **LLM de Bedrock** (decidido): solo genera la respuesta en el schema A2UI. El modelo está por definir. **Propuesta:** los pasos fijos del FSM (onboarding, facturación) usan plantillas A2UI sin LLM.
- **Límite de Bedrock (máx. 1 RPS, decidido):** una pequeña pausa entre llamadas encadenadas a Bedrock y reintentos con backoff exponencial ante throttling. Transcribe y Polly no cuentan para ese límite.
- **Voz (decidido, Eric 8 oct 10:38 — lo más simple):**
  - **STT: Amazon Transcribe streaming, `es-US`.** No existe locale ecuatoriano ni es-419; es-US es el locale en español con más funciones (vocabulario personalizado, modelos de lenguaje personalizados, redacción de datos). El vocabulario personalizado (en formato tabla) sirve para nombres de productos. Transcribe Medical solo existe en inglés. Prueba sintética (Polly → streaming): cédula y frase exactas, resultado final ~0,2 s después de terminar el audio; marcas (Buprex, Tempra, Finalín) bien reconocidas. Voxtral (Bedrock) fue más lento y confundió marcas, además de gastar RPS. Nova 2 Sonic es speech-to-speech y no sirve solo para transcribir.
  - **TTS: Amazon Polly, voz Lupe (es-US), motor generative**; Lupe neural si hace falta menos latencia. Alternativa masculina: Pedro.

## 11. Backend simulado: una API mock (decidido)
Todos los servicios viven detrás de **una sola API mock** con datos sintéticos:

| Servicio | Datos |
|---|---|
| CRM | Clientes, datos de facturación, consentimientos, preferencias, condiciones/enfermedades probables, productos frecuentes, arquetipo de cliente |
| Catálogo | Productos, precios, venta libre vs receta |
| Inventario | Stock por farmacia |
| Farmacias | Sucursales, ubicación, horarios |
| SmartClub / Promociones | Cashback, beneficios, cupón del onboarding |
| Pedidos | Carrito, reserva y retiro |
| Facturación | Factura mock |

**Admin liviano (decidido):** UI de solo lectura para revisar todos los registros de cada servicio mock y las últimas llamadas a la API (logs).

## 12. Componentes del sistema
- PWA (SvelteKit) con el shell de voz/chat y un **renderer A2UI Svelte mínimo propio** (Basic + catálogo FV).
- Orquestador conversacional: FSM de onboarding y facturación, GLiNER2.5-Decide, guardrails y LLM A2UI.
- API mock única (§11) + admin de solo lectura.
- Voz: Transcribe streaming (URL firmada por el backend; las credenciales nunca van al navegador) y Polly.

La arquitectura de despliegue se diseña después (orden de Eric: diseño de producto → arquitectura → MVP → prototipo → pitch).

## 13. Canales
| Canal | Descripción | Estado |
|---|---|---|
| PWA móvil | Prompt + chat + botón grande de audio. Sin formularios. Placeholder desplegado en https://main.d2bloxc35rzfqy.amplifyapp.com (AWS Amplify) | Decidido |
| Web híbrida | La web clásica más un prompt que genera la UI (referencia: nimblersoft.com) | Decidido |
| Punto de venta | QR en la farmacia con beneficio (onboarding, §7.1) | Decidido |

**Stack del placeholder:** SvelteKit 3 + Svelte 5 + Tailwind 4, PWA estática en Amplify.

## 14. Métricas
| KPI | Por qué |
|---|---|
| Frecuencia de compra SmartClub | Fidelización (el reto) |
| Ticket promedio | Valor por visita |
| Share of wallet | Compra entre marcas del grupo |
| Instalaciones nuevas de la app/PWA | Adopción de quienes hoy no usan apps |
| **+ Activación y retención** (% que canjea el cupón, % que vuelve o compra de nuevo; ventana por definir) | Evita que las instalaciones sean una métrica de vanidad |
| Tasa de aceptación de sugerencias personalizadas | Personalización que convierte |
| Tasa de reposición / recompra (desde sugerencia proactiva) | Adherencia + fidelización |

Secundaria, tomada del canvas: % de sesiones completadas por voz (inferido). Línea base: retención por marca del deck (por ejemplo, Económicas 63,37% y Medicity 49,34%).

## 15. Real vs simulado
| Componente | Demo |
|---|---|
| LLM A2UI (AWS Bedrock, máx. 1 RPS) | **Real** |
| GLiNER2.5-Decide (AWS) | **Real** (en prueba) |
| STT (Transcribe) y TTS (Polly) | **Real** (decidido) |
| Hosting PWA (AWS Amplify) | **Real** |
| Admin de solo lectura | **Real**, sobre datos simulados |
| Catálogo, stock y precios | Simulado (sintético) |
| SmartClub (socio, cashback, beneficios) | Simulado |
| Farmacias cercanas | Simulado |
| Cupones y canje | Simulado |
| Identidad (cédula, cruce de datos) | Simulado (sin datos reales; validación módulo 10 real) |
| Insights CRM (arquetipo, preferencias, condiciones probables, productos frecuentes) | Simulado (sintético) |
| Pedidos, retiro y factura | Simulado (factura marcada SIMULADA) |
| Hand-off a farmacéutico | Simulado |

AWS es la única API externa. Todo lo demás está simulado.

## 16. MVP
Orden de trabajo de Eric: diseño de producto → diseño de arquitectura → definir el MVP → prototipo → pitch. El flujo está decidido (§7).
- **Criterio MVP (decidido, Eric 8 oct 10:38):** lo más simple en cada elección abierta.
  - Voz: Transcribe streaming `es-US` + Polly Lupe (§10).
  - Renderer A2UI: Svelte mínimo propio (§9).
  - Facturación: "consumidor final" si total ≤ USD 50 c/IVA; si no, nombre + ID + email (§7.4).
- **Flujo principal:** QR → cédula (§7.1) → hablar → productos + beneficio SmartClub + farmacia cercana (§7.2) → pedido con retiro (§7.3) → facturación (§7.4) → confirmación + factura mock + cupón (§7.5). Personalización / reposición CRM cuando haya perfil (§6).

## 17. Fuera de alcance
- Diagnóstico médico y venta o sugerencia de medicamentos con receta.
- Pagos reales, emisión real de facturas al SRI y entrega a domicilio.
- Integraciones reales: SAP, VTEX/Pardux, SmartClub, FarmaPOS, identidad.
- Cualquier dato real (personal, de salud o de pago). Solo se usan datos sintéticos.
- Diseño de arquitectura en detalle (va en un documento aparte).

## 18. Preguntas abiertas
1. **Pago:** ¿se paga al retirar en la farmacia o hay un pago simulado en la app antes de la factura?
2. **Modelo de Bedrock para generar A2UI** (§9).
3. **Cruce de datos con SmartClub en un piloto:** acceso, consentimiento y protección de datos.
4. **Canal real del hand-off:** presencial, teléfono o WhatsApp.
5. **Guardrails propuestos en §8:** falta la confirmación de Eric.
6. **Beneficio cross-marca en el demo:** ¿se muestra o no (por ejemplo, otras marcas SmartClub)?
7. **Early adopters y "voz del cliente":** falta validar con mentores y sponsors (observar, no preguntar).
8. **Meta "100k socios SmartClub":** no tiene fuente. El deck dice 75.377.
9. **Reposición proactiva en el MVP:** ¿solo en el chat o también push notification de la PWA?
10. **Arquetipos sintéticos del mock CRM** para el demo: ¿cuáles 3–4?
11. **Consentimiento LOPDP** para usar "condiciones probables": ¿en el onboarding (un toque con la cédula) o en la primera sugerencia?

## 19. Decisiones registradas
- **Beneficio del QR:** promoción abierta; la define Farmaenlace (monto, tipo y quién la financia).
- **Propiedad intelectual:** el código que generemos es nuestro (confirmado por Fernando Rivera, 8 oct).
- **Onboarding:** pseudo-FSM guiado por IA; solo pide y valida la cédula (módulo 10 en dispositivo + backend). El MVP asume que no hay datos cruzados.
- **Facturación:** los datos se piden solo antes del checkout; se guardan en el CRM y en caché del dispositivo.
- **"Confirmar":** agregar al pedido y reservar para retirar en la farmacia.
- **Backend:** una API mock con 7 servicios + admin de solo lectura.
- **IA:** GLiNER2.5-Decide (intención + tool calling, en prueba) + LLM de Bedrock solo para A2UI; guardrails como capa propia; pausa + backoff por el límite de 1 RPS.
- **UI generativa:** A2UI v0.9.1 con Basic Catalog + catálogo FV.
- **Voz (Eric 8 oct 10:38):** Transcribe streaming `es-US` + Polly Lupe generative (neural si latencia). Cierra la pregunta abierta.
- **Renderer A2UI (Eric 8 oct 10:38):** renderer Svelte mínimo propio de los componentes que usamos; sin lib comunitaria. Criterio: lo más simple.
- **Facturación ≤ USD 50 c/IVA (Eric 8 oct 10:38):** ofrecer "consumidor final"; si supera, pedir nombre + identificación + email.
- **Inteligencia de cliente desde CRM (Eric 8 oct 10:38):** el mock incluye preferencias, condiciones/enfermedades probables, productos frecuentes y arquetipo; UI adaptada al arquetipo, reposición proactiva, flywheel de demanda (Diego Alarcón) y sugerencias bajo guardrails; LOPDP = consentimiento + personalización transparente (§6).
- **Criterio MVP (Eric 8 oct 10:38):** lo más simple en cada elección abierta.
