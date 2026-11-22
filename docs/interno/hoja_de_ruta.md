# Hoja de ruta · Experimento colaborativo "Inflación 1"

DMEyF 2026, comisión lunes · Manuel Marasco, Alejandro Esquivel y Alexander Arias · actualizada el 2026-11-15

**Hipótesis:** deflactar cada grupo de variables monetarias con su propio índice da más ganancia que dividir todo por el IPC, y deflactar da más que no deflactar.
**Entrega:** video grupal de 10 minutos, **23/11 antes del mediodía**. Se discute en clase el 24/11.
**Documento:** `docs/investigacion.md`. El esquema de referencia (meses, modelo y métrica) está en `DECISIONES.md` (D1, D7 y D13).

Los números de paso son los de la versión original, así siguen valiendo las referencias de `DECISIONES.md`.

Estado: ✅ hecho · 🔄 en curso · 🟡 esperando una decisión del grupo · ⬜ pendiente

## Preparar los datos
- ✅ **Paso 2. Convertir el dataset** a un parquet por mes (`src/00_convertir_a_parquet.py`).
- ✅ **Paso 3. Exploración y clase** (`src/01_exploracion.py`). La clase llega hasta 201910, y para armarla se usa la presencia del cliente en 201911 y 201912. Hay columnas rotas en 201904, 201905 y 201910 (D4).
- ✅ **Paso 4. Inventario de columnas monetarias** (`src/06_monetarias.py`): las 73 columnas y cómo se mueven frente a cada índice.

## Baseline (es el brazo "sin deflactar")
- ✅ **Paso 5. FE base**: lag y delta 1 y 2, en una sola función (`src/fe.py`).
- ✅ **Paso 6. Modelo base** con el esquema de referencia (`src/03_baseline.py`):
  - Entrena 201903–201906 completos, sin sampling, con BAJA+1 y BAJA+2 combinadas.
  - Optimiza `num_leaves`, `learning_rate`, `min_data_in_leaf`, `feature_fraction` y `bagging_fraction`, con `bagging_freq` = 1.
  - Valida 201908 con AUC (optimización y early stopping) y testea 201910 con ganancia.
  - Resultado: 281,6 M (R1).
  - Para el test se reentrena con 201903–201908 (D13).
- ✅ **Paso 7. Ruido por semilla (objetivo 2)** (`src/04_semillas.py`): 284,0 ± 3,3 M con 20 semillas (R2).

## Deflactación
- ✅ **Paso 8. Índices y bibliografía** (`src/05_indices.py`, `datos_externos/FUENTES.md`).
- 🔄 **Paso 9. Índice del mes anterior (objetivo 1).** Se compara el brazo IPC con el índice de t-1 contra el mismo brazo con el de t (`ipc_d1` contra `ipc_d0`).
- 🟡 **Paso 10. Clasificar las columnas y asignar deflactor (objetivo 3).** La propuesta está en `docs/paso10_clasificacion.md` y faltan las 5 decisiones del grupo.
- 🔄/⬜ **Paso 11. Comparar los tres brazos (objetivo 4)** (`src/07_comparar.py`):
  - Sin deflactar ✅.
  - Todo con IPC 🔄.
  - Por grupo ⬜: necesita el Paso 10.

  Todos con las mismas 20 semillas y comparación pareada.
- ⬜ **Paso 11b (opcional).** Una Optuna propia para cada brazo, como chequeo de robustez.

## Entrega
- ⬜ **Paso 12a.** Completar Resultados, Discusión y Conclusión en `docs/investigacion.md`.
- ⬜ **Paso 12b.** Guion, gráficos, grabación y entrega del video (10 minutos como máximo). Tiene que ser directo, claro y no aburrido. No se suben slides, pero su estructura guía el video:
  1. **Hipótesis:** qué se experimenta y qué se espera.
  2. **Diseño experimental:** cómo fue el método.
  3. **Limitaciones** de lo que se probó.
  4. **Resultados.**
  5. **Conclusiones** y qué seguiríamos experimentando.

  La bibliografía se comparte por Zulip junto con el video. La plantilla de referencia, la plantilla de la cátedra (`experimentos_colaborativos_2026_google_slides.pptx`, no versionada), tiene 10 secciones: Hipótesis, Bibliografía, Sesgos, Diseño, Limitaciones, Resultados (sin interpretar), Discusión (resultados ↔ hipótesis y ↔ otros problemas), Conclusiones, Futuros y Anexo. El Anexo es el link al repo con los scripts, cómo correrlos desde el dataset y las salidas: este repo ya lo cubre.

## Decisiones a hablar entre los tres
- Las 5 preguntas de `docs/paso10_clasificacion.md`.
- Quién hace el guion y los gráficos del video.
