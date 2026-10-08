<!-- Generado por opencode (openai/gpt-6.1-sol#medium), agente plan (solo lectura), --standalone. -->
<!-- Timestamp: 2026-10-08 12:26 -05 (UTC-5). Texto final del planner, verbatim. -->

# Plan ejecutable — MVP antes de 14:45; freeze 15:45
**Ventana: 12:25–14:45, 140 min. Prioridad: PWA completa; web híbrida solo reutilizando.** No se editaron archivos.

## 1. Base y decisiones
- `app/`: shell PWA, service worker y tarjetas existentes; `mock/assistant.ts` responde texto fijo. Faltan FSM, acciones y A2UI.
- `web/`: landing híbrida funcional, tarjetas duplicadas y streaming/voz simulados. No construir otro motor.
- `infra/gliner/`: Lambda privada existente; conservar contenedor/pesos. Clasifica y extrae, **no ejecuta acciones**.
- Reutilizar `tests/llm/system_prompt.md`, `catalog.json` y `checks.py`; Haiku v2 obtuvo 100% en las seis fixtures, no garantiza todos los casos.
- Implementar pasos fijos con **plantillas A2UI**, y consultas con IA real; sin streaming visual del LLM inicialmente: validar toda la respuesta antes de mostrarla (SPEC §9–10).
- Aplicar conservadoramente los mínimos propuestos de §8: OTC, alergias/otros medicamentos, aviso y hand-off; confirmar alcance en los primeros 10 min.

## 2. Arquitectura AWS: una API, una Lambda nueva
**Amplify estático → API Gateway HTTP API con JWT → Lambda Python → DynamoDB + GLiNER + Bedrock/Polly.**
- **Autenticación:** Cognito User Pool, cliente público sin secreto, Hosted UI con Authorization Code + PKCE; navegador envía access token con scope de API.
- Cuenta sintética de demo creada por operador; autorregistro deshabilitado. Login técnico una vez antes de presentar, **no sustituye ni añade datos al onboarding QR+cédula** (§7.1).
- La cédula **no autentica**: solo identifica el perfil sintético. No publicar contraseña ni incrustar claves/API keys en JS; CORS no es autenticación.
- URL Amplify pública; invocaciones reales protegidas. Sin sesión, mostrar acceso a demo o modo local **SIMULADO**, nunca abrir endpoints anónimos con gasto AWS.
- JWT obligatorio en todas las rutas funcionales; CORS limitado a ambas URLs Amplify. `/admin` exige grupo Cognito `admin`, comprobado también en Lambda.
- **Sin App Runner, sin VPC ni microservicios.** GLiNER sigue sin URL; acceso por `lambda:InvokeFunction`. Si se usara Function URL, exclusivamente `AWS_IAM`.
- Lambda Python empaqueta orquestador, API mock y validador existente; DynamoDB privado guarda perfiles, consentimiento, sesiones, pedidos y logs (§11–12).
- Una tabla, datos agrupados por propietario autenticado + sesión demo; fixtures estáticas de catálogo/farmacias. Nunca confiar en `sessionId` sin comprobar propiedad.
- IAM mínimo: GLiNER concreta, tabla concreta, Polly, Transcribe y perfil/modelos Bedrock necesarios para inferencia cross-region; recursos etiquetados.
- Rutas mínimas: `POST /session`, `/turn`, `/action`, `/voice/stt-url`, `/voice/tts`, `/demo/reset`; `GET /admin/{service}`, `/admin/logs`.
- Respuestas: `{sessionId,state,revision,messages,spokenText,mode}`; `messages` contiene A2UI v0.9.1.
- Transcribe: backend entrega **URL WebSocket SigV4 temporal**; navegador captura micrófono, convierte a PCM16 mono y envía AWS EventStream con `es-US`; mostrar parciales y enviar solo transcript final (§10, §12).
- Polly: backend sintetiza frase breve validada, Lupe generative — neural si tarda—; devuelve audio para reproducir tras interacción. Sin credenciales AWS en navegador.
- Limitar texto, audio, duración, frecuencia y tamaño; no guardar audio ni URLs firmadas en logs. SW cachea shell/assets, **no tokens ni respuestas API**.
- Serializar backend inicialmente con concurrencia reservada 1; temporizador persistente entre llamadas Bedrock **≥1,1 s**. Tests y demo nunca simultáneos.
- A2UI inválido: un reintento; throttling: máximo dos reintentos con backoff/jitter, siempre dentro del presupuesto HTTP. Después, **fail closed**, sin efectos (§7.7).
- GLiNER frío (~30 s; primer despliegue puede tardar más) excede el presupuesto HTTP: calentarlo por invocación directa antes de aceptar demo.

## 3. Contrato funcional mínimo
- FSM servidor: QR/saludo → cédula → consentimiento → consulta/seguridad → productos → farmacia → resumen → facturación → confirmación (§7.1–7.5).
- Módulo 10 en dispositivo y servidor; tercera cédula inválida ofrece hand-off; válida sin CRM crea perfil sintético (§7.1, §7.7).
- Consentimiento guarda booleano+timestamp; rechazo permite continuar **sin arquetipo, reposición ni contexto personalizado** (§6.5).
- Turno libre: GLiNER → guardrails propios → dispatcher de **lecturas** → contexto permitido → Haiku 4.5 → validación → A2UI/TTS (§10).
- Filtrar condiciones probables en servidor; no enviarlas al navegador. Al LLM llegan hábitos y productos permitidos, no condiciones sensibles (§6, §8).
- Guardrails examinan texto original y extracción; alarma/receta/diagnóstico producen UI fija. Alarma bloquea comercio y muestra ECU 911 (§7.6, §8).
- `action` exige nombre permitido, revisión vigente y confirmación explícita; servidor recalcula precios, stock, beneficios y vuelve a comprobar guardrails.
- Reserva idempotente: transacción única guarda pedido+factura mock+cupón aplicado; doble toque no duplica ni consume dos veces (§7.3–7.5).
- Facturación conversacional: ≤$50 con IVA ofrece consumidor final+email; >$50 pide nombre+ID+email faltantes; confirmar tarjeta, sin dirección/teléfono (§7.4).
- Pago al retirar; factura visible **SIMULADA**, QR de retiro, cupón primera reserva y cashback doble para reposición (§6.2, §7.5).
- **Reset:** cancelar solicitudes/audio, limpiar chat/carrito/caché FV y crear nueva sesión sembrada; restaurar cupón y perfiles solo en ese sandbox, nunca reset global (§7.8).

## 4. Fases, responsables y definición de hecho
**A = backend/AWS; B = PWA/A2UI; C = voz/QA/entrega.** Con dos agentes, C pasa a B después del renderer; recortar web y TTS antes de comprometer el flujo.

| Hora / duración | Tarea y responsable | Dependencia | Hecho verificable |
|---|---|---|---|
| 12:25–12:35 / 10 min | Contrato, fixtures Cuidador/Práctico, acciones y permisos — A+B+C | Ninguna | Contrato acordado; permisos Cognito/API/Dynamo/Bedrock/voz comprobados; alcance §8 confirmado |
| 12:35–13:00 / 25 min | API protegida, Cognito, Lambda y tabla — A | Contrato | Amplify llama ruta con JWT; sin token devuelve 401; GLiNER solo invocable por IAM |
| 12:35–13:00 / 25 min | Renderer base y adaptación de tarjetas — B | Contrato | Renderiza fixtures JSONL, bindings y eventos; rechaza componentes desconocidos |
| 12:35–13:00 / 25 min | Cliente STT y pruebas offline — C | Contrato | Captura PCM/EventStream preparada; tests del validador pasan; texto siempre disponible |
| 13:00–13:20 / 20 min | Siete servicios mock y persistencia — A | API/tabla | CRM, catálogo, inventario, farmacias, SmartClub, pedidos y factura consultables; checkout idempotente probado |
| 13:00–13:35 / 35 min | FSM visual, componentes faltantes y reset — B | Renderer | Recorrido entero con transporte fake; factura, confirmación, hand-off y alerta; reset restaura fixtures |
| 13:00–13:35 / 35 min | STT/Polly autenticados + admin read-only — C | API; mocks para admin | Voz real reconoce cédula/frase; reproduce audio; admin muestra siete servicios/logs y no ofrece escrituras |
| 13:20–13:45 / 25 min | FSM servidor, guardrails, dispatcher y Haiku — A | Mocks/contrato | Consulta real válida; acciones autorizadas; alarma fija sin productos; temperatura prod 0,1 |
| 13:35–14:05 / 30 min | Integración PWA y correcciones — B+C; A desde 13:45 | Piezas anteriores | QR→reserva real de extremo a extremo; consentimiento rechazado y alerta funcionan |
| 14:05–14:25 / 20 min | Suite LLM, seguridad y smoke e2e — C; A+B corrigen | Integración | Todos los checks pasan; ningún efecto ante JSON inválido/alarma; builds y checks Svelte pasan |
| 14:25–14:40 / 15 min | Deploy Amplify, warm-up y ensayo — A+B+C | Gates anteriores | URL publicada funciona en móvil limpio; reset y dos arquetipos demostrables |
| 14:40–14:45 / 5 min | Buffer y Checkpoint 2 — Eric | Deploy | Demo estable; estado real/simulado y problemas pendientes declarados |

- Paralelizar por directorios/propiedad: A backend/infra, B frontend, C voz/admin/tests; un responsable integra y despliega.
- Compartir renderer/cliente/voz en `shared/` mediante imports de ambas apps; sin monorepo nuevo ni migración de tarjetas extensa.
- Ruta crítica: **autenticación → mocks → orquestación → integración → smoke → deploy**. No esperar voz para integrar por texto.

## 5. Gates y línea de corte
- **13:00:** si permisos/auth AWS bloquean, mantener API cerrada; priorizar Plan B local, no Function URL anónima ni secretos en frontend.
- **13:45:** si reserva completa aún no funciona, detener novedades; conectar plantillas deterministas al backend mock y terminar checkout.
- **14:05:** congelar componentes/contratos; si voz bloquea, texto primero y declarar STT/TTS pendientes. No fingir transcripciones reales.
- **14:25:** solo fixes críticos y deploy; modo de demo elegido explícitamente, sin alternancia silenciosa durante una reserva.
- Orden de recorte: web real → animaciones/streaming visual → TTS → geolocalización real → arquetipos secundarios.
- Conservar dos perfiles contrastantes y reposición simple si es posible (§6.1–6.2); ubicación desconocida se pregunta, distancia sintética etiquetada.
- **Plan B:** mismo renderer/FSM, fixtures y A2UI determinista local; recorrido completo, alerta, factura/cupón/reset. Badge “IA y servicios simulados”.
- Nunca recortar consentimiento, guardrails, confirmación explícita, email obligatorio, idempotencia ni etiqueta de factura mock.

## 6. Pruebas y operación de demo
- Offline: `python3 -m unittest tests/llm/test_checks.py`; agregar fixtures de consentimiento rechazado, facturación >$50 y acción bloqueada.
- Bedrock: `FV_LLM_MODEL=haiku-4.5 FV_LLM_TEMPERATURE=0 python3 -m unittest tests/llm/test_consistency.py -v`.
- Producción: perfil `us.anthropic.claude-haiku-4-5-20251001-v1:0`, prompt v2, **0,1**; modelo configurable, no intentar upgrades durante integración (§10).
- Validación adicional al schema: productos/precios/URLs coinciden con contexto, acciones permitidas y componentes correctos; regex del benchmark no reemplaza guardrails.
- Smoke: QR+cupón; cédula inválida/nueva; consentimiento sí/no; Cuidador vs Práctico; reposición/“por qué”; ambos umbrales de factura.
- Smoke crítico: farmacia sin stock, doble confirmar, token ausente/otra sesión, alarma antes del checkout, mic bloqueado, throttling, JSON inválido y reset.
- `npm run check` y build en `app/`; en `web/` si se modifica. Probar instalación PWA y actualización del SW en teléfono real.
- Warm-up GLiNER a **14:20 y 14:35**, luego cada ~5 min durante la espera; invocaciones directas seriales con timeout 300 s y `AWS_MAX_ATTEMPTS=1`.
- Registrar `cold`, `ms` y latencia; los pings no garantizan retención. Evitar despliegues GLiNER y concurrencia nueva antes de presentar.
- Primera UI A2UI visible <10 s con plantilla; consulta real caliente objetivo <10 s (§5). No ejecutar suite Bedrock durante ensayo/demo.

## 7. Entregables hasta freeze
- **14:45:** Checkpoint 2 con PWA pública operativa, flujo completo y rama roja; admin autenticado y modo real/simulado explícito.
- **14:45–15:05:** web híbrida solo si reutilizar cliente/renderer toma ≤20 min; si no, conservar prototipo etiquetado y enlazar PWA.
- **15:05–15:20:** repo público bajo `ericmaster`; autenticar `gh` temprano, revisar historial/secretos y excluir credenciales/datos privados.
- **15:20:** PPT breve: problema, flujo/demo, arquitectura, diferenciador CRM/GenUI, KPIs y real vs simulado; declarar código, libs, IA y referencias.
- **15:20–15:35:** publicar URLs/repo/PPT, ensayo de 3 min y captura de respaldo; actualizar progreso y `updated_at` durante ejecución.
- **15:35:** último smoke + warm-up; **15:45 freeze absoluto**, sin incorporar funcionalidades nuevas.
