# Decisiones · Experimento "Inflación 1"

Qué se decidió, por qué y qué se descartó. Los resultados de la exploración están en `reportes/paso3/`.

---

## D1 — Meses y clase (esquema de referencia)
- Se usa solo 2019. La clase de la foto *t* se arma con la presencia del cliente en *t+1* y *t+2*. BAJA+1 = no está en *t+1*. BAJA+2 = está en *t+1* y no en *t+2*.
- Meses con clase: 201901–201910. Para la clase de 201910 se mira 201911 y 201912 (es un supuesto a validar). 201911 y 201912 no se usan como meses con clase.
- 201901–201902: solo historia para lags. Entrena 201903–201906, valida 201908 con AUC y testea 201910 con ganancia, reentrenando con 201903–201908 (D13).

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
- Espacio: `learning_rate` 0,01–0,3 (log) · `num_leaves` 8–1024 (log) · `min_data_in_leaf` 10–5000 (log) · `feature_fraction` 0,1–1 · `bagging_fraction` 0,5–1. `bagging_freq` = 1 y el resto en default. La ventana de búsqueda es decisión nuestra.
- Early stopping de 100 rondas sobre el AUC de 201908, con un tope de 5000 rondas.
- Envíos: N es el máximo de la curva de ganancia de 201908 del mejor trial, mirando cortes de a 500.
- Test: reentrena con 201903–201908, con los parámetros y las iteraciones del mejor trial, y mide en 201910 con ese N (D13). El máximo de la curva en 201910 se reporta solo como dato informativo, no para elegir.
- El mismo script corre cualquier dataset con este formato, así que los brazos de deflactación van a ser `--dataset` distintos.

## D8 — Índices externos (`src/05_indices.py`, detalle en `datos_externos/FUENTES.md`)
- Las fuentes son datos.gob.ar (IPC y RIPTE) y la API v4.0 del BCRA (tipo de cambio A3500, tasas, CER y UVA). Lo descargado se guarda y se versiona en `datos_externos/crudo/`.
- Series diarias: el promedio del mes se usa para flujos y el último dato para saldos. Las tasas se pasan a un índice acumulado.
- Tasa de plazo fijo: id 12 (30 días). Se bajó también la de personas humanas (id 1190), que da casi lo mismo.
- Tasa activa: hay dos candidatas, préstamos personales (id 14) y tarjetas (id 1215). La de tarjetas termina en 202004, pero para 2019 alcanza. Se decide en el Paso 10.
- La UVA es el CER reescalado, así que se usa uno solo.

## D9 — Cómo se comparan los brazos (2026-11-15)
- Comparación principal: los tres brazos (sin deflactar, todo con IPC y por grupo) con los hiperparámetros e iteraciones del baseline (R1) y las mismas 20 semillas. Se reentrena con 201903–201908 (D13) y se mide en 201910 (`src/04_semillas.py`).
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

## D13 — Para el test en 201910 se reentrena sumando 201907–08 (2026-11-15)
- El esquema de referencia entrena en 201903–201906 para Optuna (validación en 201908) y **reentrena con 201903–201908** para el test en 201910, con los mismos hiperparámetros e iteraciones. Quedó confirmado en la consulta del 2026-11-15.
- Por un rato se cambió a "sin reentrenar" por una lectura incompleta del texto, y después se revirtió. De ese intervalo quedó una corrida parcial sin reentrenar (5 semillas del baseline, media 283,6 M) en `reportes/sensibilidad_sin_reentreno/`, como sensibilidad. `--entrena-test 0306` la reproduce.

## R1 — Resultado del baseline (2026-11-15, 50 trials, 1 h 45 min)
- Mejor trial: el 32. AUC 0,93294 en 201908 · `learning_rate` 0,0132 · `num_leaves` 104 · `min_data_in_leaf` 1398 · `feature_fraction` 0,514 · `bagging_fraction` 0,680 · 405 iteraciones.
- En 201908 la ganancia es 209,0 M y el máximo de la curva está en N = 5.000.
- **Test 201910: 281,6 M con 5.000 envíos**, unos 381 de los 632 BAJA+2. El máximo de la curva de 201910 es 289,9 M con 3.500, pero es solo un dato informativo.
- Sensibilidad (D13): sin reentrenar, con el modelo de 201903–06, da también 281,6 M con 5.000 envíos (acierta la misma cantidad de BAJA+2). Su máximo es 286,6 M con 5.500.
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

## R3 — Brazo "todo con IPC" y objetivo 1 (2026-11-15, 20 semillas por versión, hiperparámetros del baseline, reentrenando con 201903–08)
- Contra el baseline (pareado por semilla, `reportes/comparacion.csv`):

  | Versión | N = 5.000 | Diferencia | Gana | p Wilcoxon | Zona plana | Diferencia | Gana | p Wilcoxon |
  |---|---|---|---|---|---|---|---|---|
  | Baseline | 284,0 ± 3,3 M | — | — | — | 283,9 ± 1,9 M | — | — | — |
  | IPC mes anterior (`ipc_d1`) | 282,3 ± 3,4 M | −1,8 M | 6/20 | 0,14 | 279,0 ± 1,8 M | −4,9 M | 0/20 | 0,0001 |
  | IPC mismo mes (`ipc_d0`) | 284,0 ± 2,9 M | −0,1 M | 9/20 | 0,81 | 280,4 ± 1,9 M | −3,5 M | 2/20 | < 0,0001 |

- AUC en 201910: 0,9374 y 0,9373, igual que el baseline.
- **Brazo 2: deflactar todo por el IPC no mejora la ganancia. En la zona plana la empeora de forma clara.** Con N fijo, la diferencia no se distingue del ruido.
- **Objetivo 1** (`reportes/comparacion_objetivo1.csv`): el IPC del mismo mes da 1,7 M más que el del mes anterior con N fijo (gana 12/20, p = 0,04) y 1,4 M más en la zona plana (gana 13/20, p = 0,015). Usar el índice del mes anterior cuesta poco, pero algo.
- Limitación: los hiperparámetros son los del baseline (D9), lo que puede favorecerlo. La Optuna por brazo es el chequeo.
- Archivos: `reportes/ipc_d1/` y `reportes/ipc_d0/` (semillas.csv, log_semillas.txt).

## D14 — Brazo 3 "por grupo": clasificación cerrada con criterio propio, para revisar entre los tres (2026-11-15)
Las decisiones 1–5 del Paso 10 se tomaron así para tener el brazo terminado. Si el grupo no está de acuerdo, se cambia `deflactar.GRUPOS` y se vuelve a correr (~1 h). Código: `src/deflactar.py` (`brazo_grupo`), `python src/02_dataset.py --brazo grupo` → `datasets/fe_grupo`.

**Verificación de monedas** (decisión 2, `src/08_monedas.py`, salidas en `reportes/paso10/monedas_*.csv`):
- **Consumos, pagos y adelantos en dólares de tarjeta (`Visa/Master_mconsumosdolares`, `_mpagosdolares`, `_madelantodolares`): están en USD.** Por cliente no se mueven con el dólar (crecimiento anual 1,0 y salto de agosto 1,0, cuando el tipo de cambio sube 35%). La mediana es de 10 (≈ USD 8,5 descontando el factor 1,173), contra 9.053 en pesos, y la moda es 1,16 ≈ USD 1. Además, `mconsumototal` es igual a `mconsumospesos` en el 100% de los casos: el total no suma los dólares. → **Sin deflactar.**
- **Saldos en dólares de tarjeta (`Visa/Master_msaldodolares`): están en pesos.** Por cliente siguen al tipo de cambio (salto de agosto 1,27, crecimiento anual 1,60, contra 1,35 y 1,62 del dólar). → Tipo de cambio.
- **Plazo fijo: las etiquetas parecen cruzadas.** `mplazo_fijo_pesos` sigue al dólar de forma exacta (1,618 y 1,347) y la tienen solo 837 clientes (0,6%). `mplazo_fijo_dolares` no se mueve con el dólar (1,19 y 1,02), la tienen 15.499 clientes (11%) y su moda es 117.300 = 100.000 × 1,173, un monto redondo típico de un plazo fijo en pesos. → **Se deflacta cada columna según cómo se comporta, no según su nombre:** `mplazo_fijo_pesos` por el tipo de cambio y `mplazo_fijo_dolares` por la tasa de plazo fijo. Los nombres no se tocan (criterio de D4).

**Asignación (73 columnas):**

| Grupo | Columnas | Deflactor | Desfase |
|---|---|---|---|
| Consumos y movimientos en pesos, préstamos, rentabilidad y márgenes | 43 | IPC | 1 mes |
| Sueldo | `mpayroll`, `mpayroll2` | RIPTE | 1 mes |
| Saldos en pesos | 7 + `mplazo_fijo_dolares` | Tasa de plazo fijo a 30 días acumulada (`idx_tasa_pf30`) | 0 |
| Dólares expresados en pesos | `mcaja_ahorro_dolares`, `minversion1_dolares`, `mplazo_fijo_pesos`, `Visa/Master_msaldodolares` | Tipo de cambio de fin de mes | 0 |
| Compra y venta de dólares | `mforex_buy`, `mforex_sell` | Tipo de cambio promedio del mes | 0 |
| Comisiones | `mcomisiones`, `_mantenimiento`, `_otras` | Moda mensual de `mcomisiones_mantenimiento` | 0 |
| Límites de tarjeta | `mlimitecompra` → `mconsumototal / mlimitecompra`; `mfinanciacion_limite` → `msaldototal / mfinanciacion_limite` | Se reemplazan por el cociente | — |
| Consumos y pagos en dólares de tarjeta | 6 | Ninguno (USD) | — |

**Por qué cada decisión:**
1. *Saldos → tasa de plazo fijo.* Es lo que plantea la hipótesis, y el brazo IPC ya cubre la alternativa. Ningún índice describe bien los saldos (crecen 1,36–1,43): queda como limitación.
2. *Monedas:* ver la verificación de arriba.
3. *CER y tasa activa quedan sin usar.* No hay préstamos que se muevan como UVA (los hipotecarios crecen 0,95) ni montos de mora. Los préstamos van por IPC. En el video se cuenta como hallazgo: la tabla original de deflactores suponía columnas que el dataset no tiene.
4. *Límites → se reemplazan por el cociente.* Así el brazo tiene las mismas columnas que los otros y la comparación queda limpia. El cociente usa los valores nominales (no tiene unidad), y 0 en el límite da NULL.
5. *Rentabilidad y márgenes → IPC.* En el mes de test valen 0 para todos (D4), así que la elección pesa poco.
6. *Desfase:* 1 mes para IPC y RIPTE, que es lo único disponible al predecir (objetivo 1: cuesta ~1,5 M, R3); 0 para las series del BCRA y para la moda de comisiones, que se calcula con el mismo mes del dataset.
7. *Comisiones:* la moda de mantenimiento sube de a escalones (723,5 → 925,8 en 201903 → 1.092,1 en 201908) y existe en todos los meses, incluidos 201905 y 201910. Si algún mes faltara, se repite la del mes anterior.

**Verificación a mano** (cliente 12311477, 201908): valor, lag1 y delta1 coinciden con el cálculo a mano en las cinco familias de deflactores, en el cociente del límite y en las columnas en USD sin tocar. En 201910, las columnas no monetarias y la clase son idénticas a las del baseline. Ejemplo para el video: este cliente paga 925,8 de mantenimiento en julio y 1.092,1 en agosto. Deflactado por la moda, queda en 723,5 en los dos meses (delta 0): el aumento de lista desaparece.

## R4 — Brazo 3 "por grupo" (2026-11-15, 20 semillas, hiperparámetros del baseline, reentrenando con 201903–08)
- Resumen de los tres brazos (pareado por semilla; `reportes/comparacion.csv` contra el baseline y `reportes/comparacion_grupo_vs_ipc.csv` contra el IPC):

  | Brazo | N = 5.000 | Zona plana | AUC 201910 |
  |---|---|---|---|
  | Sin deflactar (baseline) | 284,0 ± 3,3 M | 283,9 ± 1,9 M | 0,9375 |
  | Todo con IPC (mes anterior) | 282,3 ± 3,4 M | 279,0 ± 1,8 M | 0,9374 |
  | Por grupo | 284,4 ± 3,8 M | 280,4 ± 1,3 M | 0,9373 |

- **Por grupo contra todo con IPC: gana.** +2,1 M con N fijo (14/20, Wilcoxon p = 0,017) y +1,4 M en la zona plana (14/20, p = 0,002). → **Se confirma la primera parte de la hipótesis.**
- **Por grupo contra sin deflactar: no gana.** +0,4 M con N fijo (8/20, p = 0,69: empate) y −3,5 M en la zona plana (1/20, p = 0,0001). → **No se confirma la segunda parte.**
- Ningún brazo cambia el AUC. Lo que cambia es el orden de los clientes en la zona plana de la curva.
- Limitaciones: hiperparámetros del baseline (D9), un solo mes de test, comisiones y rentabilidad en 0 en 201910 (D4). La Optuna por brazo es el chequeo de robustez pendiente.
- Archivos: `reportes/grupo/` (semillas.csv, log_semillas.txt).

## R5 — Chequeo de robustez: Optuna propia por brazo (2026-11-16, 50 trials por brazo, mismo esquema y semilla del sampler que el baseline)
- Cada brazo se optimizó con su propia Optuna (`reportes/ipc_d1_opt/`, `reportes/grupo_opt/`) y después se corrió con las mismas 20 semillas. Se compara con N = 5.000 y en la zona plana, igual que en R3 y R4.
- AUC de validación en 201908 del mejor trial: baseline 0,93294 · IPC 0,93248 · por grupo 0,93222. Los tres eligen N = 5.000 en 201908.

  | Brazo | N = 5.000 | vs baseline | Zona plana | vs baseline | AUC 201910 |
  |---|---|---|---|---|---|
  | Sin deflactar (baseline) | 284,0 ± 3,3 M | — | 283,9 ± 1,9 M | — | 0,9375 |
  | Todo con IPC, Optuna propia | 281,9 ± 3,2 M | −2,1 M (gana 4/20, p = 0,013) | 278,1 ± 1,9 M | −5,8 M (0/20, p = 0,0001) | 0,9360 |
  | Por grupo, Optuna propia | 281,5 ± 4,2 M | −2,5 M (gana 7/20, p = 0,08) | 278,7 ± 1,7 M | −5,2 M (0/20, p = 0,0001) | 0,9357 |

- **Con hiperparámetros propios, los brazos deflactados quedan más abajo que el baseline**, y ahora también en AUC (−0,0015 y −0,0018, peor en las 20 semillas). → **La ventaja del modelo sin deflactar no se explica por los hiperparámetros: el resultado de R4 es robusto.**
- **Por grupo contra IPC, cada uno con su Optuna: empate** (−0,4 M con N fijo, p = 0,84; +0,6 M en la zona plana, p = 0,28; `reportes/comparacion_opt_grupo_vs_ipc.csv`). → **La ventaja de "por grupo" sobre "todo IPC" de R4 (+2,1 M) no se sostiene con hiperparámetros propios.** Es una diferencia chica y depende de la configuración.
- La Optuna propia no mejora a ninguno de los dos brazos (281,9 contra 282,3 y 281,5 contra 284,4). Optimizar el AUC de 201908 no se traslada a la ganancia de 201910, lo mismo que ya se vio en R1.
- Archivos: `reportes/{ipc_d1_opt,grupo_opt}/`, `reportes/comparacion_opt.csv`, `modelos/{ipc_d1_opt,grupo_opt}_{final.txt,optuna.db}`.

## D15 — Brazo diagnóstico E: IPC + `foto_mes` (criterio fijado ANTES de correrlo, 2026-11-16 15:55)
- Pregunta: ¿deflactar empeora porque borra la pista del mes que dan los montos nominales? (idea de la versión de Manuel, hoja de ruta v2).
- Brazo: `datasets/fe_ipc_d1_mes` = `fe_ipc_d1` + la columna `foto_mes_feature` (copia de `foto_mes`). Mismos hiperparámetros del baseline, las mismas 20 semillas, N = 5.000 y zona plana.
- Aviso previo: en el test todos los clientes tienen el mismo `foto_mes` (201910, fuera del rango de entrenamiento), así que la columna no puede reordenar clientes dentro del mes. Solo puede ayudar separando los efectos de cada mes durante el entrenamiento. Se espera un efecto chico.
- **Criterio de lectura** (comparación pareada E contra `ipc_d1`, Wilcoxon p < 0,05 y que gane en al menos 15 de 20 semillas):
  - E le gana a `ipc_d1` y se acerca al baseline → deflactar confundía los efectos de cada mes durante el entrenamiento, y `foto_mes` lo corrige.
  - E empata con `ipc_d1` → lo que se pierde al deflactar no es "de qué mes es la fila", sino el monto nominal en sí (comisiones de lista, cuotas fijas, ceros). No descarta que deflactar borre información.
  - Por el aviso previo, que no gane no es evidencia contra la hipótesis del mes en general: solo dice que, para un único mes de test, no se recupera nada.
- Optuna propia de E: después, como chequeo, si da el tiempo.

## R6 — Brazo diagnóstico E: IPC + `foto_mes` (2026-11-16, 20 semillas, hiperparámetros del baseline; criterio en D15)
- **E contra `ipc_d1`: empate.** +0,7 M con N fijo (gana 8/20, p = 0,49) y +0,6 M en la zona plana (13/20, p = 0,31). El AUC es igual. No cumple el criterio (p < 0,05 y al menos 15/20).
- E contra el baseline: 282,9 M contra 284,0 M con N fijo (p = 0,14), y 279,6 M contra 283,9 M en la zona plana (gana 1/20, p = 0,0002). Sigue abajo, igual que el IPC solo.
- **Lectura según D15:** lo que se pierde al deflactar no es "de qué mes es la fila". Devolverle el mes al modelo no recupera la ganancia, así que la pérdida tiene que venir del monto nominal en sí (comisiones de lista, cuotas fijas, ceros). Con un único mes de test no se puede descartar que el mes importe en otros diseños.
- Archivos: `reportes/ipc_d1_mes/` (semillas.csv, log_semillas.txt, comparacion.txt). La Optuna propia de E (`reportes/ipc_d1_mes_opt/`) quedó corriendo como chequeo.

## R7 — Brazo E con Optuna propia (2026-11-17, 50 trials, 20 semillas)
- Optuna: mejor AUC de validación en 201908, 0,93191 (trial 23, 156 iteraciones). En 201908 elige N = 4.000; para comparar se sigue usando N = 5.000, como en el resto de los brazos.
- **E contra `ipc_d1_opt` (los dos con Optuna propia): empate en ganancia.** −0,7 M con N fijo (gana 10/20, p = 0,68) y −0,3 M en la zona plana (7/20, p = 0,55). El AUC de 201910 sube apenas, +0,0005 (16/20, p = 0,02), pero no se traduce en ganancia.
- E contra el baseline: 281,2 M contra 284,0 M con N fijo (6/20, p = 0,04), y 277,8 M contra 283,9 M en la zona plana (1/20, p = 0,0001).
- **Confirma R6 con hiperparámetros propios:** agregar `foto_mes` no recupera lo que se pierde al deflactar.
- Archivos: `reportes/ipc_d1_mes_opt/` y `modelos/ipc_d1_mes_opt_{final.txt,optuna.db}`.

## D16 — Métrica adicional: el máximo de la curva de ganancia en 201910 (2026-11-17)
- `src/07_comparar.py` ahora informa también el máximo de la curva (cortes de a 500 envíos), con el mismo test pareado. Todas las tablas de `reportes/comparacion*.csv` se regeneraron con esa columna.
- **Es optimista:** supone conocido de antemano el mejor N del mes de test. La métrica principal sigue siendo la ganancia con N = 5.000, elegido en 201908 sin mirar el test. Se informa porque es la métrica de la versión de Manuel y para mostrar que la conclusión no depende de cómo se mide.
- Resultado con esta métrica (20 semillas, Wilcoxon pareado): **el orden de los brazos y las conclusiones son los mismos que con N fijo y con la zona plana.**

  | Comparación | Diferencia | Gana | p |
  |---|---|---|---|
  | IPC contra sin deflactar | −5,3 M | 0/20 | 0,0001 |
  | Por grupo contra sin deflactar | −3,6 M | 1/20 | 0,0002 |
  | Por grupo contra IPC (hiperparámetros del baseline) | +1,7 M | 15/20 | 0,007 |
  | Por grupo contra IPC (Optuna propia) | +0,6 M | 12/20 | 0,46 |
  | IPC + `foto_mes` contra IPC | +0,5 M | 9/20 | 0,76 |
  | IPC con Optuna propia contra sin deflactar | −6,5 M | 0/20 | 0,0001 |
  | Por grupo con Optuna propia contra sin deflactar | −5,9 M | 1/20 | 0,0001 |

## R8 — Hiperparámetros de la versión de Manuel en nuestro pipeline (2026-11-17, 20 semillas)
- Para ver si los dos modelos base son equivalentes: se toman los hiperparámetros que eligió su Optuna (num_leaves 218, learning_rate 0,0182, min_data_in_leaf 1540, feature_fraction 0,887, bagging_fraction 0,657) y se corren en nuestro pipeline, con nuestro dataset `fe_base` y las mismas 20 semillas que el baseline. Así la comparación es pareada y solo cambian los hiperparámetros.
- Como su notebook no guarda las iteraciones, se sacan igual que en un trial nuestro (`src/09_params_fijos.py`): entrena 201903–06, early stopping de 100 rondas sobre el AUC de 201908, semilla 100129. Resultado: 283 iteraciones (nuestro baseline: 405) y AUC de 201908 = 0,93200 (nuestro baseline: 0,93294).
- **Ganancia: empate.** Con N fijo, +1,3 M a favor de sus hiperparámetros (gana 13/20, p = 0,12). En la zona plana, −1,1 M (7/20, p = 0,10). Máximo de la curva, −1,2 M (6/20, p = 0,13). Ninguna diferencia es significativa y cambian de signo según la métrica.
- **AUC de 201910: nuestro baseline es mejor** (0,9375 contra 0,9361; gana en las 20 semillas, p < 0,0001).
- Conclusión: en ganancia, nuestro modelo base es igual al de la versión de Manuel; en AUC, de validación y de test, es mejor. El óptimo de hiperparámetros es plano, como se esperaba.
- Archivos: `reportes/baseline_manuel/` y `reportes/comparacion_baseline_manuel.csv`.

## D17 — Validación adversarial de los montos (criterio fijado ANTES de correrla, 2026-11-17)
- **Pregunta:** ¿deflactar les saca el drift a las columnas monetarias? La ganancia no lo contesta: un brazo puede perder ganancia y aun así haber hecho bien su trabajo, o al revés. La idea viene de la versión de Manuel (`7_drift.ipynb`), que la corrió con todas las columnas. Ahí las no monetarias (`tmobile_app`, fechas de tarjeta) separan los meses solas, el AUC queda pegado a 1 y no se pueden comparar los brazos.
- **Diseño** (`src/10_adversarial.py`):
  - Datasets `fe_base`, `fe_ipc_d1` y `fe_grupo`, ya construidos (mismas columnas; en por grupo, los límites ya son ratios).
  - Solo columnas monetarias, en dos conjuntos: (a) las 73 del mes y (b) las 73 con sus lags y deltas (365).
  - Dos pares de meses: 201903 contra 201910 (el de Manuel) y 201908 contra 201910 (último mes de entrenamiento contra el de test).
  - **Multivariada:** LightGBM (learning_rate 0,05, 31 hojas, hasta 300 rondas, early stopping 30) que predice el mes. Split 70/30 estratificado y AUC en el 30%. Se repite con las 5 primeras de nuestras 20 semillas.
  - **Univariada:** AUC de cada columna sola para separar los dos meses (los NaN cuentan como el valor más bajo). Drift = |AUC − 0,5|. Se informa la mediana y cuántas columnas superan 0,05.
- **Criterio:**
  - Un brazo *reduce el drift* si su AUC multivariado es menor que el del nominal en las 5 semillas y por al menos 0,01 en promedio, o si la mediana del drift univariado baja a la mitad o menos.
  - Si el AUC multivariado supera 0,99 en los tres brazos, se declara saturado y se decide solo con la univariada.
  - Se mira primero el conjunto (a) con 201903 contra 201910; los otros tres casos son de apoyo.
- **Qué significaría cada resultado:**
  - Si deflactar *reduce* el drift y aun así pierde ganancia, el drift de los montos no le molestaba al modelo.
  - Si *no lo reduce*, los índices no describen cómo se mueven los montos (coherente con la explicación 3 de la Discusión), y deflactar no podía ayudar.
