# P01 · Dictamen y constancia interna

**Dictamen: DEMOSTRACIÓN APROBADA CON RESERVAS, exclusivamente en Nivel A.** La revisión la hizo el propio autor: es una **autoevaluación**, no una auditoría independiente.

> **Alcance de la aceptación.** Aceptar P01 significa aceptar una demostración operativa reproducible con datos sintéticos. **No** equivale a:
> - certificación independiente;
> - validación en una flota real;
> - autorización de uso industrial.
>
> Las reservas R1–R5 siguen vigentes. **Aceptación formal del OWNER: emitida el 2026-11-17** (Orden A5, A5-D01). Ver la sección 8.

## 1. Puertas de aceptación

| Puerta | Estado | Evidencia |
|---|---|---|
| G0 Definición del problema | PASS | [01_caso_empresarial.md](01_caso_empresarial.md): encargo, preguntas de descubrimiento y criterios C1–C8, en el commit `38d35eb`, anterior al código y a los resultados |
| G1 Datos y contratos | PASS | Manifiesto D1–D7 comprobado contra la verdad sintética (C1); ningún resultado abierto ni futuro en el ajuste (C2) |
| G2 Validación científica | PASS | Los resultados congelados de Scania (`reports/final`, `docs/06`, `artifacts`, `MODEL_CARD.md`) no cambian. Los resultados de escenario se declaran aparte (C8) |
| G3 Integración operativa | PASS | Flujo semanal reproducible con cupo estricto (C3), revisión humana, suspensión y bitácora de cada decisión (C7) |
| G4 Escenarios y robustez | PASS con reservas | S1–S3 y 48 combinaciones de sensibilidad. Reservas R1 y R2 |
| G5 Auditoría y expediente | PASS (autoevaluación) | Este expediente y la constancia de la sección 4 |
| G6 Publicación verificable | PASS | Release [`v1.4.0`](https://github.com/jesusrlgonzalez/aps-failure-intelligence/releases/tag/v1.4.0) sobre `dff45b11a2ec4ef91cc1511d4afc17b03f55393e`, con CI verde y ZIP verificado (sección 7). `v1.4.1` es una corrección documental del expediente (sección 7) |

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

Ninguna reserva está resuelta. Las métricas publicadas no cambian. Seguimiento:

| Incidencia | Reserva | Clasificación |
|---|---|---|
| [#9](https://github.com/jesusrlgonzalez/aps-failure-intelligence/issues/9) Detección incompleta de deriva | R1 | Condición de revisión antes de cualquier piloto empresarial de Nivel B |
| [#10](https://github.com/jesusrlgonzalez/aps-failure-intelligence/issues/10) Utilidad del puntaje no verificada | R2 | Condición de revisión antes de cualquier piloto empresarial de Nivel B |
| [#11](https://github.com/jesusrlgonzalez/aps-failure-intelligence/issues/11) Evaluación externa de escenarios y supuestos | R3, R4, R5 | Mejora metodológica |
| [#12](https://github.com/jesusrlgonzalez/aps-failure-intelligence/issues/12) Criterio de duplicación de alertas | Hallazgo de la conciliación (D1) | Condición de revisión antes de cualquier piloto empresarial de Nivel B: validarlo con la exportación real. Mejora recomendada: usar el id o la hora de la alerta |

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
| CI (Python 3.13.7), commit `561d5ce` | [Ejecución 43953129953](https://github.com/jesusrlgonzalez/aps-failure-intelligence/actions/runs/43953129953): pruebas, tablero e imagen Docker PASS; salidas del piloto regeneradas idénticas |

## 6. Condiciones para un piloto real (Nivel B)

1. Una flota con autorización, un responsable identificado y criterios de éxito aprobados por escrito.
2. Registro del resultado de las alertas **no** revisadas (avería del mismo sistema en 30 días). Sin eso no se mide nada.
3. Al menos 8 semanas de historial y 5 fallas confirmadas. Resolver R1 y R2 antes de empezar.
4. Ocho semanas en modo sombra: la lista se genera y se compara, pero decide el jefe de taller como hoy.
5. Criterios de abandono de [`docs/MVP_PILOTO.md`](../../MVP_PILOTO.md). Ningún resultado de este escenario se comunica como evidencia del Nivel B.
6. Cerrar las incidencias #9, #10 y #12.

## 7. Registro de publicación

| Campo | Valor |
|---|---|
| Versión del repositorio | `v1.4.0` (P01 `P01-v1.0.0`) |
| Commit etiquetado | `dff45b11a2ec4ef91cc1511d4afc17b03f55393e`: último de `main` al etiquetar; fusión del PR [#8](https://github.com/jesusrlgonzalez/aps-failure-intelligence/pull/8) |
| CI de ese commit | [Ejecución 43990393602](https://github.com/jesusrlgonzalez/aps-failure-intelligence/actions/runs/43990393602): PASS (pruebas, incluido `test_release_bundle.py`, salidas de P01 regeneradas idénticas, tablero e imagen) |
| Release | <https://github.com/jesusrlgonzalez/aps-failure-intelligence/releases/tag/v1.4.0> |
| Workflow de release | [Ejecución 43990879168](https://github.com/jesusrlgonzalez/aps-failure-intelligence/actions/runs/43990879168): PASS |
| Paquete | `evidence-v1.4.0.zip`, 50 archivos, SHA-256 `420e4ff4e5c5e73de98ba207929df8a555b123e6fbb68058fce07cb005100c39` |
| Verificación del ZIP descargado | Contiene todos los elementos obligatorios de P01; los SHA-256 coinciden con `evidence.json`; las 6 salidas se regeneran idénticas solo con el contenido del ZIP |

### Versiones del expediente

| Versión | Commit | Qué contiene el expediente | Estado |
|---|---|---|---|
| `v1.4.0` | `dff45b11a2ec4ef91cc1511d4afc17b03f55393e` | Código, pruebas, salidas y evidencia de P01. El dictamen de esa etiqueta muestra G6 «PASS con pendiente» porque se escribió antes de crear la etiqueta, y no registra la aceptación del OWNER. El campo de versión del paquete (`pyproject.toml`, `__init__.py`, `CITATION.cff`) decía `1.3.0` | Histórica e inalterada: la etiqueta, el paquete y su hash no se modifican |
| `v1.4.1` | Etiqueta `v1.4.1` | Corrección documental: aceptación del OWNER (sección 8), G6 con su registro de publicación, reservas vigentes y versión del paquete `1.4.1` | Vigente |

Entre `v1.4.0` y `v1.4.1` no cambia ningún resultado. El código de P01, `reports/pilots/P01/` (incluido `evidence.json`) y los resultados de Scania son idénticos. `tests/test_release_bundle.py` lo comprueba en el paquete de cada versión.

## 8. Aceptación del OWNER

| Campo | Valor |
|---|---|
| Decisión | **DEMOSTRACIÓN NIVEL A APROBADA CON RESERVAS** |
| Emitida por | Jesús R. L. González (OWNER), Orden A5, A5-D01 |
| Fecha | 2026-11-17 |
| Fundamento | Criterios C1–C8 (sección 2), expediente reproducible, pruebas automatizadas y release `v1.4.0` verificado |
| Reservas reconocidas | R1–R5. #9, #10 y #12 son condiciones de revisión antes de cualquier piloto empresarial de Nivel B; #11 es mejora metodológica |
| Alcance | No constituye auditoría independiente ni certificación industrial. **No autoriza ejecutar recomendaciones sobre vehículos reales** |
