# Script — pitch 3 min (hackathon)

Hablar despacio. Mirar al jurado, no a la pantalla. Demo: narrar mientras se toca.

**[0:00–0:15] Portada**
Hola, soy Eric Aguayo, co-fundador y director de IA aplicada en Nimblersoft. Pensemos en esa señora adulta que va a Farmacias Económicas cada mes por su vitamina. Según ella, le toca ir porque las apps de hoy la abruman con catálogos, filtros, formularios y botones. Entonces no las usa. Para ella hice el Farmacéutico Virtual: tu farmacéutico más cercano, en el celular.

**[0:15–0:35] Problema**
Farmaenlace lo dice en su propio reto: en cuatro de cinco marcas, más de la mitad de los clientes compra una sola vez. Y solo cerca del dos por ciento de las ventas es online. Ustedes quieren pasar de la transacción a la relación. La puerta digital existe, pero cuesta cruzarla.

**[0:35–0:50] Propuesta de valor**
Para los clientes de Farmacias Económicas y Medicity que evitan las apps porque les resultan complicadas, ofrecemos un farmacéutico virtual al que simplemente le hablas y te arma la pantalla que necesitas. Sin catálogos ni formularios: comprar, y volver a comprar, es tan fácil como preguntarle a tu farmacéutico.

**[0:50–1:40] Demo**
Les muestro. Escaneo el QR de la farmacia, digo mi cédula y ya tengo mi cupón. Ahora hablo: "algo para la gripe". En segundos la app arma la pantalla: opciones de venta libre, precio, cashback SmartClub y stock en la farmacia más cercana.
Misma pregunta, otro cliente. A una persona práctica le muestra una sola tarjeta y un toque. A una cuidadora, letra grande y voz primero. Y como suele llevar su multivitamínico cada mes, le ofrece reservarlo con doble cashback. Reservo, retiro en la farmacia, y la factura queda lista.

**[1:40–2:00] Diferenciador**
No es un chatbot que responde texto: la interfaz se genera para cada persona. Es fidelizar con datos, por marca y arquetipo, como pide su reto. Personaliza por lo que compras y nunca menciona tu condición. Solo venta libre, nunca diagnostica, y ante una señal de alarma muestra una alerta roja con el ECU 911 y te pasa con un farmacéutico humano.

**[2:00–2:15] Real vs simulado**
Lo real: Claude Haiku en Bedrock genera la interfaz, GLiNER entiende qué pides, y la voz es de AWS. Lo simulado: catálogo, SmartClub y clientes; todos los datos son sintéticos. En nuestras pruebas, todas las respuestas salieron válidas y seguras, a menos de un centavo cada una.

**[2:15–2:40] Piloto contra sus KPIs**
¿Cómo llega a producción? No reemplaza nada: es una app nueva, opcional, sobre las APIs que Farmaenlace ya tiene. Primero, el uno por ciento de la web. Luego, QR en unas pocas farmacias contra farmacias de control. El KPI es su KPI: recompra a treinta y sesenta días contra ese control. Escalamos solo con datos.

**[2:40–2:55] Siguiente paso y cierre**
Lo que proponemos: un piloto con Farmaenlace para validar este MVP contra sus números. Que esa señora vuelva, y vuelva otra vez. Tu farmacéutico más cercano, en el celular. ¿Cuál es el siguiente paso?

---
**Si se cae el demo**
1. Recargar con `?demo` y decir: "modo simulado, misma interfaz".
2. Si no carga: grabación de 40 s; seguir el mismo texto.
3. Último recurso: 3 screenshots (UI generada, 2 arquetipos, reserva); no perder el cierre.
