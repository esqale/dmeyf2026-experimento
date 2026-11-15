# Decisiones · Experimento "Inflación 1"

Qué se decidió, por qué y qué se descartó. Los resultados de la exploración están en `reportes/paso3/`.

---

## D1 — Meses y clase (baseline de Bolaños, #Experimentos - Lunes › Baseline + Entregables)
- Se usa solo 2019. La clase de la foto *t* se arma con la presencia del cliente en *t+1* y *t+2*. BAJA+1 = no está en *t+1*. BAJA+2 = está en *t+1* y no en *t+2*.
- Meses con clase: 201901–201910. Para la clase de 201910 se mira 201911 y 201912 (es un supuesto a validar). 201911 y 201912 no se usan como meses con clase.
- 201901–201902: solo historia para lags. Entrena 201903–201906, valida 201908 con AUC y testea 201910 con ganancia, reentrenando con 201903–201908.

## D2 — Historia en parquet por mes
- `historia/mensual/<yyyymm>.parquet`: 32 meses, 4.707.495 filas, 154 columnas. No hay duplicados `(numero_de_cliente, foto_mes)` ni ids nulos (`01_exploracion.py`, sección a).
- Se borró `historia/_to_delete/` (intentos de conversión corruptos).

## D3 — Cliente 48000000
- En el crudo viene como `4.8e+07`. Es un cliente real y siempre el mismo: aparece en los 32 meses, `cliente_antiguedad` sube de a 1 (80 → 111) y hay otros 11 ids entre 47.999.000 y 48.001.000. Se guarda como entero.

## D4 — Limpieza: las columnas rotas quedan como están
- Paso 3: hay 7 columnas de comisiones y rentabilidad en 0 para el 100% de los clientes en 201905 y en 201910. En 201910 también quedan en 0 `chomebanking_transacciones` y los descuentos. En 201904 pasa lo mismo con `c/mttarjeta_visa_debitos_automaticos`. Detalle en `reportes/paso3/`.
- Decisión (2026-11-15): no se corrigen. Es lo más fiel a cómo llegan los datos en la realidad, donde un mes roto llega sin aviso.
- Consecuencia para el experimento: en el test (201910) esas columnas valen 0 para todos y sus deltas dan menos el valor del mes anterior. El deflactor de esos grupos no puede cambiar nada en ese mes. Va en Limitaciones.
- **Descartado:** pasarlas a NULL en el mes roto, o sacarlas.

## D5 — Ganancia
- +1.072.500 por cada BAJA+2 estimulado y −27.500 por cualquier otro estimulado. Son los mismos valores de la Competencia 1, confirmados por el usuario para este dataset.

## D6 — Feature engineering base (`src/fe.py`, una sola función para todos los brazos)
- Columnas crudas, más lag 1 y 2 y delta 1 y 2 de las 152 variables: 760 features en float32.
- El lag es por calendario: es el valor del mismo cliente en t-k. Si el cliente no estaba ese mes, queda NULL, y no se toma la fila anterior que exista. Por eso, los clientes sin lag1 coinciden con las altas del mes.
- `numero_de_cliente` y `foto_mes` no son features.

## D7 — Optimización del baseline (`src/03_baseline.py`)
- Optuna TPE con semilla 102191 y 50 trials. El estudio se guarda en SQLite y retoma si se corta.
- Espacio: `learning_rate` 0,01–0,3 (log) · `num_leaves` 8–1024 (log) · `min_data_in_leaf` 10–5000 (log) · `feature_fraction` 0,1–1 · `bagging_fraction` 0,5–1. `bagging_freq` = 1 y el resto en default. Es la ventana del HTML de canaritos de la cátedra.
- Early stopping de 100 rondas sobre el AUC de 201908, con un tope de 5000 rondas.
- Envíos: N es el máximo de la curva de ganancia de 201908 del mejor trial, mirando cortes de a 500 (el criterio de la cátedra).
- Test: reentrena con 201903–201908, con los parámetros y las iteraciones del mejor trial, y mide en 201910 con ese N. El máximo de la curva en 201910 se reporta solo como dato informativo, no para elegir.
- El mismo script corre cualquier dataset con este formato, así que los brazos de deflactación van a ser `--dataset` distintos.

## D8 — Índices externos (`src/05_indices.py`, detalle en `datos_externos/FUENTES.md`)
- Las fuentes son datos.gob.ar (IPC y RIPTE) y la API v4.0 del BCRA (tipo de cambio A3500, tasas, CER y UVA). Lo descargado se guarda y se versiona en `datos_externos/crudo/`.
- Series diarias: el promedio del mes se usa para flujos y el último dato para saldos. Las tasas se pasan a un índice acumulado.
- Tasa de plazo fijo: id 12 (30 días). Se bajó también la de personas humanas (id 1190), que da casi lo mismo.
- Tasa activa: hay dos candidatas, préstamos personales (id 14) y tarjetas (id 1215). La de tarjetas termina en 202004, pero para 2019 alcanza. Se decide en el Paso 10.
- La UVA es el CER reescalado, así que se usa uno solo.

## D9 — Cómo se comparan los brazos (2026-11-15)
- Comparación principal: los tres brazos (sin deflactar, todo con IPC y por grupo) con los hiperparámetros e iteraciones del baseline (R1) y las mismas 20 semillas. Se reentrena con 201903–201908 y se mide en 201910 (`src/04_semillas.py`).
- Métrica: ganancia con N fijo = 5.000 (elegido en 201908 por el baseline). Se reportan también la ganancia media en la zona plana (3.000–6.500) y el AUC de 201910. La comparación es pareada por semilla (Wilcoxon).
- Chequeo de robustez, si sobra tiempo: una optimización de Optuna propia para cada brazo (`03_baseline.py` con otro `--dataset`) y después sus 20 semillas.
- **Descartado:** usar solo la Optuna por brazo. Mezcla el ruido de la búsqueda con el efecto de deflactar y cuesta el triple.

## D10 — Paso 10: la clasificación queda como propuesta (2026-11-15)
- `docs/paso10_clasificacion.md`: 73 columnas en 11 grupos, con la evidencia de `src/06_monetarias.py` (crecimiento del mismo cliente entre 201901 y 201912, y entre 201907 y 201908, contra cada índice).
- Hallazgos que cambian la tabla de deflactores de `docs/investigacion.md`:
  - Los saldos en "dólares" están en pesos al tipo de cambio, y los consumos y pagos en dólares de tarjeta parecen estar en USD.
  - `mplazo_fijo_pesos` y `mplazo_fijo_dolares` podrían estar cruzadas.
  - No hay préstamos que se muevan como UVA ni columnas en pesos de mora.
  - Los límites suben de a escalones.
- **Pendiente:** decisión del grupo sobre las 5 preguntas del final del documento.

## D11 — Investigación.md actualizada (2026-11-15)
- Se corrigió la bibliografía (RIPTE, UVA y SR 11-7) y se agregaron las series concretas, el esquema del experimento, los hallazgos de los datos, las limitaciones y el resultado preliminar del baseline.

## D12 — Brazo "todo con IPC" y objetivo 1 (2026-11-15)
- `fe.features_mes(deflactor=...)`: cada valor se divide por el índice de **su propio mes** antes de los lags y deltas. El lag1 de t se divide por el índice de t-1, y el delta es la diferencia de los valores ya deflactados. Sin deflactor, el dataset sale idéntico al del baseline (0 filas distintas en 201905 y 201910).
- `src/deflactar.py`: índices normalizados a 201901 = 1. `desfase` = cuántos meses atrás se toma el índice.
- Brazo 2 = las 73 columnas monetarias (`m*`, `Visa_m*`, `Master_m*`) divididas por el IPC.
  - `datasets/fe_ipc_d1`: IPC del mes anterior. Es la única que se puede usar al momento de predecir, y la oficial del brazo.
  - `datasets/fe_ipc_d0`: IPC del mismo mes. Solo para el objetivo 1.
- Verificación a mano (cliente 48000000, 201904): `mrentabilidad`, el lag1 y el delta1 coinciden con el cálculo hecho a mano en las dos versiones. `cliente_edad` no cambia.
- Comparación: `src/07_comparar.py`, pareado por semilla (Wilcoxon y t pareado), con la ganancia a N fijo, la zona plana y el AUC.

## R1 — Resultado del baseline (2026-11-15, 50 trials, 1 h 45 min)
- Mejor trial: el 32. AUC 0,93294 en 201908 · `learning_rate` 0,0132 · `num_leaves` 104 · `min_data_in_leaf` 1398 · `feature_fraction` 0,514 · `bagging_fraction` 0,680 · 405 iteraciones.
- En 201908 la ganancia es 209,0 M y el máximo de la curva está en N = 5.000.
- **Test 201910: 281,6 M con 5.000 envíos.** Equivale a unos 381 de los 632 BAJA+2. El máximo de la curva de 201910 es 289,9 M con 3.500, pero es solo un dato informativo.
- La curva de 201910 es plana entre 3.000 y 6.500 envíos (280–290 M). Elegir N cuesta como mucho unos 8 M.
- Los mejores trials quedan a menos de 0,0005 de AUC entre sí, y su ganancia en 201908 (205–215 M) no sigue el orden del AUC.
- Archivos: `reportes/baseline/` (resultado.json, trials.csv, curva_201910.csv, log.txt) y `modelos/baseline_final.txt`.

## R2 — Ruido por semilla del baseline (Paso 7, 2026-11-15, 20 semillas, 55 min)
- **Ganancia en 201910 con N = 5.000: media 284,0 M · desvío 3,3 M · rango 279,4–289,3 M.** El IC 95% de la media es ±1,5 M.
- Ganancia media en la zona plana (3.000–6.500): media 283,9 M · **desvío 1,9 M**. Tiene casi la mitad del ruido, así que conviene usarla como métrica secundaria para comparar brazos.
- AUC en 201910: 0,93749 ± 0,00036.
- El máximo de la curva en 201910 cae siempre entre 3.500 y 4.500 envíos (media 290,5 M). N = 5.000 deja unos 6,5 M sobre la mesa. Es un dato informativo: no se usa para elegir N, porque 201910 es el mes de test.
- Consecuencia: con 20 semillas pareadas, una diferencia entre brazos de unos 2–3 M ya se puede distinguir del azar. Diferencias de 1 M no.
- Archivos: `reportes/baseline/semillas.csv`, `probs_201910.parquet` (no está en git) y `log_semillas.txt`.
