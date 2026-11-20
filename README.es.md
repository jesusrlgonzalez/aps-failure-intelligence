# APS failure intelligence: triaje de taller sensible al costo para camiones Scania

*[English](README.md) · Español*

**[Demo en vivo](https://huggingface.co/spaces/JesusRLGonzalez/aps-failure-intelligence)** | **[Página del proyecto](https://jesusrlgonzalez.github.io/aps-failure-intelligence/)**

**Pregunta.** ¿Qué camiones deben ir al taller a revisar el sistema de presión de aire (APS), si una falla no detectada cuesta 500 y una revisión innecesaria cuesta 10? Son los costos oficiales que Scania publicó con los datos.

**Alcance.** Conjunto de datos público APS de Scania (UCI, 2016): el resultado es una comparación con datos públicos, no una prueba en una flota en operación, y los costos son unidades abstractas del reto, no dinero. La retrospectiva semanal de la demo usa una flota **simulada**. Ningún modelo opera en un cliente.

**Respuesta, en el conjunto de prueba oficial de Scania (16,000 camiones, evaluado una sola vez):**

| | Resultado |
|---|---|
| **Costo oficial** | **11,540** (intervalo 95 %: 7,940 – 15,661) frente a **187,500** sin triaje: **−94 %**, en unidades de costo del reto IDA 2016 (no es moneda ni un ahorro medido en una empresa) |
| Fallas detectadas | 359 de 375 (**95.7 %**) |
| Carga de taller | **44.6 revisiones por cada 1,000 camiones**; una de cada dos encuentra una falla real |
| Referencia publicada | Tres primeros del reto IDA 2016: 9,920 / 10,900 / 11,480. Mismo rango; el intervalo no permite separarlos |
| Robustez | Ahorra 88–96 % frente a no hacer triaje con cualquier razón de costos entre 10 : 1 y 100 : 1; 90.7–94.7 % si solo cambia el costo de revisión de ×0.8 a ×3 ([abajo](#sensibilidad-al-costo-de-una-revisión)) |

![Costo frente al umbral](reports/figures/cost_vs_threshold.png)

## Sensibilidad al costo de una revisión

¿Y si una revisión innecesaria cuesta más de 10? Solo cambia ese costo; una falla no detectada sigue en 500. Cada umbral se elige con los puntajes fuera de pliegue del entrenamiento, y el conjunto de prueba oficial solo informa las consecuencias (`python -B -m aps_intel.sensitivity`, [reporte](reports/sensitivity/sensitivity.json)). Unidades de costo del reto IDA 2016, no dinero.

| Costo de revisión | Umbral (elegido en entrenamiento) | Revisiones / 1,000 | Revisiones innecesarias | Fallas no detectadas | Costo | vs sin triaje | Umbral re-elegido − fijo, 95 % |
|---|---:|---:|---:|---:|---:|---:|---|
| 8 (×0.8) | 0.00115 | 46.0 | 375 | 14 | 10,000 | −94.7 % | −2,372 a +200 |
| **10 (oficial)** | **0.00136** | **44.6** | **354** | **16** | **11,540** | **−93.8 %** | misma regla |
| 12 (×1.2) | 0.00136 | 44.6 | 354 | 16 | 12,248 | −93.5 % | misma regla |
| 15 (×1.5) | 0.00136 | 44.6 | 354 | 16 | 13,310 | −92.9 % | misma regla |
| 20 (×2) | 0.00298 | 38.6 | 261 | 19 | 14,720 | −92.1 % | −1,900 a +1,580 |
| 30 (×3) | 0.00429 | 35.4 | 213 | 22 | 17,390 | −90.7 % | −3,470 a +1,420 |

- **La regla es estable.** Entre 10 y 15 el umbral elegido no cambia; desde 20 sube y la carga de taller baja, como se espera.
- **Re-elegir el umbral no es demostrablemente mejor** que mantener el oficial: todos los intervalos al 95 % de la diferencia incluyen el cero.
- **Cuándo deja de convenir.** El umbral oficial solo costaría lo mismo que no revisar ningún camión si una revisión costara unas 35 veces más (348 por revisión, en datos de entrenamiento).
- **Capacidad de taller** (supuesto ilustrativo): con espacio para 30 revisiones por cada 1,000 camiones, el costo sube a 13,130 (22 fallas no detectadas); con 20, a 23,300 (45).

## Úsalo con las alertas de tu flota (MVP)

Las 170 lecturas de Scania son internas del fabricante; el producto es el **método**: decidir por costo qué alertas merecen revisión en taller y vigilar la carga cada semana. En la [demo](https://huggingface.co/spaces/JesusRLGonzalez/aps-failure-intelligence), modo **«Tus alertas»**:

1. Descarga la plantilla o sube la exportación de tu telemática (`.xlsx` o `.csv`): unidad, fecha, tipo de alerta, puntaje opcional, si se revisó y si se confirmó la falla (en taller o como avería en ruta en 30 días).
2. Captura el costo de una revisión, el costo extra de una falla en ruta y, si quieres, la capacidad semanal del taller.
3. Obtén la regla de menor costo, la banda de revisiones por semana, una retrospectiva temporal contra lo que se hizo (intervalo del 90 % por semanas) y un reporte de una página.
4. Cada lunes sube la semana nueva: sale la lista de unidades a taller y una alerta si la carga o la mezcla de alertas se mueve.

En la flota simulada de ejemplo (140 tractocamiones, 26 semanas), la regla elegida con las primeras 17 semanas habría costado **476 mil pesos menos** que la práctica actual en las últimas 9 (intervalo del 90 %: 206 a 724 mil), con 9 fallas en ruta en lugar de 23. El archivo se procesa en el navegador y no sale de él. Protocolo de piloto y criterios de abandono: [`docs/MVP_PILOTO.md`](docs/MVP_PILOTO.md).

**Caso demostrativo P01 (Nivel A, empresa ficticia, datos sintéticos, sin piloto real):** triaje semanal con cupo estricto de taller a partir de una exportación con siete tipos de defectos de datos, con revisión humana, reglas de suspensión, tres escenarios y sensibilidad a costos, capacidad y calidad del puntaje. Dictamen: aprobado con reservas (autoevaluación). [`docs/pilots/P01/`](docs/pilots/P01/README.md).

## Por qué el resultado es confiable

- **Una sola mirada al test.** Está sellado en código (`load_holdout` falla salvo en la evaluación final) y un archivo de reserva impide una segunda evaluación. Las reglas de esa evaluación y el plan de análisis se publicaron **antes** de ejecutarla.
- **Umbral sin fuga.** En validación cruzada cada pliegue se califica con un umbral elegido solo en los demás pliegues. El umbral final sale de las puntuaciones fuera de pliegue del entrenamiento.
- **Decisiones pre-registradas.** Candidatos (fase 4) y un presupuesto fijo de 12 configuraciones (fase 5) se publicaron antes de tener resultados. El tuning ganó 0.5 %, dentro del ruido de semilla, y así se reporta.
- **Datos verificados byte a byte.** Los archivos oficiales se guardan comprimidos y su SHA256 coincide con el publicado; las pruebas rechazan cualquier byte editado.
- **Afirmaciones acotadas.** Clasifica lecturas actuales bajo una matriz de costos. No pronostica cuándo ocurrirá una falla, no afirma causas y los costos son unidades abstractas del reto, no dinero.

## Método por fases

| Fase | Resultado |
|---|---|
| 1 · Ingesta y auditoría | 60,000 camiones, 1.7 % de fallas; los faltantes son informativos |
| 2 · Contrato del problema | El costo oficial es la única métrica de selección |
| 3 · Baseline y protocolo | Regresión logística 52,100 frente a 500,000 trivial (CV de entrenamiento; 49,550–52,950 en otros procesadores, [por qué](docs/03_baseline.md#reproducibility-across-processors)) |
| 4 · Candidatos | LightGBM + indicadores de faltantes, 34,600 |
| 5 · Tuning controlado | 34,440; dispersión por semilla 33,220 – 38,480 |
| 6 · Evaluación final única | 11,540 en el test oficial |
| 7 · Errores, incertidumbre, economía | Bootstrap, sensibilidad a la razón de costos, calibración, drivers |
| 8 · Model Card y release | [MODEL_CARD.md](MODEL_CARD.md) |
| 9 · Prueba de estrés y monitoreo | 8 defectos inyectados: 5 alertas, 1 aviso, 2 invisibles por diseño |
| 10 · Recalibración | Isotónica sobre OOF de entrenamiento; Brier 0.00497 → 0.00473, mismo orden |
| Siguiente · Datos reales | Datos públicos sucios y un socio real |

Los documentos de cada fase están en [`docs/`](docs) (en inglés).

## Stack y para qué sirve cada pieza

| Capa | Herramienta | Función |
|---|---|---|
| Contrato de datos | **SQL en DuckDB** | 11 controles de esquema, etiquetas, rangos y faltantes; el test se expone sin etiquetas |
| Modelado | **Python**: pandas, scikit-learn, **LightGBM** | Rasgos sin fuga, CV de costo anidada, gradient boosting |
| Decisión | Umbral óptimo por costo (búsqueda exacta) | Convierte la puntuación en revisar / no revisar |
| Explicaciones | Contribuciones de LightGBM | Lecturas que más empujan la puntuación de cada camión |
| Servicio | **FastAPI** + **Docker** | `/score` con puntuación, decisión, riesgo calibrado y drivers; `/health` con hash del modelo |
| Monitoreo | PSI, banda binomial de carga de taller, esquema | `/monitor` avisa de deriva, datos faltantes y carga de taller inesperada |
| Soporte a la decisión | **Streamlit** + Altair | Pon tus costos y tamaño de flota; el umbral se recalcula con datos de entrenamiento |
| Control de calidad | **pytest** + **GitHub Actions** | Integridad de datos, test sellado, costo óptimo, servicio, dashboard y Docker |

## Reproducir

Los comandos están en la sección *Reproduce* del [README en inglés](README.md#reproduce).

## Aptitudes demostradas

| Aptitud | Evidencia |
|---|---|
| Bayesian statistics / Estadística bayesiana | `src/aps_intel/alert_calibrator.py`, `src/aps_intel/cost.py` (contracción hacia la tasa global) |
| Model monitoring / Monitoreo de modelos | `src/aps_intel/monitor.py` (banda binomial, ji cuadrada) |
| Predictive maintenance / Mantenimiento predictivo | `src/aps_intel/cost.py` (umbral de menor costo) |
| Machine learning, FastAPI, DuckDB | `src/aps_intel/`, `src/aps_intel/service.py` |
| Data visualization, Git, CI, testing / Visualización de datos, Git, integración continua, pruebas | `dashboard/app.py`, `.github/workflows/`, `tests/` |

## Licencia y cita

Código: [Apache-2.0](LICENSE). Datos: Scania CV AB vía UCI Machine Learning Repository, [doi:10.24432/C51S51](https://doi.org/10.24432/C51S51). Ver [NOTICE](NOTICE) y [CITATION.cff](CITATION.cff).

---

**Jesús R. L. González** · Científico de Datos · Operaciones y calidad en manufactura
