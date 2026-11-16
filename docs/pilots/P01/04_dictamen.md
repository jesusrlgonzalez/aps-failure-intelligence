# P01 · Dictamen y constancia interna

**Dictamen: DEMOSTRACIÓN APROBADA CON RESERVAS** (Nivel A). Revisión hecha por el propio autor: es una **autoevaluación**, no una auditoría independiente.

## 1. Puertas de aceptación

| Puerta | Estado | Evidencia |
|---|---|---|
| G0 Definición del problema | PASS | [01_caso_empresarial.md](01_caso_empresarial.md): encargo, preguntas de descubrimiento y criterios C1–C8, en el commit `38d35eb`, anterior al código y a los resultados |
| G1 Datos y contratos | PASS | Manifiesto D1–D7 comprobado contra la verdad sintética (C1); ningún resultado abierto ni futuro en el ajuste (C2) |
| G2 Validación científica | PASS | Los resultados congelados de Scania (`reports/final`, `docs/06`, `artifacts`, `MODEL_CARD.md`) no cambian. Los resultados de escenario se declaran aparte (C8) |
| G3 Integración operativa | PASS | Flujo semanal reproducible con cupo estricto (C3), revisión humana, suspensión y bitácora de cada decisión (C7) |
| G4 Escenarios y robustez | PASS con reservas | S1–S3 y 48 combinaciones de sensibilidad. Reservas R1 y R2 |
| G5 Auditoría y expediente | PASS (autoevaluación) | Este expediente y la constancia de la sección 4 |
| G6 Publicación verificable | Se cumple al fusionar con CI verde | CI regenera las salidas y falla si difieren. Versión `P01-v1.0.0` |

## 2. Criterios

| Id | Resultado | Fuente |
|---|---|---|
| C1 Imperfecciones tratadas | PASS: 7 de 7 reglas; 1,078 de 1,078 filas esperadas | `test_c1_*`, `results.json → conciliacion` |
| C2 Sin información futura | PASS | `test_c2_*` |
| C3 Cupo respetado | PASS: máximo 30, 15 y 30 por semana | `test_c3_*` |
| C4 Referencia: ahorro neto con límite inferior > 0 | PASS: 249,090 | [03_resultados.md](03_resultados.md) |
| C5 Adversa: costo del sistema no mayor que el actual | PASS: 967,700 frente a 1,649,000 | [03_resultados.md](03_resultados.md) |
| C6 Límites: suspensión y tipos desconocidos | PASS: 3 de 3 semanas con dato insuficiente o cambio detectado suspendidas; 6 de 6 alertas desconocidas a revisión humana | `test_c6_*` |
| C7 Trazabilidad y reproducibilidad | PASS | `test_c7_*`, `evidence.json`, paso de CI |
| C8 Sin atribución indebida | PASS (revisión manual) | La ficha y los resultados separan la cifra de Scania de las de escenario |

Sin incidencias críticas.

## 3. Reservas (visibles en la ficha ejecutiva)

- **R1 Detección parcial de cambios.** El firmware alterado se inyectó en las semanas 4 a 6. El monitor suspendió la 4 y la 5; la 6 solo dio AVISO y la lista se emitió. Antes de un piloto real: tratar un AVISO justo después de una ALERTA como suspensión.
- **R2 El puntaje no se verifica.** El sistema usa el puntaje de la telemática aunque no informe. Con 50 % o más de ruido es desfavorable frente a la regla por tipo. Antes de un piloto real: comparar en la retrospectiva el modo por puntaje y el modo por tipo (el calibrador ya admite los dos) y usar el mejor.
- **R3 Ventaja frente a la regla sencilla.** Solo se distingue con el taller saturado (S2). En S1 y S3 el intervalo incluye cero con 9 semanas.
- **R4 Alcance del escenario.** El generador y el sistema son del mismo autor y los costos son supuestos. Las cifras no anticipan el efecto en una flota real.
- **R5 Decisiones humanas simuladas.** El jefe de taller sigue políticas fijas: posponer lo que no cabe, usar el cupo sobrante en lo desconocido y aplicar la práctica actual en semanas suspendidas.

## 4. Constancia Interna de Demostración Verificada

| Campo | Valor |
|---|---|
| Proyecto | `aps-failure-intelligence` · Piloto P01, triaje semanal de alertas con taller limitado |
| Versión | `P01-v1.0.0` |
| Commit evaluado | `3ffc58908017d95f8e626c00d342c5592fdf3bd2` (código, pruebas y salidas) |
| Fecha | 2026-11-16 |
| Pruebas | Piloto: 8 de 8. Suite completa: 68 pasan, 2 omitidas (sección 5) |
| Controles | C1–C7 automáticos PASS; C8 manual PASS; integridad SHA-256 de salidas y código (`evidence.json`) |
| Resultado | Demostración aprobada con reservas R1–R5 |
| Naturaleza | **Autoevaluación del autor.** No es certificación externa, validación empresarial independiente ni acreditación de producción. No autoriza uso industrial ni declaraciones de impacto real |

## 5. Registro de ejecución

| Entorno | Resultado |
|---|---|
| Local, Python 3.13 | Suite completa: 68 pasan, 2 omitidas; piloto 8 de 8 |
| CI (Python 3.13.7) | PENDIENTE |

## 6. Condiciones para un piloto real (Nivel B)

1. Una flota con autorización, un responsable identificado y criterios de éxito aprobados por escrito.
2. Registro del resultado de las alertas **no** revisadas (avería del mismo sistema en 30 días). Sin eso no se mide nada.
3. Al menos 8 semanas de historial y 5 fallas confirmadas. Resolver R1 y R2 antes de empezar.
4. Ocho semanas en modo sombra: la lista se genera y se compara, pero decide el jefe de taller como hoy.
5. Criterios de abandono de [`docs/MVP_PILOTO.md`](../../MVP_PILOTO.md). Ningún resultado de este escenario se comunica como evidencia del Nivel B.
