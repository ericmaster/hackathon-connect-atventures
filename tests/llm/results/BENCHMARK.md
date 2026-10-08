# Benchmark A2UI en Bedrock: 8 oct 2026 (us-east-1)

6 fixtures × modelo, ConverseStream, max 3000 tokens y ≥ 1,1 s entre llamadas. Precios on-demand de us-east-1 (aproximados). Las corridas `v1` usan `system_prompt_v1.md` y las `v2` usan `system_prompt.md`; `t02` = temperature 0.2 y `t0` = 0. `haiku-4.5-so` = Haiku 4.5 con structured outputs nativo.

| corrida | modelo | n | json | shape | allowed | required | content | no_condition | no_leak | otc | red_flag | ALL | lat s | TTFT s | out tok | USD/llamada |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1-t02 | haiku-4.5 | 12 | 100% | 100% | 100% | 83% | 100% | 100% | 100% | 100% | 100% | 83% | 4.4 | 0.82 | 522 | 0.00460 |
| v1-t02 | nova-2-lite | 12 | 67% | 67% | 67% | 58% | 80% | 100% | 100% | 100% | 50% | 58% | 2.0 | 0.65 | 339 | 0.00148 |
| v1-t02 | gemma-3-27b | 12 | 58% | 58% | 58% | 42% | 50% | 100% | 100% | 100% | 100% | 42% | 6.9 | 0.79 | 336 | 0.00053 |
| v1-t02 | gpt-oss-120b | 12 | 58% | 58% | 58% | 58% | 70% | 100% | 100% | 100% | 100% | 58% | 4.9 | 0.86 | 816 | 0.00074 |
| v2-t02 | haiku-4.5 | 6 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 4.2 | 0.83 | 522 | 0.00493 |
| v2-t02 | nova-2-lite | 6 | 67% | 67% | 67% | 50% | 80% | 100% | 100% | 100% | 0% | 50% | 2.1 | 0.61 | 439 | 0.00184 |
| v2-t02 | gemma-3-27b | 6 | 83% | 83% | 83% | 67% | 80% | 100% | 100% | 100% | 100% | 67% | 12.1 | 0.92 | 382 | 0.00061 |
| v2-t02 | gpt-oss-120b | 6 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 4.3 | 0.60 | 1011 | 0.00090 |
| v2-t0 | haiku-4.5 | 6 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 4.1 | 0.77 | 521 | 0.00492 |
| v2-t0 | gpt-oss-120b | 6 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 6.2 | 0.70 | 964 | 0.00087 |
| v2-so-t02 | haiku-4.5-so | 12 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 4.8 | 1.60 | 575 | 0.00621 |

Las celdas "—" no aplican al caso. `required` y `content` incluyen los componentes prohibidos del caso. Las corridas con JSON inválido fallan todos los chequeos estructurales.

## Hallazgos
- **El error dominante es JSON mal cerrado** (llaves de más o de menos al final de un `updateComponents` largo con `action` anidadas). En v1: Nova 2 Lite 4/12, Gemma 3 27B 5/12 y gpt-oss-120b 5/12; Haiku 4.5, 0/12. El prompt v2 (**un `updateComponents` por componente**: líneas cortas, y además da render progresivo) los corrige en gpt-oss y los reduce en Gemma, pero Nova sigue fallando.
- **Haiku 4.5 v1** armó `ResumenPedido` con Text/Row (2/2). La tabla "step → componente" del prompt v2 lo corrige.
- **Nova 2 Lite ante una alarma** pone `AlertaRoja`, pero igual sugiere Ibuprofeno con `ProductCard` (2 de 3 corridas). Es un fallo de seguridad. También inventó un `mapsUrl`. A veces no manda `usage` en el stream (0/0 tokens).
- **Gemma 3 27B**: la latencia es muy variable (2,5–30 s) y en v2 omitió `PharmacyCard`.
- **gpt-oss-120b**: emite bloques `reasoningContent` que se pagan como salida (~2× tokens) y nunca usa ``````. Funciona bien con el prompt v2.
- **no_condition**: 0 afirmaciones reales en ~110 respuestas. La regex sin filtro solo encontró falsos positivos ("Aquí tienes opciones", "si lo tienes disponible", "Tienes un beneficio…").
- **Throttling**: hubo 4 reintentos en Haiku (perfil us.) a pesar del espacio de 1,1 s, y el backoff los resolvió todos.

## Cómo se invoca cada modelo (Converse/ConverseStream funcionan en todos)
| Modelo | ID | Nota |
|---|---|---|
| Claude Haiku 4.5 | `us.anthropic.claude-haiku-4-5-20251001-v1:0` (o `global.`) | Solo inference profile. Envuelve la salida en ```` ```jsonl ```` aunque el prompt lo prohíba. |
| Amazon Nova 2 Lite | `us.amazon.nova-2-lite-v1:0` (o `global.`) | Solo inference profile. También usa ```` ``` ````. |
| Gemma 3 27B | `google.gemma-3-27b-it` | On-demand con el ID base. Acepta el system prompt. |
| gpt-oss-120b | `openai.gpt-oss-120b-1:0` | On-demand. Devuelve `reasoningContent` antes del texto. |
| Claude Haiku 5.5 | `us.anthropic.claude-haiku-5-5` / `global.` | Solo inference profile (el ID base da "on-demand throughput isn't supported"). **Rechaza `temperature`** ("deprecated for this model"). **En la cuenta del evento: AccessDeniedException por *private marketplace eligibility***; `get-foundation-model-availability` → `agreementAvailability: NOT_AVAILABLE`. No se pudo medir. |

## Structured outputs (Haiku 4.5)
Bedrock lo soporta (`outputConfig.textFormat` `json_schema` en Converse), con límites:
- Un JSON Schema no expresa JSONL: el modelo devuelve `{"messages":[...]}` y `structured.py` lo pasa a JSONL. Se pierde el render progresivo línea por línea.
- Las restricciones del schema rechazaron el catálogo tipado: `additionalProperties` tiene que ser `false` en todo objeto, hay un máximo de 24 parámetros opcionales (la unión plana de props tenía 58) y una variante por componente da "compiled grammar is too large" (solo compilan ≤ 5 variantes).
- Lo que funcionó: el schema fija el sobre + `id` + `component` (enum del catálogo) y las props van como **string JSON** en `props`. Resultado: 12/12, pero con +26% de costo (≈ $0,0062 vs $0,0049, por el schema en el input y el escape) y un TTFT útil peor (1,6 s).
