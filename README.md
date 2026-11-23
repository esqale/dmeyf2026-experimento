# Experimento colaborativo "Inflación 1" · DMEyF 2026 (comisión lunes)

Manuel Marasco · Alejandro Esquivel · Alexander Arias

**Pregunta:** ¿deflactar cada grupo de variables monetarias con su propio índice da más ganancia que dividir todo por el IPC? ¿Y deflactar da más que no deflactar?

**Resultado:**
- Deflactar los montos **no mejora la ganancia**: con 5.000 envíos empata con el modelo sin deflactar, y en la zona plana de la curva pierde en casi todas las semillas.
- Por grupo le gana al IPC con los hiperparámetros del baseline, pero **no de forma robusta**: con un Optuna propio por brazo empatan.
- Fuera de la hipótesis, calcular los deltas como **tasa de crecimiento** en lugar de diferencia en pesos suma **+5 M** con 5.000 envíos, en 201909 y en 201910, también con hiperparámetros propios.

**Dónde leer más:**
- `docs/presentacion_final/index.html`: la presentación del video (abrir en el navegador).
- `docs/investigacion.md`: el informe completo, con hipótesis, diseño, limitaciones, resultados y discusión.
- `DECISIONES.md`: cada decisión (D1, D2, …) y cada resultado (R1, R2, …), con el criterio escrito antes de correr cada prueba.

## Esquema

- Solo 2019. Entrena 201903–201906 con BAJA+1 y BAJA+2 combinadas.
- Valida 201908 con AUC (Optuna de 50 intentos y early stopping).
- Test en 201910: se reentrena con 201903–201908 y se mide la ganancia (+1.072.500 por BAJA+2, −27.500 por envío) con N = 5.000, elegido en 201908. Como apoyo, la ganancia media entre 3.000 y 6.500 envíos (zona plana).
- Cada brazo se corre con las mismas 20 semillas y se compara contra el baseline con un test de Wilcoxon pareado.

## Cómo correrlo desde cero

Hace falta Python 3.13 y unos 14 GB de RAM (anda con menos, pero más lento). El dataset de la cátedra (`competencia_02_crudo.csv.gz`) no se publica.

```bash
pip install -r requirements.txt

# 1. Datos: un parquet por mes. Se repite hasta que diga TODO COMPLETO (~2 min en total).
python src/00_convertir_a_parquet.py <ruta>/competencia_02_crudo.csv.gz historia/mensual

# 2. Exploración: tablas en reportes/paso3/
python src/01_exploracion.py

# 3. Dataset del baseline: lag y delta 1 y 2 + clase, 201903–201910 (~40 s)
python src/02_dataset.py

# 4. Baseline: Optuna de 50 trials + test en 201910 (~1 h 45 min; si se corta, se relanza y retoma)
python src/03_baseline.py --dataset datasets/fe_base --nombre baseline

# 5. Ruido por semilla: 20 semillas con los hiperparámetros del baseline (~50 min)
python src/04_semillas.py --dataset datasets/fe_base --nombre baseline

# 6. Índices externos (ya están en datos_externos/; --bajar los vuelve a descargar)
python src/05_indices.py

# 7. Inventario de columnas monetarias: reportes/paso10/
python src/06_monetarias.py

# 8. Brazo "todo con IPC" (IPC del mes anterior y del mismo mes) y sus 20 semillas
python src/02_dataset.py --brazo ipc --desfase 1
python src/02_dataset.py --brazo ipc --desfase 0
python src/04_semillas.py --dataset datasets/fe_ipc_d1 --nombre ipc_d1
python src/04_semillas.py --dataset datasets/fe_ipc_d0 --nombre ipc_d0

# 9. Verificación de monedas y brazo "por grupo" con sus 20 semillas
python src/08_monedas.py
python src/02_dataset.py --brazo grupo
python src/04_semillas.py --dataset datasets/fe_grupo --nombre grupo

# 10. Comparación pareada por semilla (el primero es la referencia)
python src/07_comparar.py baseline ipc_d1 ipc_d0 grupo --salida reportes/comparacion.csv
python src/07_comparar.py ipc_d1 grupo --salida reportes/comparacion_grupo_vs_ipc.csv

# 11. Optuna propio por brazo (chequeo de robustez): mismo comando que el baseline con otro dataset
python src/03_baseline.py --dataset datasets/fe_ipc_d1 --nombre ipc_d1_opt
python src/04_semillas.py --dataset datasets/fe_ipc_d1 --nombre ipc_d1_opt --params reportes/ipc_d1_opt/resultado.json

# 12. Diagnósticos: validación adversarial de los montos y dónde cortan los árboles
python src/10_adversarial.py
python src/11_cortes.py

# 13. Otras formas de corregir la inflación. Cada una: armar el dataset y correr las 20 semillas
#     --brazo ranking          G:  ranking por mes con cero fijo, antes de lags y deltas
#     --brazo ranking_post     G2: ranking después de lags y deltas (necesita fe_base)
#     --brazo nominal_ranking  M:  fe_base + las monetarias de fe_ranking con sufijo _rk
#     --brazo delta_log        H:  deltas relativos, slog(x_t) - slog(x_t-k)
#     --brazo ranking_sin_cero G0: ranking sin cero fijo
#     --brazo grupo_saldos_ipc J:  por grupo con IPC en los 8 saldos
#     --brazo mediana          K:  cada columna / su mediana del mes
#     --brazo grupo --con-mes  L:  por grupo + foto_mes
python src/02_dataset.py --brazo delta_log
python src/04_semillas.py --dataset datasets/fe_delta_log --nombre delta_log

# 14. Deltas relativos en un segundo mes de test (201909, entrenando con 201903–07)
python src/04_semillas.py --dataset datasets/fe_base --nombre baseline_t201909 --test 201909 --entrena-test 0307
python src/04_semillas.py --dataset datasets/fe_delta_log --nombre delta_log_t201909 --test 201909 --entrena-test 0307

# 15. Zona plana definida en validación, tabla de todas las pruebas y figuras del informe
python src/14_zona_validacion.py
python src/12_gain_nominal_rk.py
python src/13_figuras.py
```

Para seguir una corrida larga desde otra terminal (PowerShell):
```powershell
Get-Content reportes\baseline\log.txt -Wait -Tail 20 -Encoding UTF8 | Select-String -NotMatch "Warning"
```

## Qué hay en cada carpeta

| Carpeta | Contenido | ¿En git? |
|---|---|---|
| `src/` | Scripts numerados en orden de ejecución. Módulos comunes: `comun.py` (meses, ganancia, funciones compartidas), `fe.py` (la única definición de lags, deltas y clase), `deflactar.py` (los índices de cada grupo) y `rankear.py`. | sí |
| `docs/` | `investigacion.md` (informe), `presentacion_final/` (presentación del video), `paso10_clasificacion.md` (cada columna monetaria y su deflactor), `investigacion_bibliografica.md`, `figuras/`. En `docs/interno/`, las hojas de ruta y versiones anteriores de la presentación. | sí |
| `DECISIONES.md` | Qué se decidió, por qué y qué se descartó, más los resultados | sí |
| `datos_externos/` | Índices mensuales (IPC, RIPTE, tasas, CER, tipo de cambio), las descargas en bruto y `FUENTES.md` | sí |
| `reportes/` | Resultados de cada prueba: una carpeta por brazo (tabla abajo) y las tablas de comparación | sí |
| `modelos/` | Modelos finales de LightGBM (`.txt`) y estudios de Optuna (`.db`) | sí (pocos MB) |
| `historia/` | Un parquet por mes, generado por `00_convertir_a_parquet.py` (830 MB) | **no**, se regenera |
| `datasets/` | Features por mes, generadas por `02_dataset.py` (570 MB) | **no**, se regenera |

## Qué es cada carpeta de `reportes/`

Cada carpeta de brazo tiene `semillas.csv` (la ganancia de cada una de las 20 semillas) y, si tuvo Optuna, `resultado.json` y `trials.csv`.

| Carpeta | Prueba | Resultado |
|---|---|---|
| `baseline` | Sin deflactar | R1, R2 |
| `ipc_d1` / `ipc_d0` | Todo con IPC, del mes anterior / del mismo mes | R3 |
| `grupo` | Cada grupo con su deflactor | R4 |
| `ipc_d1_opt` / `grupo_opt` | Los dos anteriores con Optuna propio | R5 |
| `ipc_d1_mes` / `ipc_d1_mes_opt` | IPC + `foto_mes` (con y sin Optuna propio) | R6, R7 |
| `grupo_saldos_ipc` / `mediana` / `grupo_mes` | Otras variantes de dividir por un índice (J, K, L) | R17–R19 |
| `ranking` / `ranking_post` / `ranking_sin_cero` | Ranking por mes: con cero fijo, después de deltas, sin cero fijo (G, G2, G0) | R12, R13, R16 |
| `nominal_ranking` | Pesos + ranking (M) | R14 |
| `delta_log` / `delta_log_opt` | Deltas relativos (H), con y sin Optuna propio | R15, R22 |
| `baseline_t201909` / `delta_log_t201909` | Baseline y H con test en 201909 | R20 |
| `adversarial` / `cortes` | Validación adversarial y dónde cortan los árboles | R10, R11 |
| `zona_validacion` | Zona plana definida en 201908 | R21 |
| `paso3` / `paso10` / `sensibilidad_sin_reentreno` | Exploración, inventario de monetarias y test sin reentrenar | D4, D14, D13 |
| `comparacion*.csv` | Comparaciones pareadas; `comparacion_todas.csv` tiene todas las pruebas contra el baseline | — |
