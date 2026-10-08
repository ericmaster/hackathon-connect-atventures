# farmaenlace-mock

API mock separada que simula el backend de Farmaenlace (7 servicios). La Lambda orquestadora `connect-atv-orchestrator` la llama por HTTPS + SigV4 como en producción. **Nada aquí es dato real de Farmaenlace** (precios, stock, clientes, RUC, facturas).

Código: `app.py` (rutas), `data.py` (semilla), `local_server.py` (HTTP local). Cliente: `services/api/mock.py`. Spec: `openapi.yaml`.

## AWS
| Recurso | Nombre |
|---|---|
| Lambda | `connect-atv-farmaenlace-mock` (Python 3.12, arm64) |
| DynamoDB | `connect-atv-farmaenlace` (on-demand, tag `project=connect-atventures`) |
| HTTP API | `connect-atv-farmaenlace-api` — `AWS_IAM` en toda ruta; allowlist Lambda `FM_ALLOWED_ROLES` (rol orquestador); throttle stage 50 rps / burst 100 |
| IAM | inline `farmaenlace-mock-invoke` en `connect-atv-orchestrator-role` |

Deploy: `infra/farmaenlace-mock/deploy.sh` (aditivo; `OPERATOR=1` agrega `WSParticipantRole` a la allowlist solo para verificación manual). Sin CORS ni acceso anónimo: solo servidor a servidor. `curl` sin firma → 403.

## Modelo (pk / sk)
| pk | sk | Uso |
|---|---|---|
| `CAT` | `P#<sku>` | Catálogo (RO) |
| `PHARM` | `PH#<pharmacyId>` | Farmacias (RO) |
| `INV#<pharmacyId>` | `SKU#<sku>` | Stock (RO) |
| `SEED` | `CRM#<cedula>` | Perfiles CRM semilla (RO) |
| `PROMO` | `CPNDEF#…` / `PROMO#…` | Definiciones cupón/promo (RO) |
| `SBX#<sandbox>` | `CRM#` / `CPN#` / `ORD#` / `FAC#` / `IDEM#` | Estado por sesión de demo |

**`X-Sandbox-Id`**: aísla CRM/cupones/pedidos/facturas por demo (`SBX#…`). Requerido en esas rutas.  
**`Idempotency-Key`**: obligatorio en `POST /pedidos` (`[A-Za-z0-9_-]{8,64}`); replay → 200 + `replay:true`.

## Rutas (`route()`)
| Método | Path | Params / headers | Respuesta |
|---|---|---|---|
| GET | `/health` | — | `{ok, service, products}` |
| GET | `/catalogo/productos` | `q`, `incluir_receta`, `limit` | `{items, count}` |
| GET | `/catalogo/productos/{sku}` | — | producto \| 404 |
| GET | `/farmacias` | `lat`, `lng` | `{items, count}` (+ `distance_m`, `mapsUrl`) |
| GET | `/farmacias/{id}` | `lat`, `lng` | farmacia \| 404 |
| GET | `/inventario` | `skus` (csv) | `{stock: {pharmacyId: {sku: n}}}` |
| GET | `/inventario/{id}` | — | `{pharmacyId, stock}` |
| GET | `/inventario/{id}/{sku}` | — | `{pharmacyId, sku, stock}` |
| POST | `/crm/clientes` | `X-Sandbox-Id`; body `{cedula, name?}` | 201 cliente |
| GET | `/crm/clientes/{cedula}` | `X-Sandbox-Id` | `{cliente, origen}` |
| PUT | `/crm/clientes/{cedula}` | `X-Sandbox-Id`; body CRM | cliente |
| GET | `/smartclub/{cedula}` | `X-Sandbox-Id` | `{socio, cashback_saldo, cupon, promociones}` |
| POST | `/smartclub/{cedula}/cupones` | `X-Sandbox-Id`; `{qr?}` | cupón |
| POST | `/pedidos` | `X-Sandbox-Id` + `Idempotency-Key`; body pedido | 201/200 `{order, invoice, pricing, coupon, replay}` |
| GET | `/pedidos/{orderNumber}` | `X-Sandbox-Id` | pedido \| 404 |
| POST | `/facturacion/comprobantes` | `X-Sandbox-Id`; `{items, billing, orderNumber?}` | 201 comprobante |
| GET | `/facturacion/comprobantes/{n}` | `X-Sandbox-Id` | comprobante \| 404 |
| DELETE | `/sandbox` | `X-Sandbox-Id` | `{ok}` — borra `SBX#` |
| GET | `/admin/{svc}` | `interno=1`; svc = catalogo\|farmacias\|inventario\|crm\|smartclub\|pedidos\|facturacion | `{service, items, count}` |

## Facturación (forma SRI, MOCK)
Campos con forma SRI (`infoTributaria`, `infoFactura`, `detalles`, `totalConImpuestos` con `codigoPorcentaje` 0/4, `claveAcceso` 49 dígitos + mod 11). Estado siempre `SIMULADA_NO_TRANSMITIDA`. Emisor RUC en `data.EMISOR` es **falso** (demo hackathon). No se transmite al SRI.

## Datos
- **Precios**: referenciales/mock; nunca precios reales de Farmaenlace (`precio_referencial`, `nota_precio`).
- **24 SKUs originales** (FV-1001…FV-2011 + señuelos): mismo name/tags/price → demo idéntico.
- **2 Rx señuelo** `FV-9001` / `FV-9002`: `requiere_receta`; nunca sugeridos con `incluir_receta=false`.
- **12 OTC nuevos** (FV-1012…FV-1016, FV-2012…FV-2018): tags elegidos para no alterar ranking del demo.
- **Clientes**: sintéticos. Sin cambio: `1710034065` don Luis (Cuidador), `1712456787` Andrea (Práctico). Extra: doña Rosa, Mateo.

## Farmacias
| pharmacyId | Nombre | Dirección pública | Fuente |
|---|---|---|---|
| MED-UIO-014 | Medicity Quito CCI | Av. Amazonas N36-152 y Naciones Unidas | farmaenlace.com |
| ECO-UIO-003 | Económicas Shyris | Av. de los Shyris N37-104 y El Comercio | ubica.ec |
| MED-UIO-021 | Medicity Amazonas | Av. Amazonas N31-63 y Av. Eloy Alfaro | humana.med.ec |
| ECO-UIO-011 | Económicas El Inca 2 | Av. El Inca E13-50 y De los Madroños | ubica.ec / exa.ai |
| MED-UIO-030 | Medicity Quito Robles | Av. Amazonas N21-108 entre Robles y Roca | humana.med.ec |

**Fuentes**
- https://www.farmaenlace.com/puntos-de-venta/ — MEDI QUITO CCI
- https://servicio.humana.med.ec/hc/es/articles/4402730300813-Puntos-de-venta-Farmacias-Medicity — MEDI AMAZONAS; MEDI QUITO ROBLES
- https://www.ubica.ec/explore/cerca_de/quito/categoria_20/p13971231603 — Económicas Shyris
- https://www.ubica.ec/explore/neg/quito/farmacias-economicas-quito-el-inca-2 y https://exa.ai/library/place/dxz5c8w127g — Económicas Quito El Inca 2 (−0.154414, −78.471447)

Coords distintas de El Inca 2 = geocoding manual aproximado. Teléfonos, horarios y stock = mock. Distancia = haversine desde ubicación demo (`DEMO_LAT`/`DEMO_LNG`) salvo `lat`/`lng` en query.

## Uso local
```
python3 services/farmaenlace-mock/local_server.py 8765
# FV_FARMAENLACE_URL=http://127.0.0.1:8765
```
Tests offline: `FV_FARMAENLACE_URL` vacío + `FV_STORE=memory` → modo in-process (handler en el mismo proceso).

## Cliente orquestador (`services/api/mock.py`)
- Timeout 2.5 s (`FV_FARMAENLACE_TIMEOUT_S`); 1 reintento si cae keep-alive.
- Fail-closed: `BackendUnavailable` → error de turno; nunca inventa datos.
- Caché: catálogo/farmacias 300 s; inventario 20 s (stale solo para maestros).
- Trace del turno: `fe_calls`, `fe_ms`.
- Reserva: `POST /pedidos` hace la transacción de Farmaenlace (pedido + factura + cupón usado + CRM); después el orquestador avanza su sesión (`SES#`, tabla `connect-atv-data`) con escritura condicional por revisión. Un doble toque reenvía la misma `Idempotency-Key` → mismo pedido.
- La vista del carrito se calcula con los precios del catálogo cacheado; el total que vale es el que devuelve `POST /pedidos` (mismo algoritmo).
