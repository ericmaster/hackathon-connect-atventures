# Script — pitch 3 min (hackathon)

Hablar despacio. Mirar al jurado, no a la pantalla. Demo: narrar mientras se toca.

**[0:00–0:15] Portada**
Hola, soy Eric Aguayo, co-fundador y director de IA aplicada en Nimblersoft. Pensemos en esa señora adulta que va a Farmacias Económicas cada mes por su vitamina. Según ella, le toca ir porque las apps de hoy la abruman con catálogos, filtros, formularios y botones. Entonces no las usa. Para ella hice el Farmacéutico Virtual: tu farmacéutico más cercano, en el celular.

**[0:15–0:35] Problema**
Farmaenlace lo dice en su propio reto: en cuatro de cinco marcas, más de la mitad de los clientes compra una sola vez. Y solo cerca del dos por ciento de las ventas es online. Ustedes quieren pasar de la transacción a la relación. La puerta digital existe, pero cuesta cruzarla.

**[0:35–0:50] Propuesta de valor**
Para los clientes de Farmacias Económicas y Medicity que evitan las apps porque les resultan complicadas, ofrecemos un farmacéutico virtual al que simplemente le hablas y te arma la pantalla que necesitas. Sin catálogos ni formularios: comprar, y volver a comprar, es tan fácil como preguntarle a tu farmacéutico.

**[0:50–1:40] Demo** (validado en vivo 14:38, PWA real, ~3 s por respuesta)

Antes de subir: abrir la PWA (sin `?demo`), tocar "↺ Reiniciar demo", dejarla en la pantalla de cédula.

| # | Toco / digo | Sale | Digo al jurado |
|---|---|---|---|
| 1 | — (pantalla inicial) | Cupón BIENVENIDA3 $3 | "Escaneo el QR en la farmacia y ya tengo mi cupón." |
| 2 | Escribo `1710034065` → **Continuar** | "¡Gracias, don Luis!" + consentimiento | "Solo mi cédula. Nada de formularios." |
| 3 | ☑ consentimiento → **Continuar** | Letra grande sola + "Sueles llevar tu Multivitamínico 50+ cada mes…" | "Es cuidador: letra grande y voz primero, sin tocar nada." |
| 4 | **¿Por qué me sugieres esto?** | "…lo compras mensual y tu última compra fue hace 27 días." | "Personaliza por cómo compras. Nunca nombra una condición." |
| 5 | 🎤 "algo para la gripe" | "¿Tienes alergia a algún medicamento o estás tomando otro?" | "Antes de sugerir, pregunta por seguridad." |
| 6 | **No, ninguno** (espera 5–7 s) | Antigripal $5,20 + Paracetamol $2,40, stock a 240 m | Llenar la espera: "Aquí la IA real arma esta pantalla para él." |
| 7 | **Agregar al pedido** (Antigripal) → **Retirar aquí** (Medicity Quito CCI) | Resumen: cupón −$3,00, total $2,20, cashback $0,26 | "Se aplicó su cupón y gana cashback SmartClub." |
| 8 | **Confirmar pedido** → **Consumidor final** → email `demo@example.com` → **Continuar** → **Confirmar y reservar** | "¡Listo! Tu pedido está reservado." + QR + factura simulada | "Reservado. Retira y paga en la farmacia." |

Si el tiempo aprieta: saltar el paso 4 o decir "en un minuto más le llega la factura" y no completar el paso 8.

**[1:40–2:00] Diferenciador** (con alerta en vivo)
Toco **Nueva consulta** y digo 🎤 "tengo dolor de pecho fuerte y me cuesta respirar". Sale la tarjeta roja "Atención urgente" con ECU 911 y ningún producto.
No es un chatbot que responde texto: la interfaz se genera para cada persona. Es fidelizar con datos, por marca y arquetipo, como pide su reto. Personaliza por lo que compras y nunca menciona tu condición. Solo venta libre, nunca diagnostica, y ante una señal de alarma muestra una alerta roja con el ECU 911 y te pasa con un farmacéutico humano.

**[2:00–2:20] Arquitectura: real vs simulado**
Por dentro, no dejamos todo a un solo LLM. Un modelo de decisión, GLiNER, entiende qué pides. Reglas y guardrails deciden qué se puede ofrecer. Recién ahí Claude Haiku arma la pantalla, y se valida antes de mostrarse. Menos alucinaciones, más rápido y más barato. Lo simulado son las APIs de Farmaenlace, con datos sintéticos.

**[2:20–2:45] Piloto contra sus KPIs**
¿Cómo llega a producción? No reemplaza nada: es una app nueva, opcional, sobre las APIs que Farmaenlace ya tiene. Primero, el uno por ciento de la web. Luego, QR en unas pocas farmacias contra farmacias de control. El KPI es su KPI: recompra a treinta y sesenta días contra ese control. Escalamos solo con datos.

**[2:45–3:00] Siguiente paso y cierre**
Lo que proponemos: un piloto con Farmaenlace para validar este MVP contra sus números. Que esa señora vuelva, y vuelva otra vez. Tu farmacéutico más cercano, en el celular. ¿Cuál es el siguiente paso?

---
**Si se cae el demo**
1. Recargar con `?demo` y decir: "modo simulado, misma interfaz".
2. Si no carga: grabación de 40 s; seguir el mismo texto.
3. Último recurso: 3 screenshots (UI generada, 2 arquetipos, reserva); no perder el cierre.
