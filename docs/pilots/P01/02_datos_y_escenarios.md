# P01 · Manifiesto de datos, reglas de imperfección y escenarios

**Naturaleza de los datos:** sintéticos, generados con `aps_intel.alert_intake.example_data`, la misma flota simulada del MVP. No son datos de Scania ni de una empresa real. El conjunto oficial de Scania no se lee en este piloto.

## 1. Fuentes

| Fuente | Contenido | Uso |
|---|---|---|
| Verdad sintética del historial | 21 semanas desde 2026-01-05, 1,084 alertas con resultado cerrado. Incluye unidad, fecha, tipo, puntaje 1–99, proveedor (A: T-101 a T-170, B: T-171 a T-240), si se revisó y si falló | Fuente original conservada; sirve solo para comprobar la conciliación |
| Exportación recibida | La verdad con las reglas D1–D7 aplicadas: [`raw_export_history.csv`](../../../reports/pilots/P01/raw_export_history.csv), 1,383 filas | Entrada del flujo |
| Semanas operadas | 9 semanas (22 a 30). Cada lunes llegan las alertas sin resultado; el resultado se revela después solo para calcular costos | Operación simulada |

Semillas: historial 11, imperfecciones del historial 21, semanas operadas 500 + semana, imperfecciones de operación 31. Conteos exactos por escenario: [`manifest.json`](../../../reports/pilots/P01/manifest.json).

## 2. Reglas de imperfección

| Regla | Qué simula | Cómo se genera | Filas (historial) | Efecto esperado | Cómo se evalúa |
|---|---|---|---|---|---|
| D1 | Doble envío de la telemática | Copia exacta del 3 % de las filas | 40 | Se cuentan una vez | Ids únicos; duplicados eliminados = copias presentes tras D6/D7 (28) |
| D2 | Falla de captura del puntaje | Puntaje vacío en el 8 % | 107 | Se imputa la mediana del tipo; con más de 20 % en una semana se suspende la recomendación | Cada id afectado queda marcado `puntaje_imputado` y ningún otro |
| D3 | Cambio de unidades | El proveedor B reporta el puntaje en escala 0–1 desde la semana 10 | 322 | Se reescala ×100 si el máximo del proveedor en la semana es ≤ 1 | Puntaje conciliado = verdad |
| D4 | Nomenclatura contradictoria | 10 % de los tipos con variantes: mayúsculas sin acento, abreviaturas, inglés | 134 | Catálogo de 8 tipos canónicos; lo desconocido va a revisión humana | Tipo conciliado = verdad; solo quedan tipos del catálogo |
| D5 | Formatos de fecha mezclados | 5 % en ISO y 2 como número de serie de Excel | 69 | Se interpretan igual | Fecha conciliada = verdad |
| D6 | Errores de integración | Fecha imposible (31/02), unidad vacía, «tal vez» en falla | 7 | Fila excluida con aviso | Ninguna fila afectada en la fuente conciliada |
| D7 | Retraso de captura | Resultado vacío en las 4 últimas semanas del historial (la ventana de 30 días no ha cerrado) | 259 | No se usa para elegir la regla | Ninguna fila pendiente ni posterior al corte en el ajuste |

Resultado de la conciliación del historial: 1,383 filas recibidas, 134 nombres corregidos, 335 puntajes reescalados (incluye copias de D1), 271 resultados pendientes (incluye copias), 28 duplicados y 6 filas inválidas fuera. Quedan 1,078 alertas válidas, exactamente las esperadas: 1,084 cerradas menos 6 inválidas (la séptima ya estaba en semanas pendientes). Las 7 reglas se comprueban contra la verdad en `check_reconciliation` y en `tests/test_pilot_p01.py`.

## 3. Información futura

La regla se elige con las alertas del 2026-01-05 al 2026-05-03, cuyo resultado ya cerró. Las semanas pendientes y las 9 operadas no entran al ajuste. El resultado de cada semana operada se usa solo después, para medir costos. Prueba: `test_c2_rule_uses_only_closed_outcomes_before_operation`.

## 4. Escenarios

| Id | Situación | Capacidad | Imperfecciones en semanas operadas |
|---|---|---|---|
| S1 | Referencia: operación normal | 30 por semana | D1 3 %, D2 8 %, D3, D4 10 %, D5 5 % |
| S2 | Adversa: personal del taller reducido a la mitad y captura degradada | 15 por semana | D1 6 %, D2 15 %, D3, D4 15 %, D5 5 % |
| S3 | Límites: firmware que triplica las alertas ABS en las semanas 4–6, un código nuevo (`SPN 5246 FMI 7`, 3 alertas en las semanas 2 y 7) y caída de captura del puntaje (35 % adicional) en la semana 8 | 30 por semana | Las de S1, más las indicadas |

## 5. Reglas de decisión de cada lunes

1. Conciliar la semana. Si falta el puntaje en más del 20 % de las alertas o más del 10 % de las filas son inválidas: **se suspende** la recomendación.
2. Monitor semanal del calibrador (carga, mezcla de tipos, distribución del puntaje). Con estado ALERTA: **se suspende**.
3. Sin suspensión: ordenar por puntaje y marcar «revisar» lo que supera el corte de costo hasta llenar el cupo. Lo atendible que no cabe pasa a «revision_humana» (el jefe de taller decide horas extra o posponer); en la simulación se pospone.
4. Los tipos fuera del catálogo nunca se deciden solos: «revision_humana». En la simulación el jefe de taller los revisa con el cupo sobrante.
5. Semana suspendida: decide el jefe de taller con la práctica actual.

Cada decisión queda en [`decisions.csv`](../../../reports/pilots/P01/decisions.csv) con escenario, semana, id, unidad, fecha, tipo, prioridad, decisión, motivo e identificador de regla.

## 6. Alternativas de comparación

- **Práctica actual:** lo que la flota hace hoy (aceite, balatas y aire siempre; 3 de cada 10 de lo demás), por orden de llegada hasta llenar el cupo.
- **Regla sencilla por tipo:** tasa de falla de cada tipo con contracción bayesiana empírica, sin puntaje, con el mismo cupo y sin suspensión ni costo de operación.
