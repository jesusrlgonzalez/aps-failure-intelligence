# Piloto P01 · Triaje semanal de alertas con taller limitado

**Versión `P01-v1.0.0` · Nivel A (demostración operativa reproducible) · empresa ficticia · datos sintéticos · sin piloto real.**

Capa operativa sobre el método ya validado del proyecto: el calibrador de alertas por costo del MVP. No modifica ni reevalúa el modelo de Scania.

## Recorrido para reclutadores (5 minutos)

1. [Ficha ejecutiva](00_ficha_ejecutiva.md): problema, resultado y límites en una página.
2. [Resultados](03_resultados.md): comparación contra dos alternativas, escenarios y sensibilidad.
3. Código: [`src/aps_intel/pilot_p01.py`](../../../src/aps_intel/pilot_p01.py) · pruebas: [`tests/test_pilot_p01.py`](../../../tests/test_pilot_p01.py).
4. [Dictamen y constancia](04_dictamen.md): puertas G0–G6, criterios y reservas.

Competencias: requisitos de negocio, gobierno de datos imperfectos, decisión por costo con restricción de capacidad, validación temporal sin fuga, diseño de escenarios, análisis de sensibilidad, trazabilidad y reproducibilidad en CI.

## Recorrido empresarial

1. [Caso empresarial](01_caso_empresarial.md): encargo, preguntas de descubrimiento, información faltante y criterios de aceptación.
2. [Datos y escenarios](02_datos_y_escenarios.md): qué datos hacen falta, qué errores se esperan y cómo se tratan, y cómo se decide cada lunes.
3. [Resultados](03_resultados.md): cuándo conviene, cuándo es indiferente y cuándo no.
4. [Condiciones para un piloto real](04_dictamen.md#6-condiciones-para-un-piloto-real-nivel-b).

## Reproducir

```bash
pip install -r requirements-dev.txt
PYTHONPATH=src python -B -m aps_intel.pilot_p01
python -B -m pytest -q tests/test_pilot_p01.py
```

Salidas en [`reports/pilots/P01/`](../../../reports/pilots/P01/):
- `manifest.json`: reglas de imperfección y conteos;
- `raw_export_history.csv`: exportación con errores;
- `decisions.csv`: bitácora de decisiones;
- `results.json`: resultados por escenario;
- `sensitivity.csv`: análisis de sensibilidad;
- `evidence.json`: SHA-256 de salidas y código.

Controles automáticos: los ejecuta CI. Control manual: C8 (sin atribución indebida), registrado en el dictamen.
