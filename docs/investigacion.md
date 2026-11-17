**Deflactar** es convertir un monto a los precios de un mes de referencia, para poder comparar montos de meses distintos.

Se hace dividiendo el monto por el índice de precios de su mes, y multiplicándolo por el índice del mes de referencia:

monto deflactado \= monto ÷ índice del mes × índice del mes de referencia

### **Ejemplo**

Tomamos enero 2019 como mes de referencia. El IPC de enero 2019 es 100 y el de enero 2020 es 200 (los precios se duplicaron).

|  | Monto en el extracto | IPC del mes | Deflactado |
| :---- | :---- | :---- | :---- |
| Cliente A, enero 2019 | \$50.000 | 100 | 50.000 ÷ 100 × 100 \= **\$50.000** |
| Cliente B, enero 2020 | \$60.000 | 200 | 60.000 ÷ 200 × 100 \= **\$30.000** |

Sin deflactar, B parece tener más plata que A. Deflactado se ve lo que pasa de verdad: B tiene el 60% de lo que tenía A.

### **Hipótesis**

> Usar un deflactor distinto para cada grupo de variables da más ganancia que dividir todas las variables por el IPC.

**¿Por qué?** las variables del banco no se mueven todas igual. Un consumo sigue los precios mes a mes. Una comisión está quieta y de golpe salta. Un límite de tarjeta puede quedar congelado un año. Si divido las tres por el IPC, arreglo la primera y a las otras dos les meto una caída que nunca existió.

**Qué esperamos ver:**

| Modelo | Ganancia esperada |
| ----- | ----- |
| Sin deflactar | la más baja |
| Todo con IPC | en el medio |
| Cada grupo con su deflactor | la más alta |

**Cómo sabemos que nos equivocamos:** si los dos últimos empatan, o si el de grupos pierde. Eso querría decir que al modelo no le molesta que algunas variables queden mal ajustadas, y que no valía la pena el trabajo de clasificarlas.

### **Objetivo general**

**Objetivo**: determinar si usar un deflactor específico por tipo de variable monetaria mejora la ganancia frente a deflactar todo con el IPC, y si deflactar mejora frente a no hacerlo.

### **Objetivos específicos**

**1\. Verificar que usar el índice del mes anterior no cambia los resultados.**

Cuando predecimos junio, el índice de junio todavía no está publicado. Entonces usamos el de mayo. Hay que comprobar que eso da el mismo resultado que usar el de junio verdadero, porque si no, todo lo que venga después no sirve.

**2\. Medir cuánta ganancia se mueve por azar.**

El mismo modelo con otra semilla da un número distinto. Hay que saber cuánto, para después poder decir si una diferencia es real o es ruido.

**3\. Clasificar cada columna monetaria en un grupo y asignarle su deflactor.**

Según quién pone el número y cómo se ajusta: consumos, sueldos, saldos, comisiones, límites, indexadas, mora. Con la justificación de cada asignación.

**4\. Comparar tres modelos.**

Sin deflactar, todo dividido por el IPC, y cada grupo con su propio deflactor.

### **Deflactores concretos a utilizar** 

| Variables | Divisor | De dónde sale el número |
| :---- | :---- | :---- |
| Consumos con tarjeta, débitos, pagos | IPC | INDEC, serie mensual |
| Sueldo acreditado | RIPTE | datos.gob.ar |
| Saldos en cuenta, plazos fijos | Tasa de plazo fijo acumulada | BCRA |
| Comisiones y cargos | El valor más frecuente del mes | **dataset** |
| Límites de tarjeta, acuerdos | usar consumo ÷ límite | **dataset** |
| Préstamos UVA | CER | BCRA |
| Saldos en dólares | Tipo de cambio | BCRA |
| Mora, punitorios | Tasa activa | BCRA |

**Bibliografía (claramente la busqué con IA y hay que verificar todo)** 

# 1\. La definición de deflactar

Consumer Price Index Manual: Concepts and Methods (2020). FMI, con Eurostat, OIT, OCDE, UNECE y Banco Mundial. Aprobado por la Comisión de Estadística de la ONU.  
 https\://www\.imf.org/en/Data/Statistics/cpi-manual

*Qué te sirve:* es el manual oficial internacional de índices de precios. Define qué es un índice de precios y para qué se usa. Es la fuente de máxima autoridad que podés citar en este tema.

System of National Accounts 2008, capítulo 15 ("Price and volume measures"). ONU, FMI, OCDE, Eurostat, Banco Mundial.  
 https\://unstats.un.org/unsd/nationalaccount/docs/SNA2008.pdf

*Qué te sirve:* define la distinción entre valores a precios corrientes y a precios constantes, que es exactamente tu definición.

---

# 2\. La hipótesis: cada grupo con su deflactor

Esta es la fuente clave del trabajo.

Handbook on Prices and Volume Measures in National Accounts, edición 2016\. Eurostat. Catálogo KS-GQ-14-005.  
 https\://ec.europa.eu/eurostat/web/products-manuals-and-guidelines/-/ks-gq-14-005

*Qué te sirve:* clasifica los métodos de deflactar en A, B y C. Deflactar cada cosa con el índice que le corresponde es un método A. Usar un índice general cuando existe uno específico es un método peor. Es tu hipótesis escrita como doctrina oficial.

Quarterly National Accounts Manual, edición 2017, cap. 8 ("Price and Volume Measures"). FMI.

*Qué te sirve:* lo mismo, aplicado a series de tiempo y con más detalle práctico.

---

# 3\. Cada deflactor de tu tabla

### IPC (consumos, débitos, pagos)

INDEC. *Metodología del índice de precios al consumidor. Base diciembre 2016 \= 100\.*  
 https\://www\.indec.gob.ar/ftp/cuadros/economia/metodologia\_ipc\_nacional\_2019.pdf

*Qué te sirve:* explica que el IPC mide una canasta de consumo de hogares. Eso justifica usarlo para consumos y no para saldos ni para límites.

### RIPTE (sueldo acreditado)

Secretaría de Seguridad Social. RIPTE. Metodología en la Resolución 2-E/2018 (una fuente la ubica en el Anexo II y otra en el Anexo III; **a verificar**). La metodología vigente es la de la Resolución SSS 3/2021, Anexo I.  
 https\://www\.argentina.gob.ar/trabajo/seguridadsocial/ripte  
 Serie: https\://datos.gob.ar/dataset/sspm-remuneracion-imponible-promedio-trabajadores-estables-ripte

*Qué te sirve:* es el promedio de los sueldos declarados al sistema previsional. Justifica que el sueldo se deflacte con un índice de sueldos y no de precios.

Alternativa oficial: INDEC, Índice de salarios. Metodología aprobada por el Decreto 1242/2002, art. 2\.

### Tasa de plazo fijo (saldos)

BCRA. Estadísticas de tasas de interés.  
 https\://www\.bcra.gob.ar/PublicacionesEstadisticas/

*Qué te sirve:* es el dato oficial. El argumento de por qué usarlo acá lo pone el Handbook de Eurostat: hay que deflactar con el índice que corresponde al flujo, y un saldo crece también por el interés que cobra.

*Aviso:* este es el deflactor más discutible de tu tabla. Conviene probar tasa e IPC y reportar los dos.

### El valor más frecuente del mes (comisiones)

Acá estás construyendo tu propio índice desde los datos. Eso tiene respaldo:

Consumer Price Index Manual (2020), capítulo 10: Scanner Data.  
 https\://www\.imf.org/-/media/Files/Data/CPI/chapter-10-scanner-data.ashx

*Qué te sirve:* es un capítulo nuevo del manual, dedicado a construir índices de precios a partir de registros de transacciones en lugar de relevamiento manual. Es exactamente lo que vas a hacer con las comisiones. Te permite decir que no estás inventando un método: estás aplicando uno que el manual oficial reconoce.

### Consumo ÷ límite (límites de tarjeta)

Sé honesto acá: el respaldo no viene de estadística de precios, viene de riesgo crediticio.

Siddiqi, N. (2017). *Intelligent Credit Scoring*, 2.ª ed. Wiley.

*Qué te sirve:* el cociente saldo/límite ("tasa de utilización") es una variable estándar en modelos de riesgo de crédito desde hace décadas. No la estás inventando: la estás usando como se usa en la industria.

### CER (préstamos UVA)

Decreto 214/2002, art. 4 (crea el CER).  
 Comunicaciones "A" 5945 y "A" 6069 del BCRA (crean y reglamentan la UVA, ajustada por CER). La Ley 25.827 aparece citada como marco legal de la UVA, pero **el artículo no se pudo confirmar**. No confundirla con la UVI, que es de la Ley 27.271.  
 https\://www\.bcra.gob.ar/archivos/Pdfs/comytexord/A6069.pdf

*Qué te sirve:* esos saldos están atados al CER por contrato. No es una elección tuya, es lo que dice la norma. Ojo: la UVA es el CER reescalado (UVA = 14,05 × CER(t−1) / CER(31/3/2016)), así que como deflactores son el mismo índice.

### Tipo de cambio (saldos en dólares)

BCRA, Comunicación "A" 3500: tipo de cambio de referencia.  
 https\://www\.bcra.gob.ar/PublicacionesEstadisticas/

### Tasa activa (mora, punitorios)

BCRA. Estadísticas de tasas de interés. Misma fuente que arriba.

---

# 4\. Objetivo 1: usar el índice del mes anterior

Esto necesita dos justificaciones distintas.

a) Que el índice del mes no está publicado todavía:

INDEC. Calendario de publicaciones y informes técnicos del IPC.  
 https\://www\.indec.gob.ar/Nivel4/Tema/3/5/31

*Qué te sirve:* el IPC de cada mes se publica a mediados del mes siguiente. Es un hecho verificable, no una suposición.

b) Que usar un dato que no existía al momento de predecir es un error metodológico:

Kaufman, S., Rosset, S., Perlich, C. & Stitelman, O. (2012). "Leakage in Data Mining: Formulation, Detection, and Avoidance". *ACM Transactions on Knowledge Discovery from Data*, 6(4), art. 15\.  
 *(versión de conferencia: KDD 2011, pp. 556–563, con tres autores)*

*Qué te sirve:* es el trabajo canónico sobre *data leakage*. Define el problema como usar información sobre el objetivo que no debería estar legítimamente disponible. Es la cita exacta para justificar por qué no podés usar el IPC de junio para predecir junio.

Board of Governors of the Federal Reserve System. *SR 11-7: Guidance on Model Risk Management* (2011). **Reemplazada por la SR 26-2 (abril de 2026)**: el link viejo da 404. Se puede citar como la guía vigente en 2019, aclarando que fue reemplazada.  
 https\://www\.federalreserve.gov/supervisionreg/srletters/SR2602.pdf

*Qué te sirve:* guía oficial de supervisión bancaria. Exige verificar que los insumos del modelo sean consistentes con su diseño y su uso real. Respalda que el modelo tiene que poder funcionar con los datos que existen en producción.

---

# 5\. Objetivo 2: medir cuánto se mueve la ganancia por azar

Dietterich, T. G. (1998). "Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms". *Neural Computation*, 10(7), 1895–1923.

*Qué te sirve:* explica por qué comparar dos modelos con una sola corrida no sirve.

Demšar, J. (2006). "Statistical Comparisons of Classifiers over Multiple Data Sets". *Journal of Machine Learning Research*, 7, 1–30.

*Qué te sirve:* el procedimiento concreto para comparar varios modelos (test de Friedman y post-hoc). Es lo que vas a usar para comparar tus tres brazos.

Bergmeir, C. & Benítez, J. M. (2012). "On the use of cross-validation for time series predictor evaluation". *Information Sciences*, 191, 192–213.

*Qué te sirve:* justifica que no podés usar validación cruzada al azar con datos que tienen orden temporal.

---

# 6\. Por qué la inflación daña al modelo (fundamento de todo)

Hastie, T., Tibshirani, R. & Friedman, J. (2009). *The Elements of Statistical Learning*, 2.ª ed. Springer, cap. 9–10.

*Qué te sirve:* explica que los árboles son invariantes a transformaciones monótonas. Sirve para decir por qué `log()` no arregla nada, y por qué la inflación sí es un problema (porque multiplica distinto según el mes).

Ke, G. et al. (2017). "LightGBM: A Highly Efficient Gradient Boosting Decision Tree". *NeurIPS 30*.

*Qué te sirve:* describe que LightGBM agrupa cada variable en contenedores (`max_bin`) con bordes calculados sobre todo el entrenamiento. Es el mecanismo por el cual la inflación le come resolución al modelo.

Gama, J. et al. (2014). "A Survey on Concept Drift Adaptation". *ACM Computing Surveys*, 46(4), art. 44\.

*Qué te sirve:* el marco general de "los datos cambian con el tiempo y el modelo se degrada". Es la referencia estándar para encuadrar el problema.

**Inflación 1**  
Manuel Marasco  
Alejandro Esquivel  
Alexander Arias

**¿Es posible mejorar la ganancia acumulada del modelo deflactando los valores de algunos grupos de variables del dataset de clientes?**

- **Hipótesis Experimental:**

Usar un deflactor distinto para cada grupo de variables da más ganancia que dividir todas las variables por el IPC.

**¿Por qué?**   
Las variables del banco no se mueven todas igual. Un consumo sigue los precios mes a mes. Una comisión está quieta y de golpe salta. Un límite de tarjeta puede quedar congelado un año. Si divido las tres por el IPC, arreglo la primera y a las otras dos les meto una caída que nunca existió.

- **Bibliografía:**

- Consumer Price Index Manual: Concepts and Methods (2020). FMI, con Eurostat, OIT, OCDE, UNECE y Banco Mundial. Aprobado por la Comisión de Estadística de la ONU.  
   https\://www\.imf.org/en/Data/Statistics/cpi-manual  
- System of National Accounts 2008, capítulo 15 ("Price and volume measures"). ONU, FMI, OCDE, Eurostat, Banco Mundial.  
   https\://unstats.un.org/unsd/nationalaccount/docs/SNA2008.pdf  
- Handbook on Prices and Volume Measures in National Accounts, edición 2016\. Eurostat. Catálogo KS-GQ-14-005.  
   https\://ec.europa.eu/eurostat/web/products-manuals-and-guidelines/-/ks-gq-14-005  
- Quarterly National Accounts Manual, edición 2017, cap. 8 ("Price and Volume Measures"). FMI.  
- INDEC. *Metodología del índice de precios al consumidor. Base diciembre 2016 \= 100\.*  
   https\://www\.indec.gob.ar/ftp/cuadros/economia/metodologia\_ipc\_nacional\_2019.pdf  
- Secretaría de Seguridad Social. RIPTE. Metodología en la Resolución 2-E/2018 (anexo a verificar) y Resolución SSS 3/2021, Anexo I (vigente).  
   https\://www\.argentina.gob.ar/trabajo/seguridadsocial/ripte  
   Serie: https\://datos.gob.ar/dataset/sspm-remuneracion-imponible-promedio-trabajadores-estables-ripte  
- Alternativa oficial: INDEC, Índice de salarios. Metodología aprobada por el Decreto 1242/2002, art. 2\.  
- BCRA. Estadísticas de tasas de interés.  
   https\://www\.bcra.gob.ar/PublicacionesEstadisticas/  
- Consumer Price Index Manual (2020), capítulo 10: Scanner Data.  
   https\://www\.imf.org/-/media/Files/Data/CPI/chapter-10-scanner-data.ashx  
- Siddiqi, N. (2017). *Intelligent Credit Scoring*, 2.ª ed. Wiley.  
- Decreto 214/2002, art. 4 (crea el CER).  
   Comunicaciones "A" 5945 y "A" 6069 del BCRA (UVA, ajustada por CER). Ley 25.827: artículo a verificar.  
   https\://www\.bcra.gob.ar/archivos/Pdfs/comytexord/A6069.pdf  
- BCRA, Comunicación "A" 3500: tipo de cambio de referencia.  
   https\://www\.bcra.gob.ar/PublicacionesEstadisticas/  
- INDEC. Calendario de publicaciones y informes técnicos del IPC.  
   https\://www\.indec.gob.ar/Nivel4/Tema/3/5/31  
- Kaufman, S., Rosset, S., Perlich, C. & Stitelman, O. (2012). "Leakage in Data Mining: Formulation, Detection, and Avoidance". *ACM Transactions on Knowledge Discovery from Data*, 6(4), art. 15\.  
   *(versión de conferencia: KDD 2011, pp. 556–563, con tres autores)*  
- Board of Governors of the Federal Reserve System. *SR 11-7: Guidance on Model Risk Management* (2011). Reemplazada por la SR 26-2 (2026).  
   https\://www\.federalreserve.gov/supervisionreg/srletters/SR2602.pdf  
- Dietterich, T. G. (1998). "Approximate Statistical Tests for Comparing Supervised Classification Learning Algorithms". *Neural Computation*, 10(7), 1895–1923.  
- Demšar, J. (2006). "Statistical Comparisons of Classifiers over Multiple Data Sets". *Journal of Machine Learning Research*, 7, 1–30.  
- Bergmeir, C. & Benítez, J. M. (2012). "On the use of cross-validation for time series predictor evaluation". *Information Sciences*, 191, 192–213.  
- Hastie, T., Tibshirani, R. & Friedman, J. (2009). *The Elements of Statistical Learning*, 2.ª ed. Springer, cap. 9–10.  
- Ke, G. et al. (2017). "LightGBM: A Highly Efficient Gradient Boosting Decision Tree". *NeurIPS 30*.  
- Gama, J. et al. (2014). "A Survey on Concept Drift Adaptation". *ACM Computing Surveys*, 46(4), art. 44\.

- **Sesgos Cognitivos:**  
1) Puede que los valores de inflación para el año 2019 sobrestimen o subestimen la deflactación de las variables, por lo que el modelo no los tome de buena manera para la predicción.  
2) Puede que las variables con mayor peso en el modelo, no sean las que mejor respondan a la prueba por deflactación.

- **Diseño Experimental:** 

	Para llevar a cabo el experimento, se definieron una serie de objetivos específicos que responden a la misma familia de experimentos, relacionados con la deflactación de las variables para evaluar la incidencia de la inflación en el modelo del churn.

- **Objetivos específicos**  
  1\. Verificar que usar el índice del mes anterior no cambia los resultados: cuando predecimos junio, el índice de junio todavía no está publicado. Entonces usamos el de mayo. Hay que comprobar que eso da el mismo resultado que usar el de junio verdadero, porque si no, todo lo que venga después no sirve.  
  2\. Medir cuánta ganancia se mueve por azar: el mismo modelo con otra semilla da un número distinto. Hay que saber cuánto, para después poder decir si una diferencia es real o es ruido.  
  3\. Clasificar cada columna monetaria en un grupo y asignarle su deflactor: según quién pone el número y cómo se ajusta: consumos, sueldos, saldos, comisiones, límites, indexadas, mora. Con la justificación de cada asignación.  
  4\. Comparar tres modelos: sin deflactar, todo dividido por el IPC, y cada grupo con su propio deflactor.  
    
  **Deflactores a utilizar** 

| Variables | Divisor | De dónde sale el número |
| ----- | ----- | ----- |
| Consumos con tarjeta, débitos, pagos | IPC | INDEC, serie mensual |
| Sueldo acreditado | RIPTE | datos.gob.ar |
| Saldos en cuenta, plazos fijos | Tasa de plazo fijo acumulada | BCRA |
| Comisiones y cargos | El valor más frecuente del mes | **dataset** |
| Límites de tarjeta, acuerdos | usar consumo ÷ límite | **dataset** |
| Préstamos UVA | CER | BCRA |
| Saldos en dólares | Tipo de cambio | BCRA |
| Mora, punitorios | Tasa activa | BCRA |

  **Series concretas** (Paso 8, 2026-11-15; detalle y controles en `datos_externos/FUENTES.md`)

| Deflactor | Serie usada | Fuente |
| ----- | ----- | ----- |
| IPC | IPC nacional, nivel general, base dic-2016 = 100 (`148.3_INIVELNAL_DICI_M_26`) | INDEC vía datos.gob.ar |
| RIPTE | RIPTE en pesos (`158.1_REPTE_0_0_5`) | Seguridad Social vía datos.gob.ar |
| Tasa de plazo fijo acumulada | Depósitos a 30 días, % TNA (id 12), acumulada mes a mes | BCRA, API v4.0 |
| CER | CER, base 2/2/2002 = 1 (id 30) | BCRA |
| Tipo de cambio | Mayorista de referencia, Com. A 3500 (id 5) | BCRA |
| Tasa activa | Préstamos personales (id 14) o tarjetas (id 1215, publicada solo hasta 202004) | BCRA |

Controles contra valores publicados: inflación de 2019 = 53,8% (igual que INDEC), dólar 44,9 → 59,1 después de las PASO y UVA al 31/12/2019 = 47,16.

  **Esquema de referencia del experimento**
  - Solo 2019. La clase llega hasta 201910, y para armarla se usa la presencia en 201911 y 201912.
  - Features: columnas crudas, más lag 1 y 2 y delta 1 y 2. En los brazos 2 y 3, la deflactación se aplica **antes** de calcular los lags y deltas.
  - LightGBM. Optuna optimiza `num_leaves`, `learning_rate`, `min_data_in_leaf`, `feature_fraction` y `bagging_fraction`, con `bagging_freq` = 1. Entrena 201903–201906 completos con BAJA+1 y BAJA+2 combinadas, y valida en 201908 con AUC (también para el early stopping).
  - Envíos: el máximo de la curva de ganancia en 201908, de a 500.
  - Test: reentrena con 201903–201908 y mide la ganancia en 201910 (+1.072.500 por BAJA+2 y −27.500 por envío).
  - Comparación principal: los tres brazos con los hiperparámetros del baseline y las **mismas 20 semillas**, comparados con un test pareado (Wilcoxon). Chequeo de robustez: una optimización de Optuna propia para cada brazo.
  - Brazo "todo con IPC": divide las 73 columnas monetarias por el IPC. Brazo "por grupo": la clasificación del objetivo 3 (`docs/paso10_clasificacion.md`).

  **Hallazgos sobre los datos que afectan al experimento** (Pasos 3 y 10)
  - Hay siete columnas de comisiones y rentabilidad que valen 0 para todos los clientes en 201905 y en 201910. En 201910, además, valen 0 `chomebanking_transacciones` y los descuentos, y en 201904 los débitos automáticos de Visa. Se dejan como están, porque es lo más fiel a cómo llegan los datos en la realidad.
  - Las columnas "dólares" de saldos (`mcaja_ahorro_dolares`, `msaldodolares`) **están en pesos al tipo de cambio**: entre 201907 y 201908 crecen 1,347, igual que el dólar. En cambio, los consumos y pagos en dólares de tarjeta parecen estar en dólares de verdad.
  - `mplazo_fijo_pesos` se mueve como el dólar y `mplazo_fijo_dolares` no: es posible que estén cruzadas.
  - Los límites de tarjeta no cambian entre 201907 y 201908 (1,000) y en el año suben 2,67: **están quietos y suben de a escalones**, como dice la hipótesis.
  - La comisión de mantenimiento más frecuente pasa de 723,5 a 1.092,1 en el año, con un salto del 18% en agosto. Es el patrón "quieta y salta".
  - Los préstamos hipotecarios no se mueven como UVA (0,95 en el año, cuando con UVA se esperaría alrededor de 1,4), y **no hay ninguna columna en pesos de mora o punitorios**. Los grupos "CER" y "tasa activa" quedan casi vacíos.

- **Limitaciones:**
  - En 201910, el mes de test, las comisiones y la rentabilidad valen 0 para todos. Ningún deflactor puede cambiar algo en esas columnas ese mes, y sus deltas dan menos el valor del mes anterior. Esto limita lo que se puede medir del grupo "comisiones".
  - Hay un solo mes de test (201910). Con 632 BAJA+2, unas decenas de aciertos más o menos mueven la ganancia en decenas de millones.
  - 2019 tiene un quiebre (PASO de agosto y cepo de septiembre). Algunas columnas cambian por comportamiento, no por precios, y ningún deflactor lo corrige.
  - La comparación principal usa los hiperparámetros del baseline. Puede favorecer al brazo sin deflactar, porque esos hiperparámetros se optimizaron para él (el chequeo de robustez es la Optuna por brazo).
  - En el brazo IPC + `foto_mes`, el mes de test (201910) queda fuera del rango de entrenamiento, y el árbol lo trata como al último mes visto. Ese brazo prueba "devolverle el mes" solo hasta donde un modelo puede usar un mes que no vio (R9).
  - `mtransferencias_recibidas` casi no existe antes de 201906 (0,1% de clientes con valor distinto de 0, contra 55–62% desde junio): es un corte dentro de la ventana de entrenamiento y afecta a todos los brazos por igual (R10).
  - El mes de referencia del índice no es una limitación: cambiarlo multiplica todo el dataset por una constante, y los árboles son invariantes a eso (R9).
- **Resultados:**
  - *Preliminar, brazo sin deflactar (baseline), una semilla:* AUC 0,9329 en 201908, N = 5.000 elegido en 201908 y **ganancia en 201910 de 281,6 M** (unos 381 de los 632 BAJA+2). La curva de 201910 es plana entre 3.000 y 6.500 envíos (280–290 M).
  - *Ruido por semilla (objetivo 2), brazo sin deflactar, 20 semillas:* ganancia en 201910 con 5.000 envíos de **284,0 M ± 3,3 M** (rango 279,4–289,3 M). En la zona plana de la curva (3.000–6.500 envíos) el desvío baja a 1,9 M. AUC 0,9375 ± 0,0004. Con 20 semillas pareadas, una diferencia de unos 2–3 M entre brazos ya se distingue del azar.
  - *Brazo 2, todo con IPC (IPC del mes anterior), 20 semillas pareadas con el baseline:*
    - Con 5.000 envíos da **282,3 M ± 3,4 M**, 1,8 M menos que el baseline. Gana en 6 de 20 semillas (Wilcoxon p = 0,14), así que con N fijo no se distingue del azar.
    - En la zona plana da **279,0 M**, 4,9 M menos que el baseline. **No gana en ninguna de las 20 semillas** (p = 0,0001).
    - El AUC es igual al del baseline (0,9374).
    - Conclusión: deflactar todo por el IPC **no mejora y, en la zona plana, empeora**. La hipótesis "deflactar da más que no deflactar" no se cumple para el brazo IPC.
  - *Objetivo 1, IPC del mes anterior contra IPC del mismo mes:*
    - Con el IPC del mismo mes, el brazo da 284,0 M con 5.000 envíos (igual que el baseline) y 280,4 M en la zona plana.
    - Contra el del mes anterior, el del mismo mes da 1,7 M más con N fijo (gana 12 de 20, p = 0,04) y 1,4 M más en la zona plana (gana 13 de 20, p = 0,015).
    - La diferencia es chica, del orden del ruido de una semilla, pero consistente: usar el índice del mes anterior (lo único disponible al predecir) cuesta algo. Ninguna de las dos versiones le gana al baseline.
  - *Brazo 3, por grupo (clasificación en DECISIONES.md, D14), 20 semillas pareadas:*
    - Con 5.000 envíos da **284,4 M ± 3,8 M** y en la zona plana **280,4 M ± 1,3 M**. El AUC es 0,9373.
    - **Contra el brazo IPC (mismo desfase): gana.** Da +2,1 M con N fijo (14 de 20 semillas, p = 0,017) y +1,4 M en la zona plana (14 de 20, p = 0,002). La primera parte de la hipótesis se cumple.
    - **Contra el baseline sin deflactar: no gana.** Con N fijo empatan (+0,4 M, p = 0,69). En la zona plana pierde por 3,5 M (gana 1 de 20, p = 0,0001). La segunda parte de la hipótesis no se cumple.
  - *Lectura conjunta:* deflactar por grupo es mejor que deflactar todo por el IPC, pero ninguna forma de deflactar mejora al modelo sin deflactar. Los tres brazos tienen el mismo AUC. Las diferencias están en la forma de la curva de ganancia: los brazos deflactados pierden en la zona plana, aunque empatan en N = 5.000. La salvedad es que todos usan los hiperparámetros optimizados para el baseline.
  - *Chequeo de robustez, Optuna propia por brazo (R5):*
    - Con sus propios hiperparámetros, los brazos deflactados siguen por debajo del baseline. Todo con IPC da 281,9 M con N fijo y 278,1 M en la zona plana. Por grupo da 281,5 M y 278,7 M. En la zona plana pierden en las 20 semillas, y ahora también pierden en AUC (0,9360 y 0,9357 contra 0,9375).
    - **Que no deflactar sea mejor no depende de los hiperparámetros.**
    - En cambio, la ventaja de por grupo sobre todo con IPC desaparece: empatan (p = 0,84 y 0,28). **La primera parte de la hipótesis no es robusta.**
  - *Brazo diagnóstico, IPC + `foto_mes` (R6; idea de la versión de Manuel, criterio fijado antes de correrlo en D15):*
    - Es el brazo IPC con una columna más que le dice al modelo de qué mes es cada fila. Prueba si deflactar empeora porque borra la pista del mes que dan los montos nominales.
    - Resultado: **empata con el IPC solo** (+0,7 M con N fijo, p = 0,49; +0,6 M en la zona plana, p = 0,31) y sigue debajo del baseline.
    - Devolverle el mes al modelo no recupera nada: **lo que se pierde al deflactar no es el mes, sino el monto nominal en sí.**
    - Con su propia Optuna (R7) pasa lo mismo: empata con el IPC optimizado (−0,7 M, p = 0,68) y queda debajo del baseline.
  - *La conclusión no depende de la métrica (D16).* Con el máximo de la curva de 201910, que es la métrica de la versión de Manuel y es optimista porque supone conocido el mejor N del test, el resultado es el mismo:
    - Sin deflactar: 290,5 M. IPC: 285,2 M (0/20 semillas a favor). Por grupo: 286,9 M (1/20).
    - Por grupo le gana al IPC solo con los hiperparámetros del baseline (+1,7 M, p = 0,007). Con Optuna propia empatan (p = 0,46).
    - IPC + `foto_mes` empata con IPC (p = 0,76).
    - Las tres métricas (N fijo, zona plana y máximo) dan el mismo orden.
  - *¿Deflactar les saca el drift a los montos? (R10, validación adversarial, criterio en D17):*
    - Un modelo distingue 201903 de 201910 a la perfección (AUC 1,0) usando solo las 73 columnas monetarias, con o sin deflactar.
    - El drift fuerte viene de cortes de los datos, no de la inflación: rentabilidad, márgenes y comisiones valen 0 en 201910, y `mtransferencias_recibidas` casi no existe antes de 201906. Ningún deflactor los toca.
    - En los consumos, saldos y límites de tarjeta sí había drift por inflación, y deflactar lo corrige (AUC de 0,55 a ~0,51), pero era chico.
    - Con 201908 contra 201910 no cambia nada.
    - **Deflactar arregla un drift menor y deja intacto el mayor.**
  - *Réplica independiente (R9):* la versión de Manuel, con 5 semillas, llega a la misma conclusión de fondo. Dos de sus observaciones no se sostienen con 20 semillas:
    - "Deflactar estabiliza": el desvío entre semillas no baja al deflactar.
    - "`foto_mes` recupera un tercio": empata.
  - *Chequeo del modelo base (R8):* con los hiperparámetros que eligió la versión de Manuel, corridos en nuestro pipeline con las mismas 20 semillas, la ganancia empata con nuestro baseline en las tres métricas (+1,3 M con N fijo, −1,1 M en la zona plana y −1,2 M en el máximo; p ≥ 0,10). El AUC de 201910 es mejor con los nuestros (0,9375 contra 0,9361, 20/20). Los dos modelos base son equivalentes en ganancia, así que las conclusiones no dependen de cuál se use.
- **Discusión:**
  1. **Qué se encontró.** Deflactar no mejora la ganancia, ni con IPC ni por grupo. Con los hiperparámetros del baseline, por grupo le gana al IPC por 2,1 M (R4), pero esa ventaja desaparece cuando cada brazo tiene su propia Optuna (R5). Lo robusto es que el baseline gana: los brazos deflactados pierden en la zona plana en las 20 semillas, en las dos configuraciones.
  2. **Los montos sí importan.** Las variables monetarias (crudas, lags y deltas) explican el **51% de la ganancia** (gain) del modelo baseline. `mcaja_ahorro` es la segunda más importante, después de `ctrx_quarter`. Por eso, el resultado no se explica porque el modelo ignore los montos: los usa mucho, y aun así deflactarlos no ayuda.
  3. **Por qué puede pasar** (la primera, probada; el resto, hipótesis no verificadas):
     - *No es la pista del mes:* el brazo IPC + `foto_mes` (R6) empata con el IPC solo. Esta explicación quedó probada y descartada, al menos para un único mes de test.
     - *La señal de baja está cerca de cero, y el cero no se deflacta.* Un cliente que se va vacía la cuenta y deja de consumir. Que el saldo quede en 0 o caiga a la mitad se ve igual en pesos nominales que en pesos de enero. Si los cortes de los árboles caen cerca de 0, dividir por un índice casi no los mueve.
     - *La ventana es corta.* Entre 201903 y 201910 el IPC sube ~27%, poco frente a la dispersión entre clientes, donde los montos van de cientos a millones. El drift existe, pero pesa menos que las diferencias entre un cliente y otro.
     - *Los índices no describen bien a las columnas.* Los saldos crecen 1,36–1,43 en el año, y ni la tasa (1,53) ni el IPC (1,50) los siguen. Dividir por un índice que no corresponde puede agregar ruido en lugar de quitarlo.
     - *El monto nominal también tiene información.* Un sueldo que no se actualiza o una cuota fija pueden ser una señal en sí mismos, y al deflactarlos esa señal se pierde.
     - *2019 tiene un quiebre de comportamiento.* Las PASO de agosto y el cepo de septiembre no son precios, y ningún deflactor los corrige.
  4. **Objetivo 1.** Usar el índice del mes anterior, que es lo único disponible al predecir, cuesta ~1,5 M frente al del mismo mes (R3). Es un costo chico, pero consistente entre semillas.
  5. **Objetivo 2: la lección de método.** Con una sola semilla, el ruido es de ±3,3 M. Sin las 20 semillas pareadas, el +2,1 M de "por grupo" habría parecido un resultado. Y sin el chequeo con una Optuna propia por brazo, lo habríamos reportado como hallazgo. Las diferencias de unos pocos millones solo se pueden afirmar con semillas pareadas y con un chequeo de robustez.
  6. **Hallazgos sobre los datos** (D14), que salieron al clasificar las columnas:
     - Los consumos y pagos en dólares de tarjeta están en USD, mientras que los saldos en dólares están en pesos al tipo de cambio.
     - Las etiquetas de plazo fijo en pesos y en dólares parecen cruzadas.
     - No hay préstamos UVA ni montos de mora.
     - Los montos están multiplicados por 1,173.

     La tabla de deflactores de la hipótesis suponía columnas que el dataset no tiene: los grupos CER y tasa activa quedaron vacíos.
  7. **Relación con otros trabajos.** El grupo de 2023 (ver Antecedente) deflactó todo por IPC, se encontró con el mismo problema de las variables en dólares y no encontró papers sobre el tema. Este trabajo lo extiende con el brazo por grupo, la medición del ruido entre semillas y el chequeo de robustez. Llega a una conclusión en la misma línea: en churn bancario con ventanas cortas, ajustar por inflación no es una mejora obvia.
- **Conclusión:** En el churn de 2019, con un modelo LightGBM de lags y deltas, **deflactar las variables monetarias no mejora la ganancia**: el modelo sin deflactar es igual o mejor, en las 20 semillas y con hiperparámetros propios para cada brazo. Deflactar por grupo le ganó a deflactar todo por IPC solo con los hiperparámetros del baseline; con hiperparámetros propios empatan, así que esa ventaja no es robusta. La hipótesis no se confirma en ninguna de sus dos partes. Recomendación práctica: en ventanas cortas como esta, no vale la pena deflactar. Si se hace, usar el índice del mes anterior (el único disponible al predecir) cuesta poco.
- **Antecedente** (plantilla de referencia, ejemplo de 2023, "Data Drifting"): otro grupo deflactó las 73 variables monetarias por el IPC general. Encontró la misma limitación que nosotros, porque las variables en dólares vienen convertidas a pesos al tipo de cambio oficial. También dejó escrito: "no encontré paper de performance por ajuste por inflación". Nuestro brazo "todo con IPC" replica ese enfoque, y el brazo "por grupo" lo extiende. Sirve para la Discusión (problema ↔ otros problemas).
- **Futuros Experimentos y Problemas:**
  - **Ventanas largas y con más inflación** (2020–2021), donde el drift podría pesar más que la dispersión entre clientes.
  - **Varios meses de test**, en lugar de uno solo, para que el resultado no dependa de 201910.
  - **Alternativas a deflactar:** el ranking o percentil del cliente dentro de su mes, que no depende de ningún índice, o cocientes entre columnas del mismo cliente (como el uso del límite).
  - **Verificar la explicación del "cero":** ver dónde caen los cortes de los árboles en las variables monetarias y cuántos están cerca de 0.
  - **Confirmar con la cátedra** si las columnas de plazo fijo en pesos y en dólares están cruzadas.
  - Montos anonimizados: las modas son múltiplos de 1,173 (5.865 = 5.000 × 1,173). Es un factor constante y no afecta, pero vale mencionarlo.