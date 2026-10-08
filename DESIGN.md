# DESIGN.md — guía visual (base SmartClub)

## Fuente
- Deck reto p.17 "SMARTCLUB" (pdftoppm 150 dpi, color muestreado = ~aprox). Fuentes deck: Aptos Display/Calibri (Office, no marca).
- smartclub.ec CSS público (theme.1.css, Oct 2026): colores, fuentes, radios. Screenshot móvil del sitio.
- Play Store "smartclub" (com.farmaenlace.smartclub): tono, beneficios. Sin manual de marca oficial → nada aquí es oficial.
- `derivado` = nuestro, para pasar WCAG AA. No de marca.

## Paleta (tokens `@theme` en app/src/routes/layout.css)
| token | hex | origen | uso |
|---|---|---|---|
| primary | #FE6403 | deck p.17 muestreado (web: #FF6C22 botón) | fondos, halo mic, barra top. Texto encima = ink |
| primary-strong | #B83D00 | derivado | botones con texto blanco (5.7:1), burbuja user, mic |
| secondary | #A00117 | deck p.17 muestreado (titular, tarjeta 25%) | títulos, cupón |
| accent | #FF009E | deck p.17 muestreado (web #FF009D) | bordes, decor. Nunca texto chico |
| accent-strong | #C40078 | derivado | texto acento |
| success / -strong | #33C15E / #1F7A3D | web CSS label-success / derivado | stock ok |
| warning | #FFAD45 | web CSS (rol no confirmado) | avisos, texto encima = ink |
| danger | #E83E2C | web CSS button-danger | errores, bordes |
| alerta (AlertaRoja) | #A00117 | = secondary | fondo AlertaRoja, texto blanco 8.4:1 |
| ink / muted | #1D1D1F / #666666 | deck muestreado | texto / texto 2º (5.5:1) |
| line | #E2DDD4 | deck muestreado | bordes |
| cream | #F9F4E1 | deck + web CSS + CTA web | chips, superficies |
| bg / card | #FFF9EE / #FFFFFF | deck fondo muestreado / — | fondo app / tarjetas |
Web oficial = tema oscuro (#171717). App = claro (deck), mejor para adulto mayor.

## Tipografía
- Source Sans 3 (web CSS: body + títulos). Libre (OFL) → self-host `@fontsource-variable/source-sans-3`, solo latin. Base 18px, pesos 400/600/700.
- Web usa Work Sans 500 MAYÚS para labels chicos. Nosotros: Source Sans 3 semibold MAYÚS tracking. Fuente del logo: desconocida.

## Logo, forma, iconos
- Logo smartclub: wordmark minúscula ("smart" bold + "club" fino), isotipo squircle naranja con mano blanca. NO usar (no lo dio el evento). Icono app = squircle naranja + cruz crema propia.
- Radios: botones/chips = pill (web 500px). Tarjetas 24px (`rounded-card`, aprox squircle web). Burbuja 20px, esquina del lado del autor 6px.
- Espaciado: escala Tailwind 4px. Tarjeta p-4, gap-3.
- Sombras: tarjeta suave `shadow-card` (propia). Mic `shadow-mic` halo naranja. Deck = plano.
- Iconos: línea 2px, redondeados (deck p.13, tiles web). SVG inline.

## Componentes
- Burbuja: user = primary-strong + blanco, derecha. Asistente = card + borde line, izquierda. text-lg.
- Mic: círculo 96px primary-strong, icono blanco, ring 8px primary/25. Escuchando = secondary + pulse. Label debajo.
- Input: pill, borde line 2px, foco primary-strong. Enviar = ink.
- ProductCard: nombre bold, detalle muted, precio grande, chips cashback + stock, "Agregar al pedido".
- PharmacyCard: pin, distancia · horario, stock, Retirar aquí / Cómo llegar / Llamar.
- ResumenPedido: ítems, total grande, "Ganas $X de cashback", Confirmar.
- Cupon: fondo cream, borde punteado accent, título secondary, código mono, QR.
- AlertaRoja: fondo alerta, icono triángulo, botón blanco "Llamar al ECU 911". Gana a todo.
- SugerenciaPersonalizada: borde accent, label "PARA TI", "Como sueles llevar X…", Reservar, "¿Por qué me sugieres esto?". Nunca nombra condición.

## Accesibilidad
- WCAG AA: texto ≥4.5:1. Blanco sobre #FE6403 = 2.98 → NO. Usar ink o primary-strong.
- Toque ≥44px. Foco visible. aria-live en chat.
- Adulto mayor: botón "Aa" → `html.senior` base 22px (todo en rem escala). 1–2 opciones, voz primero.

## Tono
- Español Ecuador, tuteo, cálido, corto. "Tu farmacéutico más cercano".
- Marca: cercana, confiable, práctica, familiar, optimista (deck p.12 Medicity, p.13 Económicas). Web: "Simple, rápido y a tu ritmo".
- "smart" en minúscula. Sin jerga médica. Nunca diagnostica.

## No afiliados
- Badge fijo "Demo · datos simulados". Sin logo oficial. Datos 100% sintéticos.
