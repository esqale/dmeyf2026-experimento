# Experimento colaborativo "Inflación 1" · DMEyF 2026 (comisión lunes)

Manuel Marasco · Alejandro Esquivel · Alexander Arias

**Pregunta:** ¿deflactar cada grupo de variables monetarias con su propio índice da más ganancia que dividir todo por el IPC? ¿Y deflactar da más que no deflactar?

Se comparan tres brazos con un mismo esquema de referencia (churn BAJA+2, LightGBM, solo 2019): **sin deflactar**, **todo con IPC** y **cada grupo con su deflactor**. Cada brazo se corre con las mismas 20 semillas y se compara contra el ruido entre semillas.

Entrega: video de 10 minutos, 23/11 antes del mediodía. El documento del experimento es `docs/investigacion.md`, y el plan con el estado de cada paso, `docs/hoja_de_ruta.md`.

## Cómo correrlo desde cero

Hace falta Python 3.13 y unos 14 GB de RAM (anda con menos, pero más lento).

```bash
pip install -r requirements.txt

# 1. Datos: bajar competencia_02_crudo.csv.gz (link en Zulip, #Lunes: Material + Tareas › Clase 10)
#    y convertirlo a un parquet por mes. Se repite hasta que diga TODO COMPLETO (~2 min en total).
python src/00_convertir_a_parquet.py <ruta>/competencia_02_crudo.csv.gz historia/mensual

# 2. Exploración (Paso 3): tablas en reportes/paso3/
python src/01_exploracion.py

# 3. Dataset del baseline: lag y delta 1 y 2 + clase, 201903–201910 (~40 s)
python src/02_dataset.py

# 4. Baseline: Optuna de 50 trials + test en 201910 (~1 h 45 min; si se corta, se relanza y retoma)
python src/03_baseline.py --dataset datasets/fe_base --nombre baseline

# 5. Ruido por semilla: 20 semillas con los hiperparámetros del baseline (~50 min)
python src/04_semillas.py --dataset datasets/fe_base --nombre baseline

# 6. Índices externos (ya están en datos_externos/; --bajar los vuelve a descargar)
python src/05_indices.py

# 7. Inventario de columnas monetarias (Paso 10): reportes/paso10/
python src/06_monetarias.py

# 8. Brazo "todo con IPC" (con el IPC del mes anterior y del mismo mes, para el objetivo 1) y sus 20 semillas
python src/02_dataset.py --brazo ipc --desfase 1
python src/02_dataset.py --brazo ipc --desfase 0
python src/04_semillas.py --dataset datasets/fe_ipc_d1 --nombre ipc_d1
python src/04_semillas.py --dataset datasets/fe_ipc_d0 --nombre ipc_d0

# 9. Verificación de monedas (Paso 10, D14) y brazo "por grupo" con sus 20 semillas
python src/08_monedas.py
python src/02_dataset.py --brazo grupo
python src/04_semillas.py --dataset datasets/fe_grupo --nombre grupo

# 10. Comparación pareada por semilla (el primero es la referencia)
python src/07_comparar.py baseline ipc_d1 ipc_d0 grupo
python src/07_comparar.py ipc_d1 grupo

# 11. Diagnósticos (D17, D18): validación adversarial de los montos y dónde cortan los árboles
python src/10_adversarial.py
python src/11_cortes.py

# 12. Otras formas de corregir la inflación (D19, D20). Cada una: armar el dataset y correr las 20 semillas
#     --brazo ranking          G:  ranking por mes con cero fijo, antes de lags y deltas  -> datasets/fe_ranking
#     --brazo ranking_post     G2: ranking después de lags y deltas (necesita fe_base)
#     --brazo nominal_ranking  M:  fe_base + las monetarias de fe_ranking con sufijo _rk (necesita las dos)
#     --brazo delta_log        H:  deltas relativos, slog(x_t) - slog(x_t-k)
#     --brazo ranking_sin_cero G0: ranking sin cero fijo
#     --brazo grupo_saldos_ipc J:  por grupo con IPC en los 8 saldos
#     --brazo mediana          K:  cada columna / su mediana del mes
#     --brazo grupo --con-mes  L:  por grupo + foto_mes -> datasets/fe_grupo_mes
python src/02_dataset.py --brazo delta_log
python src/04_semillas.py --dataset datasets/fe_delta_log --nombre delta_log
python src/07_comparar.py baseline ranking ranking_post nominal_ranking delta_log ranking_sin_cero grupo_saldos_ipc mediana grupo_mes ipc_d1 grupo --salida reportes/comparacion_d19_d20.csv
```

Para seguir una corrida larga desde otra terminal (PowerShell):
```powershell
Get-Content reportes\baseline\log.txt -Wait -Tail 20 -Encoding UTF8 | Select-String -NotMatch "Warning"
```

## Qué hay en cada carpeta

| Carpeta | Contenido | ¿En git? |
|---|---|---|
| `src/` | Scripts numerados en orden de ejecución. `fe.py` tiene **la única definición** de features (con deflactación opcional) y de la clase. `deflactar.py` define los brazos. `comun.py` tiene los meses, la ganancia y las funciones compartidas. | sí |
| `docs/` | `hoja_de_ruta.md` (plan por pasos), `investigacion.md` (documento del experimento), `paso10_clasificacion.md` (columnas y deflactores, para discutir) | sí |
| `DECISIONES.md` | Qué se decidió, por qué y qué se descartó, más los resultados (R1, …) | sí |
| `datos_externos/` | Índices mensuales (IPC, RIPTE, tasas, CER, tipo de cambio), las descargas en bruto y `FUENTES.md` | sí |
| `reportes/` | Resultados de cada paso: tablas, curvas y logs | sí |
| `modelos/` | Modelos finales de LightGBM (`.txt`) y estudios de Optuna (`.db`) | sí (pocos MB) |
| `historia/` | Un parquet por mes, generado por `00_convertir_a_parquet.py` (830 MB) | **no**, se regenera |
| `datasets/` | Features por mes, generadas por `02_dataset.py` (570 MB) | **no**, se regenera |

## Esquema de referencia

- Solo 2019. Entrena 201903–201906 con BAJA+1 y BAJA+2 combinadas.
- Valida 201908 con AUC (Optuna y early stopping).
- Test en 201910 con ganancia: +1.072.500 por cada BAJA+2 y −27.500 por envío. Para el test se reentrena con 201903–201908 y se usa el N elegido en 201908.
- **Resultado: 281,6 M en 201910 con 5.000 envíos.** El detalle está en `DECISIONES.md` (R1).
