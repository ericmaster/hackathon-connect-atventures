# Farmacéutico Virtual: especificación de producto

> Estado: borrador del 8 oct 2026. **Decidido** = acordado con Eric. **Propuesta** = falta que Eric lo confirme. **Por definir** = no está decidido.
> Fuentes: `PITCH.md`, `services/dashboard/canvas.json`, `services/dashboard/value-prop.json` y `docs/DRIVE-SUMMARY.md`.

## 1. Resumen
El Farmacéutico Virtual es un asistente de Farmaenlace al que le hablas o le escribes y que **arma en el momento la pantalla que necesitas**: productos, la farmacia más cercana y tu beneficio SmartClub, sin catálogos ni formularios. Está pensado para los clientes que hoy evitan las apps y la web. Entran por un QR en la farmacia que les da un cupón y se identifican solo con su cédula.

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
- Es **audio-first**: un botón grande para hablar. Escribir es la alternativa.
- **No hay formularios**: los datos se piden uno a uno, dentro de la conversación.
- La misma capa sirve para la PWA móvil y para la web híbrida.
- **Regla de demo:** la UI generada tiene que verse **en los primeros 10 s**.

## 6. Flujos
Cada paso indica lo que hace el usuario y, después de "→ UI:", lo que genera la interfaz.

### 6.1 Onboarding: QR + cupón (resuelve la paradoja de adopción)
1. En la farmacia, el cliente ve un QR con la oferta: *"Descuento/bonificación en tu próxima compra solo instalando la app y mostrando tu cupón al farmacéutico, en un solo paso."* → UI: ninguna (material físico).
2. Escanea el QR y se abre la PWA, sin pasar por la tienda de apps. → UI: saludo del Farmacéutico Virtual, botón grande para hablar y la opción de instalar en la pantalla de inicio.
3. Dice o escribe su cédula, que es el único dato que se pide. → UI: un único campo numérico grande o la captura por voz.
4. Si la cédula ya está en SmartClub o en los sistemas del grupo, el resto se precarga. → UI: tarjeta con los datos para confirmar ("¿Eres …?") y botones Sí/No.
5. Si no hay datos, el sistema valida con el usuario conversando, una pregunta a la vez y sin formulario. → UI: preguntas cortas con respuesta por voz o con botones.
6. Se emite el cupón. → UI: tarjeta grande con el código/QR del cupón y el texto "Muéstralo al farmacéutico".
7. El cliente lo muestra al farmacéutico en un solo paso y el descuento se aplica en la próxima compra.

En el demo todo esto es simulado con datos sintéticos: ninguna cédula ni dato personal es real.

### 6.2 Consulta / compra conversacional
1. El usuario toca el botón y habla, por ejemplo: "algo para la gripe". → UI: la transcripción y un indicador de que el asistente está escuchando o pensando.
2. Si es una consulta de síntomas, el asistente hace preguntas mínimas de seguridad (ver §7). → UI: una pregunta con botones grandes.
3. Sugiere opciones. → UI: 1–3 tarjetas de producto con precio y beneficio SmartClub (cashback o descuento), más una nota visible: "si persiste, consulta a un médico".
4. Muestra dónde conseguirlo. → UI: tarjeta de la farmacia cercana con stock, distancia y horario, y botones "Cómo llegar" y "Llamar".
5. El usuario confirma. → UI: botón grande "Lo quiero" y luego una pantalla de confirmación con el beneficio SmartClub. Qué significa "confirmar" está **por definir** (ver §13).

### 6.3 Hand-off a un farmacéutico humano
1. Hay tres disparadores: el usuario lo pide, el producto requiere receta, o aparece un síntoma de alarma (ver §7).
2. → UI: tarjeta "Habla con un farmacéutico" con la farmacia cercana y los botones Llamar / Cómo llegar. Si hay una señal de alarma, la UI muestra en cambio un aviso destacado de atención médica urgente.
3. La conversación queda resumida para que el cliente no tenga que repetir nada. El canal real está por definir; en el demo es simulado.

## 7. Farmacéutico Virtual: alcance y guardrails
**Decidido:**
- El cliente puede preguntar cualquier cosa y el asistente puede sugerir.
- **Nunca emite un diagnóstico.**
- Ante un "¿qué tomo para…?", sugiere y recomienda ver a un médico si el problema persiste.
- Debe ser flexible y no un muro de negativas. Contexto: en la permacrisis de Ecuador, mucha gente no tiene tiempo de ir al médico.

**Propuesta — confirmar con Eric** (guardrails mínimos que mantienen esa flexibilidad):
- Solo sugiere productos **OTC / de venta libre**.
- Ante medicamentos **con receta**, no sugiere: remite al farmacéutico o a la receta médica.
- **Síntomas de alarma → recomendar atención urgente o un médico de inmediato.** Ejemplos: dolor de pecho, dificultad para respirar, fiebre alta en bebés, embarazo.
- **Antes de sugerir, pregunta siempre** por alergias y por otros medicamentos que la persona esté tomando.
- Muestra un **aviso visible**: "No reemplaza la consulta con un profesional de salud."
- Ofrece **hand-off a un farmacéutico humano** en cualquier momento (§6.3).

## 8. Canales
| Canal | Descripción | Estado |
|---|---|---|
| PWA móvil | Prompt + chat + botón grande de audio. Sin formularios. Placeholder desplegado en https://main.d2bloxc35rzfqy.amplifyapp.com (AWS Amplify) | Decidido |
| Web híbrida | La web clásica más un prompt que genera la UI (referencia: nimblersoft.com) | Decidido |
| Punto de venta | QR en la farmacia con recompensa (onboarding, §6.1) | Decidido |

**Stack del placeholder:** SvelteKit 3 + Svelte 5 + Tailwind 4, PWA estática en Amplify. La arquitectura **no está diseñada** todavía.

## 9. Métricas
| KPI | Por qué |
|---|---|
| Frecuencia de compra SmartClub | Fidelización (el reto) |
| Ticket promedio | Valor por visita |
| Share of wallet | Compra entre marcas del grupo |
| Instalaciones nuevas de la app/PWA | Adopción de quienes hoy no usan apps |
| **+ Activación y retención** (% que canjea el cupón, % que vuelve o compra de nuevo; ventana por definir) | Evita que las instalaciones sean una métrica de vanidad |

Secundaria, tomada del canvas: % de sesiones completadas por voz (inferido). Línea base: retención por marca del deck (por ejemplo, Económicas 63,37% y Medicity 49,34%).

## 10. Real vs simulado
| Componente | Demo |
|---|---|
| LLM (AWS Bedrock, máx. 1 RPS) | **Real** |
| Voz speech-to-speech (Nova 2 Sonic / Nova 2.5 Sonic) | **Real si funciona**: está disponible pero sin probar |
| Hosting PWA (AWS Amplify) | **Real** |
| Catálogo, stock y precios | Simulado (sintético) |
| SmartClub (socio, cashback, beneficios) | Simulado |
| Farmacias cercanas | Simulado |
| Cupones y canje | Simulado |
| Identidad (cédula, cruce de datos) | Simulado (sin datos reales) |
| Hand-off a farmacéutico | Simulado |

AWS es la única API externa. Todo lo demás está simulado.

## 11. MVP candidato (por definir)
Orden de trabajo de Eric: diseño de app → diseño de arquitectura → definir el MVP → prototipo → pitch. Esta sección es **solo una candidata** y no está decidida.
- **Flujo principal:** hablar → pantalla generada con productos + beneficio SmartClub + farmacia cercana → confirmar (§6.2).
- **Onboarding:** QR → cédula → cupón (§6.1).

## 12. Fuera de alcance
- Diagnóstico médico y venta o sugerencia de medicamentos con receta.
- Pagos online, checkout real y entrega a domicilio.
- Integraciones reales: SAP, VTEX/Pardux, SmartClub, FarmaPOS, identidad.
- Cualquier dato real (personal, de salud o de pago). Solo se usan datos sintéticos.
- Diseño de arquitectura (va en un documento aparte).

## 13. Preguntas abiertas
1. **Recompensa del QR:** ¿qué monto o tipo (descuento, bonificación, cashback)?
2. **¿Quién financia el cupón?** (Farmaenlace, una marca o un proveedor)
3. **"Confirmar" en §6.2:** ¿significa reserva para retiro, pedido o solo intención de compra?
4. **Modelo de voz:** ¿Nova 2 Sonic o Nova 2.5 Sonic (los dos sin probar)? ¿Alcanza con el límite de 1 RPS de Bedrock?
5. **Cruce de datos con SmartClub en un piloto:** acceso, consentimiento y protección de datos.
6. **Canal real del hand-off:** presencial, teléfono o WhatsApp.
7. **Guardrails propuestos en §7:** falta la confirmación de Eric.
8. **Beneficio cross-marca en el demo:** ¿se muestra o no (por ejemplo, otras marcas SmartClub)?
9. **Early adopters y "voz del cliente":** falta validar con mentores y sponsors (observar, no preguntar).
10. **Meta "100k socios SmartClub":** no tiene fuente. El deck dice 75.377.
11. **Propiedad intelectual:** el Acuerdo de participación **cede al patrocinador** el código y los resultados creados para el reto, mientras que las Reglas dicen que "sigue siendo tuyo". Los documentos se contradicen; asumir cesión.
