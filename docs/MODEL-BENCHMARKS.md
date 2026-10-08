# Benchmarks públicos: LLM de Bedrock para generar A2UI

Consultado el 8 oct 2026. Uso: el LLM genera JSON de UI (A2UI v0.9.1, Basic Catalog + catálogo FV) que sigue un schema, en español, con temperatura baja y baja latencia.

> **La evidencia principal es nuestro benchmark A2UI (`tests/llm`), que corre aparte.** Este documento solo resume datos públicos. Ningún benchmark público mide "JSON A2UI válido en español".

Convenciones: "no listado" = el modelo no aparece en ese benchmark. **[V]** = dato reportado por el fabricante; **[I]** = dato independiente. Los IDs de fuente [S#] están al final.

## 1. BFCL V4 (function calling) [I]

Fuente: [S1] y [S2], leaderboard oficial con **Last Updated 2026-04-12** (commit `f7cf735`, `bfcl-eval==2025.12.17`). Columnas: Overall; Non-Live AST (una llamada, chequeo de schema/argumentos: es lo más parecido a nuestro caso); Live AST; Multi-turn; latencia media del harness.

| Modelo (modo) | Rank /109 | Overall | Non-Live AST | Live | Multi-turn | Lat. media (s) |
|---|---|---|---|---|---|---|
| Claude Sonnet 4.5 (FC), referencia | 2 | 73.24% | 88.65% | 81.13% | 61.37% | 4.31 |
| **Claude Haiku 4.5 (FC)** | 6 | **68.70%** | 86.50% | 78.68% | 53.62% | **1.68** |
| Qwen3-235B-A22B-Instruct-2507 (Prompt) | 23 | 52.15% | 90.33% | 78.68% | 44.62% | 2.56 |
| mistral-large-2411 (FC)¹ | 46 | 38.37% | 84.65% | 81.87% | 14.12% | 2.04 |
| Gemma-3-27b-it (Prompt) | 69 | 29.47% | 87.17% | 74.54% | 10.75% | 10.88 |
| **Amazon Nova 2 Lite (FC)** | 80 | **27.10%** | 86.96% | 80.83% | 2.12% | 8.55 |
| Amazon Nova Pro v1 (FC) | 88 | 24.97% | 86.58% | 78.53% | 1.88% | 2.25 |
| Claude Haiku 4.5 (Prompt) | 87 | 25.26% | 55.42% | 52.48% | 1.75% | 3.75 |

- No listados: Claude Sonnet 5.5, Claude Haiku 5.5, gpt-oss-120b/20b, Mistral Large 3 y Gemini 3.8 Flash.
- ¹ Es Mistral Large 2411, no Mistral Large 3, que es el que está en Bedrock.
- **Caveat Nova 2 Lite:** Amazon reporta **60.3%** BFCL v4 Overall [V][S5, tabla 2], frente a 27.10% en el leaderboard oficial. La diferencia viene casi toda del multi-turn (2.12%), lo que sugiere un problema del harness o de la configuración. En single-turn (Non-Live AST) los cinco candidatos quedan entre 86.5% y 90.3%: **BFCL no discrimina para una sola generación estructurada**.

## 2. Structured output / JSON schema

| Benchmark | Haiku 4.5 | Nova 2 Lite | Gemma 3 27B | Sonnet 5.5 | gpt-oss | Gemini 3.8 Flash |
|---|---|---|---|---|---|---|
| JSONSchemaBench [S6] (feb 2025) | no listado | no listado | no listado | no listado | no listado | no listado |
| OpenMark "JSON Generation", ago 2026 [S7] | 100% (231/231, ±0) | no listado² | no listado² | no listado² | no listado² | no listado² |
| Structured outputs nativo en Bedrock (`bedrock-runtime`) [S8] | **Sí** | **No** | Sí | No | Sí (120b) | n/a (no está en Bedrock) |

- JSONSchemaBench evalúa motores de decodificación restringida (Guidance, Outlines, XGrammar, OpenAI, Gemini) con Llama-3.x, no estos modelos.
- OpenMark: **evidencia débil**. Son 10 tests con 2 runs, ponderación Fibonacci (los 2 tests más difíciles pesan el 62%), configuración por defecto y un sitio comercial. ² En el texto de la página no aparece; la tabla completa no se revisó. En el mismo test, Claude Sonnet 5 sacó 33%.
- Structured outputs: según las tablas de features de las model cards de Bedrock (Haiku 5.5 tampoco lo soporta). Ver la conclusión.

## 3. Instruction following

**IFBench** (AllenAI, 58 restricciones fuera de dominio). Fuente: [S3], Artificial Analysis (AA), evaluación independiente [I]. Es un dato por modelo en la página de AA; ya no forma parte del Intelligence Index v4.3.2.

| Modelo (variante AA) | IFBench [I] | Vendor [V] |
|---|---|---|
| Claude Haiku 4.5 (sin razonamiento) | 42.0% | — |
| Claude Haiku 4.5 (razonamiento) | 54.3% | 54.3% IF-Bench (citado por Amazon) [S5] |
| Nova 2 Lite (sin razonamiento) | 40.5% | 70.8% IF-Bench, prompt loose [S5]³ |
| Gemma 3 27B Instruct | 31.8% | IFEval 90.4 [S9] |
| gpt-oss-120b (high) | 69.0% | — |
| gpt-oss-20b (high) | 65.1% | — |
| Qwen3 235B A22B 2507 Instruct | 46.1% | — |
| Mistral Large 3 | 36.2% | — |
| Nova Pro / Nova Lite (v1) | 38.1% / 34.1% | — |
| Claude Sonnet 5.5, Haiku 5.5, Gemini 3.8 Flash | no listado | — |

- ³ Amazon no indica el nivel de razonamiento en la tabla; Nova 2 es un modelo de "extended thinking". No es comparable con el 40.5% sin razonamiento.
- IFEval (Gemma, [V]) es un benchmark más viejo y saturado; no es comparable con IFBench.

## 4. Tool use agéntico: τ²-bench

| Modelo | τ²-Bench Telecom, AA [I][S3] | Vendor [V] |
|---|---|---|
| Claude Haiku 4.5 (sin razonamiento) | 32.5% | — |
| Claude Haiku 4.5 (razonamiento) | 54.7% | Retail 83.2 / Airline 63.6 / Telecom 83.0 [S10]⁴ |
| Nova 2 Lite (sin razonamiento) | 62.0% | Telecom 76.0 / Retail-Verified 76.5 / Airline-Verified 64.8 [S5] |
| Gemma 3 27B | 10.5% | — |
| gpt-oss-120b (high) / 20b (high) | 65.8% / 60.2% | — |
| Qwen3 235B 2507 Instruct | 33.3% | — |
| Mistral Large 3 | 24.6% | — |
| Nova Pro / Nova Lite (v1) | 14.0% / 17.5% | — |
| Sonnet 5.5, Haiku 5.5, Gemini 3.8 Flash | no listado | — |

- Leaderboard oficial τ²-bench (taubench.com, tab "Standard") [S11]: **ninguno de nuestros candidatos está listado** (solo hay 8 entradas, p. ej. Claude Sonnet 4.5 con 76.4%).
- ⁴ Anthropic: extended thinking de 128k y un "prompt addendum" en las políticas Airline/Telecom. No es comparable con AA.
- Mide conversación multi-turno con herramientas, que no es nuestro caso (en A2UI el dispatch es determinista, §10 del SPEC). Sirve solo como indicador general.

## 5. Multilingüe / español

| Modelo | Dato | Tipo |
|---|---|---|
| Claude Haiku 4.5 | MMMLU 83.0% (14 idiomas no ingleses, 128k thinking) [S10] | [V] |
| Gemma 3 27B IT | Global-MMLU-Lite 75.1; WMT24++ 53.4 [S9, tabla 18] | [V] |
| Nova 2 Lite | No reporta benchmark de texto multilingüe (solo ASR/TTS en español) [S5] | — |
| gpt-oss-120b (high) | AA Multilingual Index, **español 87.2%** [S12] | [I] |
| Otros (Haiku, Nova, Gemma, Sonnet 5.5, Gemini 3.8 Flash) | En AA no se pudo extraer: la página solo trae el top preseleccionado | — |

- Ningún dato público mide la generación de JSON en español; esto lo cubre nuestro benchmark.

## 6. Latencia, throughput y precio

Fuente: [S4], páginas de providers de AA, fila **Amazon Bedrock** [I]. Mediana con prompt de 10k tokens de entrada; "Total" = segundos hasta recibir 500 tokens de salida (incluye el razonamiento). Precios en USD por 1M tokens (entrada/salida).

| Modelo (variante) | t/s | 1er chunk (s) | Total 500 tok (s) | Precio Bedrock | Fuente precio |
|---|---|---|---|---|---|
| **Claude Haiku 4.5 (sin razonamiento)** | 100 | **0.79** | 5.80 | $1.00 / $5.00 | AA [S4] |
| **Nova 2 Lite (sin razonamiento)** | **166** | 1.10 | **4.12** | $0.30 / $2.50 | AA [S4] |
| Gemma 3 27B | 66 | 1.51 | 9.03 | $0.23 / $0.38 | AWS price list us-east-1 [S13] |
| Mistral Large 3 | 134 | 1.34 | 5.07 | $0.50 / $1.50 | AA [S4] |
| Qwen3 235B 2507 Instruct | 74 | 1.22 | 8.00 | — | — |
| gpt-oss-120b (high) | 68 | 1.04 | 37.68 (29.31 de razonamiento) | $0.15 / $0.60 | [S13] |
| gpt-oss-20b (high) | 141 | 49.06 | 66.77 | $0.07 / $0.30 | [S13] |
| Claude Sonnet 5.5 (Low) | 103 | 1.35 | 6.21 | $2.00 / $10.00 | AA [S4] |
| Claude Sonnet 5.5 (Max, default de AA) | 133 | 482.47 | 486.24 | $2.00 / $10.00 | AA [S4] |
| Claude Haiku 5.5 (Max) | AA no tiene datos de Bedrock (Anthropic API: 242 t/s, 432 s) | — | — | $0.10 / $0.50 (prompts ≤100k) | Anthropic [S14] |
| Gemini 3.8 Flash (High), **no está en Bedrock** | 125 (Google) | 24.33 | 28.32 | $0.75 / $3.75 (Google) | AA [S4] |
| Gemini 3.8 Flash (Low) | sin datos de rendimiento | — | — | $0.75 / $3.75 | AA [S4] |

- Los precios de Claude y Nova son los de "Amazon" según AA; el AWS price list público (publicado el 6 oct 2026) no incluye los modelos de Marketplace. Verificar en https://aws.amazon.com/bedrock/pricing/.
- AA mide sin razonamiento cuando la variante existe. En nuestro caso (temperatura baja, respuesta corta) hay que **apagar el razonamiento**: con razonamiento, Sonnet 5.5, Haiku 5.5 y gpt-oss se van a decenas o cientos de segundos.
- Para comparar: AA Intelligence Index v4.3.2 (general, no específico): Haiku 4.5 15* (sin razonamiento) / 17; Nova 2 Lite 9*; Gemma 3 27B 5; gpt-oss-120b 12; Sonnet 5.5 36 (Low) / 56 (Max); Gemini 3.8 Flash 33 (Low) / 41 (High). (*estimado por AA)

## 7. Gemini 3.8 Flash (pedido por Eric)

No está en Bedrock (SPEC §19). Datos públicos: AA Intelligence Index 41 (High) / 33 (Low); τ³-Banking (AA) 44.9% (High) / 33.2% (Low); $0.75/$3.75; en High, 24.33 s al primer token [S4]. En BFCL, IFBench, τ²-Telecom y JSONSchemaBench aparece como **no listado**. Google publica su metodología en [S15], con benchmarks de coding/knowledge work, no de JSON.

## Conclusión

- **Lo que pide A2UI:** una sola generación de JSON que siga el schema, en español y rápida. Los benchmarks públicos más cercanos son BFCL Non-Live AST e IFBench; τ² y el BFCL multi-turno miden otra cosa.
- **Claude Haiku 4.5 (sin razonamiento) es el que respaldan los datos públicos como default:**
  - Es el mejor BFCL v4 Overall de los candidatos baratos (68.70%, puesto 6) y tiene la menor latencia media del harness (1.68 s).
  - Tiene el menor tiempo al primer chunk en Bedrock (0.79 s). Esto importa si renderizamos A2UI por streaming.
  - Es el único de los dos finalistas con **structured outputs nativo en Bedrock**, que garantiza el schema por decodificación.
  - En OpenMark JSON sacó 100% (evidencia débil).
  - Su debilidad es el precio frente a Nova 2 Lite: 3.3× en input, 2× en output y 1.5× en el precio blended de AA.
- **Nova 2 Lite es la alternativa rápida y barata:**
  - Throughput de 166 t/s y 4.12 s por 500 tokens, frente a 5.80 s de Haiku. Precio de $0.30/$2.50.
  - IFBench parecido a Haiku 4.5 sin razonamiento (40.5% vs 42.0%) y mejor τ²-Telecom (62.0% vs 32.5%).
  - En contra: el BFCL oficial (27.10%) contradice el 60.3% que reporta Amazon, y la model card de Bedrock **no lista structured outputs**, así que la validez del JSON depende del prompt más el reintento (§7.7).
- **Se descartan con lo que hay:**
  - **Gemma 3 27B:** el más bajo en IFBench (31.8%) y τ² (10.5%), y el más lento en Bedrock (9.03 s).
  - **gpt-oss:** buen IFBench, pero es de razonamiento y en Bedrock tarda 37–67 s.
  - **Sonnet 5.5:** queda como techo, sin datos públicos de FC, IF ni JSON. En Low tarda 6.21 s y cuesta $2/$10.
  - **Gemini 3.8 Flash:** no está en Bedrock.
- **Nuevo, a verificar:** Claude Haiku 5.5 salió en Bedrock el 7 oct 2026 [S14][S16]. Cuesta $0.10/$0.50 y Anthropic dice que es su modelo más rápido [V]. Todavía no tiene datos públicos de FC/IF/JSON, solo se accede por perfiles geo/global y su model card **no lista structured outputs**. Conviene sumarlo a `tests/llm` si la cuenta tiene acceso.
- **Decisión:** la deciden `tests/llm` (tasa de A2UI válido, componentes correctos, guardrails y latencia p50/p95 en Bedrock). Los datos públicos solo respaldan arrancar con **Haiku 4.5 + structured outputs** y tener **Nova 2 Lite** como opción si la latencia o el costo pesan más.

## Fuentes

- [S1] BFCL V4 leaderboard (Last Updated 2026-04-12): https://gorilla.cs.berkeley.edu/leaderboard.html
- [S2] Datos crudos del mismo leaderboard: https://gorilla.cs.berkeley.edu/data_overall.csv
- [S3] Artificial Analysis, páginas por modelo (IFBench, τ²-Bench Telecom, τ³-Banking; Intelligence Index v4.3.2), consultadas el 8 oct 2026: https://artificialanalysis.ai/models/claude-4-5-haiku , /claude-4-5-haiku-reasoning , /nova-2-0-lite , /gemma-3-27b , /gpt-oss-120b , /gpt-oss-20b , /qwen3-235b-a22b-instruct-2507 , /mistral-large-3 , /nova-pro , /nova-lite , /gemini-3-8-flash , /gemini-3-8-flash-low ; metodología IFBench: https://artificialanalysis.ai/evaluations/ifbench
- [S4] Artificial Analysis, providers y comparaciones (8 oct 2026): https://artificialanalysis.ai/models/claude-4-5-haiku/providers , /nova-2-0-lite/providers , /gemma-3-27b/providers , /gpt-oss-120b/providers , /gpt-oss-20b/providers , /mistral-large-3/providers , /qwen3-235b-a22b-instruct-2507/providers , /claude-sonnet-5-5/providers , /claude-sonnet-5-5-low/providers , /claude-haiku-5-5/providers , /gemini-3-8-flash/providers , /gemini-3-8-flash-low/providers ; https://artificialanalysis.ai/models/comparisons/claude-sonnet-5-5-vs-gemini-3-8-flash-low
- [S5] Amazon Nova 2 Technical Report (PDF del 15 dic 2025), tablas 1–2: https://cdn.amazon.science/c5/3d/84514a224666b5be6de4b43ef4aa/nova-2-0-technical-report2.pdf
- [S6] JSONSchemaBench, arXiv 2501.10868v3 (feb 2025): https://arxiv.org/abs/2501.10868
- [S7] OpenMark, "Best AI for JSON Generation 2026" (agosto 2026): https://openmark.ai/best-ai-for-json-generation
- [S8] Model cards de Bedrock (features de `bedrock-runtime`): https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-haiku-4-5.html , …-amazon-nova-2-lite.html , …-google-gemma-3-27b-pt.html , …-openai-gpt-oss-120b.html , …-anthropic-claude-sonnet-5-5.html , …-anthropic-claude-haiku-5-5.html
- [S9] Gemma 3 Technical Report, arXiv 2503.19786 (mar 2025), tablas 6 y 18: https://arxiv.org/abs/2503.19786
- [S10] Anthropic, "Introducing Claude Haiku 4.5" (15 oct 2025), tabla de benchmarks: https://www.anthropic.com/news/claude-haiku-4-5
- [S11] τ-bench leaderboard oficial, τ²-bench Standard (8 oct 2026): https://taubench.com/leaderboard?benchmark=core
- [S12] AA Multilingual, español (8 oct 2026): https://artificialanalysis.ai/models/multilingual/spanish
- [S13] AWS Price List API, Amazon Bedrock us-east-1 (publicationDate 2026-10-06), tier Standard: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonBedrock/current/us-east-1/index.json
- [S14] Anthropic, "Claude Haiku 5.5" (7 oct 2026): https://www.anthropic.com/claude-haiku-5-5
- [S15] Google DeepMind, metodología de evals de Gemini 3.8 Flash: https://deepmind.google/models/evals-methodology/gemini-3-8-flash/
- [S16] Model card de Bedrock, Claude Haiku 5.5: https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-haiku-5-5.html
