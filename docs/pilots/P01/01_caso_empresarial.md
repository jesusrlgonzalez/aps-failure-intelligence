# P01 · Caso empresarial: triaje semanal de alertas con taller limitado

**Nivel de validación:** A, demostración operativa reproducible. **Empresa:** ficticia. **Datos:** sintéticos. **Piloto real (Nivel B):** no existe.

## 1. Encargo

**Transportes Ficticios del Altiplano, S.A.** (empresa ficticia) opera 140 tractocamiones con telemática. Su gerente de mantenimiento escribe:

> Recibimos unas 66 alertas por semana. Hoy mandamos a taller todas las de aceite, balatas y aire, y unas 3 de cada 10 de las demás. El taller atiende 30 revisiones por semana. Este trimestre tuvimos averías en ruta por alertas que no se revisaron, y el jefe de taller dice que la mitad de lo que le mandamos no tiene nada. Necesito saber qué unidades revisar cada lunes sin pasarme del cupo, cuánto me cuesta cada opción y cuándo no debo confiar en la lista.

## 2. Situación actual y consecuencias

| Concepto | Supuesto del caso | Origen |
|---|---|---|
| Costo de una revisión | MXN 1,800: horas de técnico y medio día de unidad detenida | Supuesto declarado (`alert_calibrator.Settings`) |
| Costo extra de una avería en ruta | MXN 38,000: grúa, carga demorada y días de unidad parada | Supuesto declarado (`alert_calibrator.Settings`) |
| Capacidad del taller | 30 revisiones por semana | Supuesto del caso |
| Costo de operar el sistema | MXN 1,500 por semana: dos horas de analista para cargar datos y revisar la lista | Supuesto del caso |
| Práctica actual | Revisar siempre aceite, balatas y aire, y 3 de cada 10 de lo demás, por orden de llegada | Regla del generador sintético |

Las cifras de costo son de escenario. No son ahorros medidos en una empresa real.

## 3. Por qué la práctica actual no basta

- Decide por tipo de alerta y por orden de llegada: ignora el puntaje de riesgo que ya entrega la telemática.
- Cuando el taller se satura, se atiende lo que llegó primero, no lo más riesgoso.
- Nadie detecta cuándo cambia la telemática (firmware, proveedor) y las alertas dejan de significar lo mismo.

## 4. Preguntas de descubrimiento

| Pregunta al cliente | Por qué importa | Respuesta en este caso |
|---|---|---|
| ¿Se registra si hubo falla en las alertas que **no** se revisaron? | Sin eso no se puede medir el costo de no revisar | Sí: avería en ruta del mismo sistema en 30 días |
| ¿Cuántas semanas de historial hay y cuánto tarda en cerrarse el resultado de una alerta? | Define cuándo un dato ya es utilizable | 30 semanas; el resultado se conoce 30 días después |
| ¿Todas las unidades usan el mismo proveedor de telemática? | Cambios de escala o de códigos | No: dos proveedores; el B cambió de formato |
| ¿Los nombres de alerta están normalizados? | Un mismo tipo escrito de varias formas parte la estadística | No: hay variantes y abreviaturas |
| ¿Qué pasa cuando el taller no alcanza? | Restricción dura frente a promedio | Lo que no cabe se pospone; el jefe de taller puede autorizar horas extra |
| ¿Quién aprueba la lista semanal? | Revisión humana | El jefe de taller; el sistema solo recomienda |

## 5. Diagnóstico inicial y viabilidad

- **Información disponible:** alertas con unidad, fecha, tipo, puntaje, proveedor, si se revisó y si hubo falla.
- **Información faltante:** costo real por tipo de avería, disponibilidad diaria del taller y causa raíz. Se usan supuestos declarados.
- **Viabilidad:** hay historial suficiente (mínimo 8 semanas y 5 fallas, regla del calibrador) para elegir y validar una regla con separación temporal.

## 6. Propuesta metodológica

1. Recibir la exportación tal como llega (con errores), conservar el original y producir una fuente reconciliada con bitácora de cada corrección.
2. Elegir la regla de costo mínimo con las semanas de historial cuyo resultado ya cerró, sin usar resultados posteriores.
3. Cada lunes: validar la semana, monitorear cambios y emitir la lista ordenada por riesgo **sin rebasar el cupo**. Lo atendible que no cabe y lo que el sistema no reconoce va a revisión humana.
4. Suspender la recomendación automática cuando la calidad de datos o el monitor lo impidan; esa semana decide el jefe de taller con la práctica actual.
5. Comparar contra la práctica actual y contra una regla estadística sencilla (tasa de falla por tipo) en escenarios normal, adverso y de límites. Medir la sensibilidad a costos y capacidad.

## 7. Criterios de aceptación (fijados antes de la evaluación)

| Id | Criterio | Cómo se comprueba |
|---|---|---|
| C1 | Cada regla de imperfección del manifiesto se detecta o corrige como indica el manifiesto | Prueba automática contra la verdad sintética |
| C2 | Ningún resultado pendiente ni posterior a la semana de corte entra al ajuste de la regla | Prueba automática |
| C3 | En ninguna semana la lista automática rebasa la capacidad del taller | Prueba automática en los tres escenarios |
| C4 | Escenario de referencia: ahorro neto (incluido el costo de operar) frente a la práctica actual con límite inferior del intervalo bootstrap 90 % por semanas mayor que cero. Si no se cumple, el dictamen es «no desplegar» | Reporte de resultados |
| C5 | Escenario adverso: cupo respetado y costo del sistema no mayor que el de la práctica actual con el mismo cupo (estimación puntual) | Reporte de resultados |
| C6 | Escenario de límites: recomendación suspendida en el 100 % de las semanas con datos insuficientes o cambio detectado, y cero decisiones automáticas sobre tipos de alerta desconocidos | Prueba automática |
| C7 | Cada decisión registra semana, unidad, tipo, prioridad, decisión, motivo, escenario e identificador de regla; las salidas se regeneran idénticas | Prueba automática y CI |
| C8 | Ningún documento atribuye al escenario sintético el desempeño del conjunto oficial de Scania | Revisión manual del expediente |

Un incumplimiento de C1, C2, C3, C6 o C7 es incidencia crítica: bloquea la publicación como demostración validada. C4 y C5 deciden entre «conviene probar» y «no desplegar».
