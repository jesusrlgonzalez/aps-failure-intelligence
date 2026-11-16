# P01 · Resultados de escenario

**Todo lo de esta página es resultado de escenario sintético** (empresa ficticia, 9 semanas operadas, MXN de escenario). No es un ahorro medido en una empresa real. Tampoco es el desempeño del modelo de Scania, que se midió una sola vez en el conjunto oficial (costo 11,540 en unidades del reto IDA 2016, [docs/06](../../06_final_evaluation.md)) y no se toca aquí.

Fuente de cada cifra: [`results.json`](../../../reports/pilots/P01/results.json). Una prueba automática comprueba que las cifras de costo de esta página coinciden con ese archivo.

## Regla elegida

Se ordena por puntaje y se revisa lo que tiene puntaje ≥ 27, hasta llenar el cupo. La regla se eligió con 1,078 alertas del 2026-01-05 al 2026-05-03. Su identificador es `be6ec74a9382` y aparece en cada fila de la bitácora.

## Comparación por escenario (9 semanas)

Costo = MXN 1,800 por revisión + MXN 38,000 por avería en ruta. El costo del sistema incluye además MXN 13,500 de operación (1,500 por semana). El ahorro va con su intervalo bootstrap del 90 % por semanas.

| | S1 Referencia (cupo 30) | S2 Adversa (cupo 15) | S3 Límites (cupo 30) |
|---|---|---|---|
| Costo del sistema | 707,700 | 967,700 | 1,096,700 |
| Costo de la práctica actual | 1,166,600 | 1,649,000 | 1,539,200 |
| Costo de la regla sencilla por tipo | 866,200 | 1,283,600 | 1,369,200 |
| **Ahorro neto frente a la práctica actual** | **458,900** (249,090 a 692,580) | **681,300** (404,500 a 961,700) | **442,500** (134,810 a 750,100) |
| Ahorro neto frente a la regla por tipo | 158,500 (−7,900 a 370,190) | 315,900 (20,900 a 578,390) | 272,500 (−55,180 a 621,700) |
| Revisiones: sistema / actual / por tipo | 259 / 247 / 249 | 129 / 135 / 122 | 264 / 264 / 254 |
| Averías en ruta: sistema / actual / por tipo | 6 / 19 / 11 de 50 | 19 / 37 / 28 de 50 | 16 / 28 / 24 de 68 |
| Alertas enviadas a revisión humana | 23 | 56 | 282 |
| Semanas con recomendación suspendida | 0 | 1 | 3 |
| Máximo de la lista en una semana | 30 | 15 | 30 |

Lectura:

- **Frente a la práctica actual**, el sistema gana en los tres escenarios: el intervalo no incluye cero. Con un esfuerzo de taller parecido, las averías en ruta bajan de 19 a 6 en S1.
- **Frente a la regla sencilla por tipo**, la ventaja es clara solo en S2, cuando el cupo es escaso y ordenar por puntaje pesa más. En S1 y S3 el intervalo incluye cero: con 9 semanas no se distingue.
- **S2:** la semana 7 se suspendió por 21 % de alertas sin puntaje. Ese lunes decidió el jefe de taller.
- **S3:**
  - Se suspendieron las semanas 4 y 5 (cambio de firmware detectado) y la 8 (40 % sin puntaje).
  - La semana 6, también con firmware alterado, solo dio AVISO y la lista se emitió. **El monitor detectó 2 de 3 semanas con cambio.**
  - Las 6 alertas del código nuevo fueron todas a revisión humana.

## Sensibilidad

[`sensitivity.csv`](../../../reports/pilots/P01/sensitivity.csv) cubre 48 combinaciones de tres factores:
- razón avería/revisión de 2:1 a 80:1;
- capacidad de 10 por semana a sin límite;
- calidad del puntaje: 0 %, 50 % o 100 % reemplazado por ruido.

| Condición | Frente a la práctica actual | Frente a la regla por tipo |
|---|---|---|
| Puntaje informativo, razón ≥ 5:1 | Conviene en todas las capacidades | Conviene o indiferente; nunca desfavorable |
| Puntaje informativo, razón 2:1 | Conviene | **Desfavorable** en todas las capacidades: revisar casi no cuesta menos que fallar y el costo de operar el sistema pesa |
| Puntaje con 50 % de ruido, cupo 30 | Conviene a 2:1 y 5:1; indiferente desde 10:1 | **Desfavorable** desde 21:1 |
| Puntaje sin información, cupo 30 | Conviene a 2:1 y 5:1; indiferente desde 10:1 | **Desfavorable** desde 10:1 |

Conclusión económica: el sistema conviene cuando el puntaje de la telemática distingue de verdad las alertas riesgosas, la razón avería/revisión es de al menos 5:1 y el taller no alcanza para todo. Con un puntaje pobre, una lista fija por tipo de alerta es mejor y más barata.

## Reproducir

```bash
pip install -r requirements-dev.txt
PYTHONPATH=src python -B -m aps_intel.pilot_p01        # regenera reports/pilots/P01/ (unos 25 s)
python -B -m pytest -q tests/test_pilot_p01.py
```

CI regenera las salidas en cada cambio y falla si difieren de las publicadas. [`evidence.json`](../../../reports/pilots/P01/evidence.json) guarda el SHA-256 de cada salida y del código que las produce.
