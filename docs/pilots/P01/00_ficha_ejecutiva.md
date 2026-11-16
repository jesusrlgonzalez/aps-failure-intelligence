# P01 · Ficha ejecutiva: qué unidades mandar a taller cada lunes

**Nivel A, demostración operativa reproducible.** Empresa ficticia, datos sintéticos, 9 semanas simuladas. **No existe piloto real (Nivel B).**

**Problema.** Una flota ficticia de 140 tractocamiones recibe unas 66 alertas por semana y su taller solo hace 30 revisiones. Hoy decide por tipo de alerta y por orden de llegada: hay averías en ruta por alertas no revisadas y revisiones que no encuentran nada.

**Qué se hizo.**
- La exportación llega con 7 tipos de error: duplicados, puntajes faltantes, cambio de escala de un proveedor, nombres contradictorios, fechas mezcladas, filas inválidas y resultados aún abiertos. El sistema la concilia y registra cada corrección.
- Elige una regla de costo mínimo solo con resultados ya cerrados.
- Cada lunes emite la lista **sin rebasar el cupo**. Manda a revisión humana lo que no cabe o no reconoce, y suspende la recomendación cuando los datos o el monitor no permiten decidir.

**Resultado de escenario** (MXN de escenario; no es un ahorro real). Intervalo del 90 % entre paréntesis.

| Escenario | Ahorro neto frente a la práctica actual | Averías en ruta: sistema / actual |
|---|---|---|
| Normal, cupo 30 | 458,900 (249,090 a 692,580) | 6 / 19 |
| Taller a la mitad, captura degradada | 681,300 (404,500 a 961,700) | 19 / 37 |
| Cambio de firmware, código nuevo, captura caída | 442,500 (134,810 a 750,100) | 16 / 28 |

**Cuándo conviene y cuándo no.**
- Conviene si el puntaje de la telemática distingue las alertas riesgosas, una avería cuesta al menos 5 veces una revisión y el taller no alcanza para todo.
- Con un puntaje pobre, o si la avería cuesta solo el doble que la revisión, una lista fija por tipo de alerta es mejor.

**Límites visibles.**
- El monitor detectó 2 de 3 semanas con cambio de firmware.
- El sistema no comprueba por sí mismo que el puntaje aporte información.
- Frente a la regla sencilla por tipo, la ventaja solo se distingue con el taller saturado.

**Dictamen:** demostración aprobada con reservas (autoevaluación). Detalle en [04_dictamen.md](04_dictamen.md).

**Evidencia científica, aparte.** El modelo de Scania se evaluó una sola vez en 16,000 camiones del conjunto oficial: costo 11,540 frente a 187,500 sin triaje, en unidades del reto IDA 2016 ([docs/06](../../06_final_evaluation.md)). Ese resultado no se atribuye a este escenario.
