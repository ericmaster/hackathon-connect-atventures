# Farmacéutico Virtual: especificación de producto

> Estado: borrador del 8 oct 2026. **Decidido** = acordado con Eric. **Propuesta** = falta que Eric lo confirme. **Por definir** = no está decidido. **En prueba** = se está probando.
> Fuentes: `PITCH.md`, `services/dashboard/canvas.json`, `services/dashboard/value-prop.json` y `docs/DRIVE-SUMMARY.md`. Requisitos SRI: fuentes oficiales en §7.4.
> Actualizado 8 oct 12:06 con la revisión de Eric (§19). 8 oct 12:22: modelo del LLM de respuesta decidido (§10).

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
- La UI se adapta al **arquetipo del cliente** (insights CRM, §6), solo con consentimiento (§6.5).
- **Regla de demo:** la UI generada tiene que verse **en los primeros 10 s**.

## 6. Inteligencia de cliente desde CRM (decidido, innovación)
Asumimos que el CRM de Farmaenlace ya tiene insights por cliente. El mock los incluye. Sirven para personalizar la UI, reponer y sugerir — siempre bajo guardrails (§8) y **solo con consentimiento** (§6.5). Solo datos sintéticos.

**Campos del CRM mock (además de identidad y facturación):** consentimiento (booleano + timestamp), preferencias, condiciones/enfermedades probables, productos frecuentes (con ritmo de compra), arquetipo de cliente (§6.6).

**Regla dura (decidido):** el asistente **nunca asume ni afirma una condición**. La personalización se dice solo como sugerencia por comportamiento: "como sueles llevar X…". Las "condiciones probables" del CRM solo deciden **qué sugerencias se ofrecen**; **nunca se verbalizan** al usuario (tampoco en "¿por qué me sugieres esto?", que responde por comportamiento).

### 6.1 UI generativa adaptada al arquetipo (decidido, incluido)
La UI no solo cambia las sugerencias: **se adapta al arquetipo** (letra, prioridad de voz, cantidad de opciones, tipo de productos). Arquetipos del mock: §6.6.
**Momento de demo (decidido 8 oct):** **2 arquetipos contrastantes**; la misma pregunta → dos UIs distintas. Propuesta: Cuidador vs Práctico (los más opuestos de §6.6).

### 6.2 Reposición proactiva (decidido, incluido)
Solo por **ritmo de compra** de productos frecuentes; no se infiere ninguna condición. Ej.: lo compra cada mes → ~3 días antes de la fecha esperada, el asistente ofrece reservarlo en su farmacia habitual: "Sueles llevar tu multivitamínico cada mes, ¿te lo reservo en tu farmacia de siempre?". Recompra + adherencia = fidelización. **Solo en el chat** (decidido 8 oct; sin push). **Beneficio: doble cashback SmartClub** en la reposición (sintético).
→ UI: tarjeta `SugerenciaPersonalizada` / `Reposicion` con acción de reservar y affordance "¿por qué me sugieres esto?" (§9).

### 6.3 Volante (flywheel) (decidido, incluido)
Las conversaciones enriquecen el perfil CRM y generan señales de demanda para la planificación de Farmaenlace (contacto: **Diego Alarcón**, jefe de planificación de demanda).

### 6.4 Sugerencias personalizadas
Basadas en estos insights, siempre bajo guardrails (§8) y la regla dura (§6). Sin diagnóstico.

### 6.5 Privacidad y consentimiento (LOPDP Ecuador) (decidido)
Los datos de salud son sensibles → hace falta **consentimiento explícito**.
- **Mock simple:** un solo paso en el onboarding, justo después de validar la cédula (§7.1). Un toque/checkbox con el texto: "Acepto que Farmaenlace use mi historial de compras para darme sugerencias personalizadas". Se puede seguir sin aceptar.
- Se guarda en el CRM mock como booleano + timestamp.
- **Sin consentimiento:** sin personalización (ni arquetipo, ni reposición, ni sugerencias del CRM); solo respuestas genéricas.
- Incluir la explicación "¿por qué me sugieres esto?". Posicionamiento: **personalización transparente**. Solo datos sintéticos.

### 6.6 Arquetipos del mock CRM (decidido)
Nombres y descripciones del deck del reto (`docs/drive/1. Hackaton - FARMAENLACE_BYD_Reto.pdf`): audiencias de Medicity (p. 12: Cuidadores, Wellness seekers, Prácticos) y de Económicas (p. 13: Cuidadores del hogar, Resolutivos de urgencia, Ahorradores inteligentes). Perfil demo, adaptación de UI y productos frecuentes = **datos sintéticos de demo**.

| Arquetipo (fuente) | Perfil demo (sintético) | Adaptación de UI (sintético) | Productos frecuentes (sintético) |
|---|---|---|---|
| **Cuidador** (Medicity p. 12: "Cuidan de sí mismos y de quienes más les importan") | Adulto mayor que compra lo mismo cada mes | Letra extra grande, voz primero, 1–2 opciones, reposición destacada | Multivitamínico 50+ (mensual), crema humectante, pañal adulto |
| **Cuidador del hogar** (Económicas p. 13) | Mamá/papá con niños pequeños | Productos infantiles y combos | Pañales (mensual), paracetamol infantil, suero oral |
| **Práctico** (Medicity p. 12: "Quieren resolver sus necesidades de forma rápida y simple") | Joven profesional con poco tiempo | Una tarjeta con "Agregar" directo, recompra en un toque, mínimo de pasos | Antigripal, protector solar, desodorante |
| **Ahorrador inteligente** (Económicas p. 13; el deck no lo describe) | Familia de NSE medio/medio-bajo (Económicas p. 13) | Precio, cashback y promo SmartClub primero; genérico / marca propia como alternativa (deck p. 21) | Paracetamol genérico, alcohol, minimarket |

Fuera del demo: Wellness seekers y Resolutivos de urgencia.

## 7. Flujos (decidido)
Cada paso indica lo que hace el usuario y, después de "→ UI:", lo que genera la interfaz. Recorrido completo: onboarding → consulta → pedido y retiro → datos de facturación → compra completada. El hand-off está disponible en todo momento.

### 7.1 Onboarding: QR + cédula (pseudo-FSM guiado por IA)
La IA conversa, pero una máquina de estados decide el paso y no avanza hasta cumplirlo: `saludo → pedir_cedula → validar → consentimiento → buscar_crm → (confirmar_datos) → listo`.
1. En la farmacia, el cliente ve un QR con un beneficio por instalar la app. **Decidido (8 oct):** cupón de bienvenida que se aplica a la **primera reserva** (monto sintético en el demo; el real lo define Farmaenlace). → UI: ninguna (material físico).
2. Escanea el QR y se abre la PWA, sin pasar por la tienda de apps. → UI: saludo del Farmacéutico Virtual, botón grande para hablar y la opción de instalar en la pantalla de inicio.
3. El asistente pide la cédula; el usuario la dice o la escribe. **Es el único dato del onboarding.** → UI: una pregunta y un campo numérico grande (o la captura por voz).
4. Se valida el dígito verificador (módulo 10) **en el dispositivo** y otra vez **en el backend**. Si falla, la pide de nuevo sin culpar ("¿me la repites?"); al tercer intento ofrece el hand-off. → UI: aviso corto en el mismo campo.
5. **Consentimiento (mock, §6.5):** un toque/checkbox "Acepto que Farmaenlace use mi historial de compras para darme sugerencias personalizadas". Se guarda booleano + timestamp en el CRM. Sin aceptar, sigue sin personalización. → UI: texto corto + checkbox + "Continuar".
6. Busca la cédula en el CRM. **Sin perfil → se crea un perfil nuevo** (decidido 8 oct). Si hay datos cruzados, los muestra para confirmar ("¿Eres …?", Sí/No). **El MVP asume que no hay datos cruzados**: este paso se salta.
7. El cupón del QR queda asociado a la cédula en SmartClub y se aplica a la primera reserva (§7.5). → UI: "Listo, ya tienes tu beneficio" y pasa a la consulta.

**Módulo 10 (cédula):** 10 dígitos; provincia 01–24 (30 = registrados en el exterior); tercer dígito < 6; coeficientes 2-1-2-1-2-1-2-1-2 sobre los 9 primeros (si el producto pasa de 9, se resta 9); verificador = (10 − suma mód 10) mód 10. Ejemplo sintético válido: `1710034065`.

En el demo todo esto es simulado con datos sintéticos: ninguna cédula ni dato personal es real.

### 7.2 Consulta conversacional
1. El usuario toca el botón y habla, por ejemplo: "algo para la gripe". → UI: la transcripción en vivo y un indicador de que el asistente está escuchando o pensando.
2. La capa de guardrails revisa el pedido antes de generar la respuesta (§8). Si es una consulta de síntomas, hace preguntas mínimas de seguridad. → UI: una pregunta con botones grandes.
3. Sugiere opciones. → UI: 1–3 tarjetas de producto con precio, beneficio SmartClub (cashback o descuento), stock en la farmacia más cercana y el botón "Agregar al pedido". Cuando aplica, una nota visible: "si persiste, consulta a un médico".

### 7.3 Pedido y retiro
1. El usuario agrega productos. → UI: resumen del pedido (productos, cantidades, total y cashback).
2. Elige retirar en la farmacia más cercana (u otra). → UI: tarjeta de farmacia con stock, distancia y horario, y botones "Retirar aquí", "Cómo llegar" y "Llamar".
3. **Cierre MVP (decidido 8 oct):** reservar y retirar en la farmacia; **se paga al retirar**. Sin entrega a domicilio ni pago en la app (backlog, §17).
4. **Ninguna acción comercial** (agregar, reservar, facturar) se ejecuta sin pasar los guardrails (§8) y sin **confirmación explícita** del usuario (botón A2UI → `action`).

### 7.4 Datos de facturación (solo antes del checkout)
1. Antes de confirmar la reserva, si el total es ≤ USD 50 el asistente ofrece **"consumidor final"** como opción rápida y pide **solo el email** (si falta) para enviar la factura/RIDE. Si supera (o el usuario prefiere factura con datos), pide **solo los datos que falten**, una pregunta a la vez: **nombre o razón social, cédula/RUC/pasaporte y email**. **El email es obligatorio** siempre que se piden datos de facturación: toda la facturación es electrónica y la factura se entrega por email. No pide dirección ni teléfono. → UI: una pregunta y un campo grande por dato; al final, una tarjeta para confirmar.
2. Se guardan **de forma permanente en el CRM** y en **caché en el dispositivo**. La próxima vez no se piden.
3. **Requisitos SRI del comprador (verificado 8 oct con fuentes oficiales):**
   - **Obligatorios:** `tipoIdentificacionComprador` (04 RUC, 05 cédula, 06 pasaporte, 07 consumidor final, 08 exterior; se deriva, no se pregunta), `razonSocialComprador` (nombres y apellidos o razón social) e `identificacionComprador`. [F1 p. 13 y 49; F2; F3 art. 19 num. 1]
   - **Opcionales:** `direccionComprador` ("obligatorio cuando corresponda"; `minOccurs="0"` en el XSD; solo se exige en la factura comercial negociable, Anexo 11, que no aplica). Email y teléfono van en `infoAdicional/campoAdicional`, también opcional para el SRI. El email sirve para enviar la factura; sin email se entrega el RIDE. [F1 p. 49 y 109; F2; F4 preg. 16] **Nuestra regla (8 oct 12:11): el email es obligatorio** (también con consumidor final), porque la factura/RIDE se entrega por email.
   - **Dirección o sector del comprador: NO es obligatorio** → no se agrega a los datos pedidos. El art. 19 no la incluye.
   - **Consumidor final:** tipo `07`, ID `9999999999999`, leyenda "CONSUMIDOR FINAL"; solo si la transacción **no supera USD 50** y el comprador no necesita sustentar costos o gastos. [F1 p. 13; F3 art. 19 num. 1; F4 preg. 34]
   - **Desde 1 ene 2026:** una factura a consumidor final transmitida al SRI **no se puede anular** ni modificar con nota de crédito. [F5; F6]
   - ⚠️ **No confirmado:** (a) que el tope de USD 50 sea "con IVA": la norma dice "la transacción"; usamos el total con IVA (lectura conservadora). (b) Reformas al art. 19 posteriores a la compilación del SRI (RO 496, 9 feb 2024); la FAQ del SRI coincide con USD 50. (c) Que la factura a consumidor final no sirva para deducir gastos personales: se infiere porque no identifica al comprador; no se revisó la fuente.
   - Fuentes:
     - F1 Ficha técnica comprobantes electrónicos offline v2.34 (jul 2026): https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/f8d9bb36-5632-4f96-b463-b9265b55338c/FICHA%20TE%cc%81CNICA%20COMPROBANTES%20ELECTRO%cc%81NICOS%20ESQUEMA%20OFFLINE%20Versio%cc%81n%202.34.pdf
     - F2 XSD factura v2.1.0: https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/05546998-6f29-4870-be3b-62650f312a6c/XML%20y%20XSD%20Factura.zip
     - F3 Reglamento de Comprobantes de Venta, Retención y Documentos Complementarios (art. 19): https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/fc9f2c55-fc0d-41d1-a834-797b202b4d11/Reglamento_comprobantes_ventaydc_ultima%20modificacion_09022024.pdf
     - F4 Preguntas frecuentes facturación electrónica: https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/cef82829-f261-4374-a45c-96adb2c3ace8/Preguntas+frecuentes+facturaci%F3n+electr%F3nica.pdf
     - F5 Boletín SRI 033 (anulación): https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar/142630d3-569f-4cd2-a5a5-58557b7fc342/BOLET%C3%8DN%20033%20-%20SRI%20ESTABLECE%20NUEVAS%20REGLAS%20PARA%20LA%20ANULACI%C3%93N%20DE%20COMPROBANTES%20ELECTR%C3%93NICOS%20COMO%20PARTE%20DE%20SU%20ESTRATEGIA%20DE%20CONTROL.pdf
     - F6 Res. NAC-DGERCGC25-00000017 (vigencia 1 ene 2026): https://www.sri.gob.ec/o/sri-portlet-biblioteca-alfresco-internet/descargar?id=e98fc8a6-299e-4ea9-8de7-2f6c70dbb4f5&nombre=NAC-DGERCGC25-00000017.pdf
     - Índice: https://www.sri.gob.ec/web/intersri/facturacion-electronica
4. **Decidido (única regla):** total ≤ USD 50 con IVA → ofrecer "consumidor final" + email; si supera → nombre + identificación + email. Email siempre obligatorio.

### 7.5 Compra completada
1. → UI: confirmación de la reserva (número, farmacia, hora y código QR de retiro).
2. → UI: factura (mock, marcada **SIMULADA**), **emitida al confirmar** la reserva.
3. → UI: cupón de bienvenida aplicado (primera reserva) y cashback SmartClub (doble si es reposición), con el texto "Muéstralo al farmacéutico".
4. **Pago al retirar en la farmacia** (decidido 8 oct). Sin pago en la app (backlog, §17).

### 7.6 Hand-off a un farmacéutico humano
1. Está disponible en todo momento. Hay tres disparadores: el usuario lo pide, el producto requiere receta, o aparece un síntoma de alarma (ver §8).
2. → UI: tarjeta "Habla con un farmacéutico" con la farmacia cercana y los botones Llamar / Cómo llegar. Si hay una señal de alarma, la UI muestra en cambio una **alerta roja** de atención médica urgente (ECU 911).
3. La conversación queda resumida para que el cliente no tenga que repetir nada. El canal real está por definir; en el demo es simulado.

### 7.7 Casos borde (decidido 8 oct, fallback más simple)
| Caso | Fallback |
|---|---|
| Cédula válida sin perfil CRM | Crear perfil nuevo (§7.1). |
| Dato desconocido (ubicación, etc.) | El asistente lo pregunta. |
| Micrófono bloqueado | Pedir que lo habilite; la entrada de texto sigue disponible. |
| JSON A2UI inválido o throttling de Bedrock | A2UI inválido (chequeos de forma de `tests/llm`): **un reintento**. Throttling: reintento con backoff exponencial (N por definir). Si sigue fallando, **fail closed**: mensaje fijo seguro y **ninguna acción ejecutada**. |
| Cold start de GLiNER | Pings de warm-up antes del demo; por ahora se toleran demoras. |

### 7.8 Reinicio de la conversación (decidido 8 oct)
- **Demo:** botón "Reiniciar" (solo demo).
- **Producción:** la conversación se reinicia tras un periodo de inactividad (por definir); se conservan perfil, ítems del carrito y similares.

## 8. Farmacéutico Virtual: alcance y guardrails
**Decidido:**
- El cliente puede preguntar cualquier cosa y el asistente puede sugerir.
- **Nunca emite un diagnóstico.**
- **Nunca asume ni afirma una condición** (regla dura, §6): sugiere solo por comportamiento ("como sueles llevar X…"); las condiciones probables del CRM solo filtran sugerencias y nunca se verbalizan.
- Ante un "¿qué tomo para…?", sugiere y recomienda ver a un médico si el problema persiste.
- Debe ser flexible y no un muro de negativas. Contexto: en la permacrisis de Ecuador, mucha gente no tiene tiempo de ir al médico.
- **Los guardrails son una capa propia, no solo el prompt.** Corren antes de generar la respuesta y **antes de cualquier acción comercial** (que además exige confirmación del usuario, §7.3), sobre lo que dijo el usuario y sobre los productos que devuelve el catálogo. Detectan síntomas de alarma, pedidos de diagnóstico y medicamentos con receta. Si se activan, la respuesta usa un componente fijo (alerta roja, hand-off) y no la decide el LLM.

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
| Onboarding: consentimiento | Text, CheckBox, Button | — |
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
- **Turno (orden decidido 8 oct):** voz → STT → **GLiNER2.5-multi-Decide** (solo clasifica intención y extrae entidades) → **guardrails** → **dispatcher determinista propio** (solo lecturas a la API mock: catálogo, stock, farmacias, CRM) → **LLM de Bedrock** genera la respuesta en A2UI → se valida contra el schema → TTS de la frase corta. **Acciones comerciales** (agregar, reservar, facturar): solo después de guardrails + **confirmación del usuario** (`action` A2UI), y las ejecuta el dispatcher.
- **GLiNER2.5-multi-Decide** (decidido, **funciona en Lambda**: contenedor, pesos desde S3): clasifica y extrae; **no** despacha acciones. **Cold start:** pings de warm-up antes del demo; por ahora se toleran demoras.
- **Dispatch de acciones** (decidido): código determinista propio, no el modelo.
- **LLM de Bedrock** (decidido): solo genera la respuesta en el schema A2UI. **Modelo (decidido, Eric 8 oct 12:22): Claude Haiku 4.5**, vía inference profile `us.anthropic.claude-haiku-4-5-20251001-v1:0`. **Temperatura 0,1 en producción** (suena menos robótico); **0 solo en la suite de pruebas** (determinismo). El benchmark dio 100% con 0 y con 0,2.
  - **Prompt v2** de `tests/llm` (`system_prompt.md`): JSONL, **un componente por línea** (un `updateComponents` por componente). Antes de renderizar, se valida la forma con los chequeos de `tests/llm` (`checks.py`); si falla, **se reintenta una vez** y luego fail closed (§7.7).
  - **Modelo configurable por variable de entorno.** Upgrade preferido: **Claude Haiku 5.5** si los organizadores lo habilitan (hoy bloqueado por *private marketplace eligibility*; además rechaza `temperature`, así que no se envía). Fallback barato: **gpt-oss-120b** (`openai.gpt-oss-120b-1:0`; 100% con prompt v2).
  - **Descartados:** Nova 2 Lite (JSON inválido y sugiere productos ante una alarma) y Gemma 3 27B (JSON inválido, latencia muy variable). Evidencia: `tests/llm/results/BENCHMARK.md` y `docs/MODEL-BENCHMARKS.md`. Gemini 3.8 Flash **no está en Bedrock**.
  - **Propuesta:** los pasos fijos del FSM (onboarding, facturación) usan plantillas A2UI sin LLM.
- **Consistencia (requisito decidido, 8 oct):** no se exigen respuestas idénticas, sí comportamiento consistente. **Suite de pruebas** de los casos más comunes sobre contextos pre-armados (fixtures sintéticos: perfiles, carritos, estados de conversación). Verifica comportamiento, no texto exacto: JSON A2UI válido, componentes correctos, guardrails respetados, ninguna condición verbalizada (§6).
- **Límite de Bedrock (máx. 1 RPS, decidido):** una pequeña pausa entre llamadas encadenadas a Bedrock y reintentos con backoff exponencial ante throttling o A2UI inválido; tras N intentos, fail closed (§7.7). Transcribe y Polly no cuentan para ese límite.
- **Voz (decidido, Eric 8 oct 10:38 — lo más simple):**
  - **STT: Amazon Transcribe streaming, `es-US`.** No existe locale ecuatoriano ni es-419; es-US es el locale en español con más funciones (vocabulario personalizado, modelos de lenguaje personalizados, redacción de datos). El vocabulario personalizado (en formato tabla) sirve para nombres de productos. Transcribe Medical solo existe en inglés. Prueba sintética (Polly → streaming): cédula y frase exactas, resultado final ~0,2 s después de terminar el audio; marcas (Buprex, Tempra, Finalín) bien reconocidas. Voxtral (Bedrock) fue más lento y confundió marcas, además de gastar RPS. Nova 2 Sonic es speech-to-speech y no sirve solo para transcribir.
  - **TTS: Amazon Polly, voz Lupe (es-US), motor generative**; Lupe neural si hace falta menos latencia. Alternativa masculina: Pedro.

## 11. Backend simulado: una API mock (decidido)
Todos los servicios viven detrás de **una sola API mock** con datos sintéticos:

| Servicio | Datos |
|---|---|
| CRM | Clientes, datos de facturación, consentimiento (booleano + timestamp), preferencias, condiciones/enfermedades probables, productos frecuentes, arquetipo de cliente |
| Catálogo | Productos, precios, venta libre vs receta |
| Inventario | Stock por farmacia |
| Farmacias | Sucursales, ubicación, horarios |
| SmartClub / Promociones | Cashback, beneficios, cupón del onboarding |
| Pedidos | Carrito, reserva y retiro (pago al retirar) |
| Facturación | Factura mock |

**Admin liviano (decidido):** UI de solo lectura para revisar todos los registros de cada servicio mock y las últimas llamadas a la API (logs).

## 12. Componentes del sistema
- PWA (SvelteKit) con el shell de voz/chat y un **renderer A2UI Svelte mínimo propio** (Basic + catálogo FV).
- Orquestador conversacional: FSM de onboarding y facturación, GLiNER2.5-multi-Decide (clasificación/extracción), guardrails, dispatcher determinista de acciones y LLM A2UI.
- Suite de pruebas de comportamiento con fixtures sintéticos (§10).
- API mock única (§11) + admin de solo lectura.
- Voz: Transcribe streaming (URL firmada por el backend; las credenciales nunca van al navegador) y Polly.

La arquitectura de despliegue se diseña después (orden de Eric: diseño de producto → arquitectura → MVP → prototipo → pitch).

## 13. Canales
| Canal | Descripción | Estado |
|---|---|---|
| PWA móvil | Prompt + chat + botón grande de audio. Sin formularios. Placeholder desplegado en https://main.d2bloxc35rzfqy.amplifyapp.com (AWS Amplify) | Decidido |
| Web híbrida | La web clásica más un prompt que genera la UI (referencia: nimblersoft.com). Visión omnicanal de Eric. Prototipo en https://main.dfsvbpju4hwi2.amplifyapp.com (AWS Amplify) | Decidido (se mantiene, 8 oct) |
| Punto de venta | QR en la farmacia con beneficio (onboarding, §7.1) | Decidido |

**Stack del placeholder:** SvelteKit 3 + Svelte 5 + Tailwind 4, PWA estática en Amplify. PWA y web híbrida desplegadas como mocks.

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
Estado al 8 oct.

| Componente | Demo |
|---|---|
| LLM A2UI (AWS Bedrock, máx. 1 RPS) | **Real**: Claude Haiku 4.5, temperatura 0,1 (0 en tests) (§10) |
| GLiNER2.5-multi-Decide (AWS Lambda) | **Real**: funciona en Lambda (contenedor, pesos desde S3) |
| STT (Transcribe) y TTS (Polly) | **Real**: probados |
| PWA y web híbrida (AWS Amplify) | **Desplegadas** con API real (IA real, datos sintéticos); `?demo` = mock |
| Admin de solo lectura | **Real**, sobre datos simulados |
| API de Farmaenlace (7 servicios) | Simulada: API separada (Lambda + DynamoDB) que el orquestador llama por HTTP + SigV4; ver `services/farmaenlace-mock/README.md` |
| Catálogo, stock y precios | Simulado (sintético) |
| SmartClub (socio, cashback, beneficios) | Simulado |
| Farmacias cercanas | Simulado |
| Cupones y canje | Simulado |
| Identidad (cédula, cruce de datos) | Simulado (sin datos reales; validación módulo 10 real) |
| Insights CRM (arquetipo, preferencias, condiciones probables, productos frecuentes) | Simulado (sintético) |
| Pedidos, retiro y factura | Simulado (factura marcada SIMULADA) |
| Hand-off a farmacéutico | Simulado |
| Audit log de conversación | **Hecho**: tabla DynamoDB `connect-atv-data` (query en `services/api/CONTRACT.md`) |

AWS es la única API externa. Todo lo demás está simulado.

## 16. MVP
Orden de trabajo de Eric: diseño de producto → diseño de arquitectura → definir el MVP → prototipo → pitch. El flujo está decidido (§7).
- **Criterio MVP (decidido, Eric 8 oct 10:38):** lo más simple en cada elección abierta.
  - Voz: Transcribe streaming `es-US` + Polly Lupe (§10).
  - Renderer A2UI: Svelte mínimo propio (§9).
  - Facturación: "consumidor final" + email si total ≤ USD 50 c/IVA; si no, nombre + ID + email. Email siempre obligatorio (§7.4).
  - Cierre: reservar y retirar; pago al retirar; factura mock al confirmar (§7.3, §7.5).
  - Casos borde: fallback más simple de §7.7.
- **Demo:** 2 arquetipos contrastantes (§6.1); reposición solo en el chat (§6.2); botón de reinicio solo en el demo (§7.8); GLiNER caliente con warm-up (§10).
- **Calidad:** temperatura baja + suite de pruebas de comportamiento con fixtures (§10).
- **Flujo principal:** QR → cédula + consentimiento (§7.1) → hablar → productos + beneficio SmartClub + farmacia cercana (§7.2) → reserva con retiro (§7.3) → facturación (§7.4) → confirmación + factura mock + cupón (§7.5) → pago al retirar. Personalización / reposición CRM cuando haya perfil y consentimiento (§6).

## 17. Fuera de alcance
- Diagnóstico médico y venta o sugerencia de medicamentos con receta.
- Pagos reales y emisión real de facturas al SRI.
- Integraciones reales: SAP, VTEX/Pardux, SmartClub, FarmaPOS, identidad.
- Cualquier dato real (personal, de salud o de pago). Solo se usan datos sintéticos.
- Diseño de arquitectura en detalle (va en un documento aparte).

**Backlog (post-MVP, Eric 8 oct):**
- Integración con pasarela de pago (pago en la app); hoy reserva + pago al retirar.
- Entrega a domicilio.
- Canal WhatsApp (Eric 8 oct 12:34): mismo asistente/orquestador vía WhatsApp Business API.
- Diferido del MVP (decisiones 8 oct): notificaciones push de reposición (§6.2); flywheel CRM + señales de demanda implementado (§6.3); reset por inactividad en producción (§7.8); canal real del hand-off (§18.4); upgrade a Haiku 5.5 si AWS lo habilita (§10); integraciones reales (§17).

## 18. Preguntas abiertas
1. ~~**Pago**~~ **Cerrada (8 oct):** se paga al retirar; factura mock al confirmar (§7.5).
2. ~~**Modelo de Bedrock para generar A2UI**~~ **Cerrada (Eric 8 oct 12:22):** Claude Haiku 4.5, temperatura 0,1 en producción y 0 en tests; configurable por env (upgrade Haiku 5.5, fallback gpt-oss-120b) (§10).
3. **Cruce de datos con SmartClub en un piloto:** acceso, consentimiento y protección de datos.
4. **Canal real del hand-off:** presencial, teléfono o WhatsApp.
5. **Guardrails propuestos en §8:** falta la confirmación de Eric.
6. **Beneficio cross-marca en el demo:** ¿se muestra o no (por ejemplo, otras marcas SmartClub)?
7. **Early adopters y "voz del cliente":** falta validar con mentores y sponsors (observar, no preguntar).
8. **Meta "100k socios SmartClub":** no tiene fuente. El deck dice 75.377.
9. ~~**Reposición proactiva: chat o push**~~ **Cerrada (8 oct):** solo en el chat (§6.2).
10. **Periodo de inactividad** para reiniciar la conversación en producción (§7.8) y **N** de reintentos ante throttling antes del fail closed (§7.7; A2UI inválido: un reintento).

## 19. Decisiones registradas
- **Beneficio del QR:** promoción abierta; la define Farmaenlace (monto, tipo y quién la financia). En el demo: cupón de bienvenida en la primera reserva (8 oct).
- **Propiedad intelectual:** el código que generemos es nuestro (confirmado por Fernando Rivera, 8 oct).
- **Onboarding:** pseudo-FSM guiado por IA; solo pide y valida la cédula (módulo 10 en dispositivo + backend) + un toque de consentimiento. El MVP asume que no hay datos cruzados.
- **Facturación:** los datos se piden solo antes del checkout; se guardan en el CRM y en caché del dispositivo.
- **"Confirmar":** agregar al pedido y reservar para retirar en la farmacia.
- **Backend:** una API mock con 7 servicios + admin de solo lectura.
- **IA:** GLiNER2.5-multi-Decide (clasificación/extracción; el tool calling pasa al dispatcher determinista, 8 oct) + LLM de Bedrock solo para A2UI; guardrails como capa propia; pausa + backoff por el límite de 1 RPS.
- **UI generativa:** A2UI v0.9.1 con Basic Catalog + catálogo FV.
- **Voz (Eric 8 oct 10:38):** Transcribe streaming `es-US` + Polly Lupe generative (neural si latencia). Cierra la pregunta abierta.
- **Renderer A2UI (Eric 8 oct 10:38):** renderer Svelte mínimo propio de los componentes que usamos; sin lib comunitaria. Criterio: lo más simple.
- **Facturación ≤ USD 50 c/IVA (Eric 8 oct 10:38):** ofrecer "consumidor final"; si supera, pedir nombre + identificación + email.
- **Inteligencia de cliente desde CRM (Eric 8 oct 10:38):** el mock incluye preferencias, condiciones/enfermedades probables, productos frecuentes y arquetipo; UI adaptada al arquetipo, reposición proactiva, flywheel de demanda (Diego Alarcón) y sugerencias bajo guardrails; LOPDP = consentimiento + personalización transparente (§6).
- **Criterio MVP (Eric 8 oct 10:38):** lo más simple en cada elección abierta.
- **Innovación CRM (Eric 8 oct):** incluidas UI adaptada al arquetipo, reposición proactiva (solo por ritmo de compra) y conversaciones que alimentan el CRM / señales de demanda (§6.1–6.3).
- **Regla dura (Eric 8 oct):** nunca asumir ni afirmar una condición; personalizar solo por comportamiento; las condiciones probables solo filtran sugerencias, nunca se verbalizan (§6, §8).
- **Consentimiento (Eric 8 oct):** mock de un toque en el onboarding, tras validar la cédula; booleano + timestamp en el CRM; sin consentimiento, solo respuestas genéricas (§6.5, §7.1). Cierra la pregunta abierta.
- **Arquetipos del mock CRM (Eric 8 oct):** Cuidador, Cuidador del hogar, Práctico y Ahorrador inteligente, tomados del deck (Medicity p. 12, Económicas p. 13); detalles sintéticos (§6.6). Cierra la pregunta abierta.
- **Consistencia (Eric 8 oct 12:06):** LLM de respuesta con temperatura baja; suite de pruebas de comportamiento con fixtures sintéticos (A2UI válido, componentes correctos, guardrails, ninguna condición verbalizada). Requisito (§10).
- **Cold start (Eric 8 oct 12:06):** GLiNER caliente con warm-up pings antes del demo; se toleran demoras (§10).
- **Casos borde (Eric 8 oct 12:06):** cédula sin perfil → perfil nuevo; dato desconocido → se pregunta; mic bloqueado → pedir habilitarlo + texto; A2UI inválido o throttling → backoff y fail closed tras N intentos (§7.7).
- **Reinicio (Eric 8 oct 12:06):** botón solo en el demo; en producción, reinicio por inactividad conservando perfil y carrito (§7.8).
- **Facturación SRI (Eric 8 oct 12:06):** se mantiene la regla simple; verificado con fuentes del SRI que la dirección/sector del comprador no es obligatoria, así que no se pide (§7.4). Se elimina la contradicción de §7.4.
- **Cierre MVP (Eric 8 oct 12:06):** reservar y retirar; pago al retirar; factura mock al confirmar. Backlog: pasarela de pago y entrega a domicilio (§7.5, §17). Cierra la pregunta abierta.
- **Beneficio (Eric 8 oct 12:06):** el cupón de bienvenida del QR aplica a la primera reserva; la reposición da doble cashback SmartClub (sintético) (§6.2, §7.1).
- **Modelo Bedrock (Eric 8 oct 12:06):** Gemini 3.8 Flash no está en Bedrock; modelo pendiente del benchmark (Claude Haiku 4.5, Nova 2 Lite si está disponible, Gemma 3 27B) (§10).
- **Orquestación (Eric 8 oct 12:06):** GLiNER solo clasifica/extrae; el dispatch de acciones es código determinista propio; ninguna acción comercial antes de guardrails + confirmación del usuario (§7.3, §10).
- **Demo (Eric 8 oct 12:06):** 2 arquetipos contrastantes; reposición solo en el chat (cierra la pregunta del push) (§6.1, §6.2).
- **Web híbrida (Eric 8 oct 12:06):** se mantiene (visión omnicanal); prototipo en https://main.dfsvbpju4hwi2.amplifyapp.com (§13).
- **Email de facturación obligatorio (Eric 8 oct 12:11):** siempre que se piden datos de facturación (nombre + ID + email), el email es obligatorio; con consumidor final también se pide el email para enviar la factura/RIDE. Motivo: toda la facturación es electrónica y la factura se entrega por email (§7.4).
- **Modelo LLM de respuesta (Eric 8 oct 12:22):** Claude Haiku 4.5, temperatura 0,1 en producción (menos robótico) y 0 solo en la suite de pruebas, inference profile `us.anthropic.claude-haiku-4-5-20251001-v1:0`; prompt v2 de `tests/llm` (JSONL, un componente por línea); forma validada con los chequeos de `tests/llm` antes de renderizar, un reintento. Modelo configurable por env: upgrade Haiku 5.5 si lo habilitan (sin `temperature`), fallback gpt-oss-120b. Nova 2 Lite y Gemma 3 27B descartados (`tests/llm/results/BENCHMARK.md`, `docs/MODEL-BENCHMARKS.md`). Cierra la pregunta abierta (§10, §18).
- **Real vs simulado (8 oct):** GLiNER multi-Decide funciona en Lambda; Transcribe/Polly probados; PWA y web desplegadas en Amplify como mocks (§15).
