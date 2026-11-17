# Inflación en variables monetarias para LightGBM sobre datos bancarios: qué dice la evidencia y qué conviene probar

No encontré ningún paper, tesis ni informe de banco central que compare variables monetarias deflactadas contra nominales en modelos de scoring, comportamiento o churn de clientes bancarios en economías de alta inflación; la única evidencia comparativa disponible es informal (notebooks y repositorios de alumnos de esta misma materia sobre este mismo banco), y apunta a que el ranking por mes con el cero fijo funciona algo mejor que deflactar por IPC, aunque con diferencias del orden del ruido entre semillas.

## TL;DR

- **No hay evidencia publicada que compare deflactar contra no deflactar en modelos de clientes bancarios con inflación alta.** Hice 18 búsquedas propias y una búsqueda adicional delegada, en inglés y en español, sobre Argentina, Turquía, Brasil, Venezuela, Irán y Zimbabue. Lo más cercano es literatura de estabilidad poblacional en scoring y recomendaciones de política sin prueba empírica. Su experimento sería evidencia original, no una réplica.
- **El resultado que obtuvieron (deflactar no mejora) es el esperable por teoría.** Dividir por un índice por mes es una transformación monótona distinta en cada mes. Para los árboles solo importa por dos vías: cuánto mueve a los clientes respecto de los cortes (ustedes midieron ~2%) y cómo cambia los deltas. Las técnicas que más prometen son las que eliminan toda diferencia de escala entre meses, como el ranking por mes con cero fijo, o las que son invariantes a cualquier deflactor común, como los cocientes entre variables del mismo mes y los deltas relativos. Ninguna de ellas necesita un índice externo.
- **La NIC 29 y la RT 6 no respaldan deflactores por grupo.** Piden un único índice general (en Argentina, el IPC nacional del INDEC empalmado con el IPIM). Solo ajustan por contrato las partidas indexadas, como UVA/CER. No encontré trabajos que usen índices por quintil de la ENGHo para deflactar en modelos predictivos. Para el problema del índice no publicado, la salida más simple es usar transformaciones sacadas del propio dato del mes. Si mantienen la deflación, pueden usar la mediana del REM del BCRA.

## Resumen (una página)

**1. Literatura empírica sobre inflación y modelos de clientes bancarios.** No encontré ningún trabajo revisado por pares ni informe técnico (BCRA, BIS, FMI, Banco Mundial, bancos centrales de Turquía o Brasil) que evalúe cómo la inflación afecta un modelo de scoring o churn construido con datos de clientes. Tampoco encontré ninguno que compare variables deflactadas contra nominales. Lo más cercano:
- **Du Pisanie, Allison, Budde y Visagie (2023, arXiv:2303.01227), sobre índices de estabilidad poblacional.** Advierten que un scorecard puede verse estable mientras la población enfrenta "higher inflation or interest rates, which could decrease their ability to pay", y que estas métricas no distinguen un corrimiento de la población de una variable inestable.
- **Peykani, Sargolzaei, Oprean-Stan, Kamyabfar y Reghabi (2025, *PLOS One* 20(8):e0329587), sobre mora en la banca iraní.** Recomiendan "inflation-adjusted credit scoring models", pero sale de un TVP-VAR macro y no de una prueba de features.
- **Min y Yolalan (2003), Yapı Kredi en Turquía.** Usan ratios financieros en un contexto de "high public deficit and a high inflation", pero para empresas y sin comparar contra nominales.\[1\]

Toda la evidencia comparativa que existe es práctica informal de esta misma materia:
- **Rossi (2019).** Usó el mismo banco, con datos de 201805–201904. Concluyó que los rangos por percentil y el escalado por mes fueron "claramente peores al benchmark" nominal, y que IPC y dólar superaron al nominal "en algunos casos pero no está claro que sean superiores".\[2\] El diseño era débil: 4 variables, XGBoost con 20 rondas, un solo mes de entrenamiento y percentiles sin cero fijo.
- **Repositorios de la edición 2026, con datos de 2021.** El ranking por mes con cero fijo aparece como práctica generalizada y con mejoras chicas:
  - Dominguez: la ganancia pasó de 108,82 a 111,65 con ranking y a 112,39 con cero fijo, en el leaderboard público.\[3\]
  - Larrea y Carraud: con 10 semillas, AUC de 0,9349 con rank de cero fijo contra 0,9322 con IPC, con desvíos de ~0,0006–0,0008.\[4\]

**2. Técnicas alternativas.** El ranking por mes, la normalización por cuantiles y la división por la mediana mensual tienen respaldo teórico, pero no evidencia publicada en banca. Para árboles conviene saber tres cosas:
- **La normalización por cuantiles contra un mes de referencia equivale al ranking por mes en los niveles.** La correspondencia percentil → cuantil de referencia es una sola función monótona, aplicada igual a todos los meses. Solo difieren en cómo quedan los deltas que se calculan después.
- **Los cocientes entre variables del mismo mes (consumo/límite, saldo/sueldo) son exactamente invariantes a cualquier deflactor común del mes.** En esos cocientes, la discusión IPC contra RIPTE desaparece.
- **El log del cociente x_t/x_{t−1} cambia con cualquier deflactor solo en una constante por mes** (≈ log de la inflación del mes). Es casi inmune al problema por construcción.

**3. Árboles e invariancia.** La invariancia de los árboles a transformaciones monótonas está en Breiman et al. (1984), citada textualmente por Galili y Meilijson (2016): "invariant under all monotone transformations of individual ordered variables". Galili y Meilijson muestran que la invariancia se rompe solo al interpolar cerca de un corte con pocas observaciones: 9% de error con 10 observaciones por corte y 1% con 100.\[5\] Con 130.000 clientes por mes eso es irrelevante, lo que explica por qué el log no cambia nada. El argumento de que el monto nominal tiene información propia está documentado en economía del comportamiento: la "ilusión monetaria" (Shafir, Diamond y Tversky, 1997) es la tendencia a pensar en valores nominales y no reales.\[6\] No encontré trabajos que lo prueben dentro de un modelo predictivo. Es una hipótesis plausible para explicar por qué deflactar empeora un poco, no un resultado establecido.

**4. NIC 29 / RT 6.**
- **Partidas monetarias** (efectivo, saldos, préstamos en pesos): no se reexpresan, porque ya están en moneda de cierre.\[7\]\[8\]
- **Partidas indexadas por contrato:** se ajustan según el contrato (párrafo 13), lo que respalda usar CER para préstamos UVA.\[9\]
- **Todo lo demás, incluidos ingresos y gastos:** se reexpresa con un índice general, preferentemente el mismo para todas las entidades (párrafo 37).\[10\]
- **En Argentina:** la FACPCE fija el IPC nacional del INDEC empalmado con el IPIM, y el coeficiente es índice de cierre ÷ índice de origen.\[11\]

La NIC 29 sirve como guía conceptual en dos puntos: separar partidas monetarias de indexadas, y reexpresar los comparativos (análogo de los lags). No sirve para justificar deflactores distintos por grupo, porque va en sentido contrario.

**5. Índices por segmento de ingreso.** Hay índices construidos con ponderadores de la ENGHo 2017/18 por quintil: CENTRORA-UBA, UNLPam y Equilibra (segundo quintil).\[12\]\[13\]\[14\] No encontré ninguno usado para deflactar variables de un modelo predictivo.

**6. Índice no publicado.** El REM del BCRA se releva en los últimos 3 días hábiles de cada mes. Desde enero de 2019 incluye una estimación del mes corriente, publicada como mediana.\[15\] Forte (BBVA Research; *Ensayos Económicos* del BCRA n.º 84, págs. 141–159, número fechado 2024 y publicado en línea en 2025), con "una base de datos con indicadores en frecuencia mensual desde 1962", concluye que un Random Forest alcanza "una precisión de pronóstico estadísticamente comparable al consenso de analistas de mercado relevado por el [BCRA]". Dado que para los árboles el deflactor por mes es casi irrelevante, la prueba que ya hicieron (índice del mes anterior contra el del mismo mes) basta. Las transformaciones sacadas del propio dato evitan el problema por completo.

## Tabla de técnicas

| Técnica | Referencia principal | Evidencia | ¿Aplica a árboles? | Cómo la aplicaríamos |
|---|---|---|---|---|
| Deflactar por IPC (índice único) | NIC 29 párr. 37; FACPCE RT 6; Rossi (2019) | Normativa contable (no predictiva); práctica informal: Rossi y Larrea/Carraud, sin mejora clara | Débil: es un reescalado por mes; solo cambia cortes cerca del umbral y los deltas | Ya probado: empata o empeora. Mantener como brazo de control |
| Deflactores por grupo (RIPTE, tasa, TC, CER) | Doc del equipo (Eurostat/SNA, no verificados por mí); NIC 29 párr. 13 solo para indexadas | Teórica (contabilidad nacional); ninguna evidencia predictiva | Igual que el IPC: reescalados por mes y por columna | Ya probado: empata con IPC. Conservar solo CER para UVA, por contrato |
| Ranking (percentil) por mes con cero fijo | Repos DMEyF 2026 (Dominguez, Larrea/Carraud, Forni, Suárez, Lovrich, Dituro, Freites, Abregú); en contra: Rossi (2019) sin cero fijo | Práctica informal; mejoras de ~1–3% de ganancia o ~0,003 de AUC, cerca del ruido entre semillas | Sí: es la única transformación por mes que elimina toda diferencia de escala, incluida inflación, aguinaldo y estacionalidad | Prioridad 1: sobre valores, lags y deltas; negativos en [−1,0), cero en 0, positivos en (0,1]\[16\] |
| Normalización por cuantiles contra un mes de referencia | Bolstad et al. (2003), microarrays; Galili y Meilijson (2016) | Empírica en biología; teórica en árboles | En niveles equivale al ranking por mes; difiere solo en los deltas calculados después | No como brazo aparte para niveles; solo como variante de "deltas en escala de referencia" |
| Dividir por la mediana mensual de cada columna | Sin referencia específica; análogo al deflactor sacado del dato (escáner de precios del Manual IPC, citado en el doc del equipo, no verificado) | Ninguna; teórica | Reescalado por mes como el IPC, pero absorbe también aguinaldo y cambios reales | Prueba barata: si empata con IPC, confirma que el deflactor no importa; cuidado con columnas de mediana cero |
| Deltas relativos (log con signo de x_t/x_{t−1}) | Sin referencia específica en banca; propiedad algebraica | Teórica | Sí: invariante a cualquier deflactor común salvo una constante por mes ≈ inflación mensual | Prioridad 2: agregar junto a los deltas absolutos, con tratamiento explícito de ceros |
| Cocientes entre variables del mismo mes (consumo/límite, saldo/sueldo, cuota/sueldo) | Siddiqi (2017), utilización (no verificado en texto completo); Home Credit/Kaggle ("Top predictive power"); Min y Yolalan (2003)\[17\] | Práctica de la industria e informal; empírica indirecta en scoring corporativo | Sí: exactamente invariante a cualquier deflactor común del mes | Prioridad 2: 10–20 cocientes con sentido de negocio, más sus lags |
| Mantener nominal + transformada (dejar elegir al modelo) | Shafir, Diamond y Tversky (1997), ilusión monetaria; Rossi (2019) | Teórica/conductual; ninguna en modelos | Sí: el árbol elige qué versión corta | Prioridad 3: probar la hipótesis de que el nominal tiene información propia |
| Mes como feature | Su experimento | Propia | Solo sirve si el efecto es un nivel por mes; no corrige escalas | Ya probado: no recupera nada |
| Índices por quintil (ENGHo) | CENTRORA-UBA; UNLPam; Equilibra DT 8 | Construcción de índices sí; uso predictivo no encontrado | Cambiaría cortes solo marginalmente | Baja prioridad |
| Nowcast del índice (REM, Random Forest) | BCRA, metodología REM; Forte (2025) | Empírica para pronosticar inflación, no para modelos de clientes | Irrelevante si se usa ranking | Solo si conservan la deflación en producción |

## Detalle por pregunta

**P1: trabajos sobre inflación en modelos de clientes.** La búsqueda se hizo en inglés y en español: alrededor de 30 consultas entre las mías y las del subagente. No incluyó repositorios de tesis turcas (YÖK Tez), brasileñas (BDTD) ni de la UBA o el ITBA. La ausencia hay que leerla como "no encontrado en una búsqueda acotada", no como prueba de que no existe. El tratamiento estándar en scoring es monitorear el corrimiento con índices de estabilidad, sin corregir las variables.\[18\]\[19\] Du Pisanie et al. muestran justamente que esas métricas pueden no detectar el deterioro por inflación.\[20\] El comentario de Ross W. Gayler (*Statistical Science* 21(1):19–23, 2006) al artículo de Hand sobre la "ilusión de progreso" en scoring resume la práctica: "a large part of the value added by credit scoring practitioners comes from anticipating possible future shifts in the data distribution and designing the models to be relatively insensitive to such shifts". Es el argumento general a favor de features robustas, como ranking y cocientes, y no de corregir con índices.

**P2: técnicas alternativas.** Lo más informativo para su caso viene de los repositorios de la materia. Su diseño es casi idéntico al de ustedes: LightGBM, lags y deltas de orden 1 y 2, y ganancia sobre los N primeros. Dominguez explica la mejora del ranking así: "un mismo sueldo 'significa' distinto en marzo que en agosto. El ranking compara a cada cliente con los demás del mismo mes, y eso borra la inflación y el aguinaldo". Atribuye la mejora del cero fijo a que "en el ranking común, 'no tener el producto' quedaba pegado a 'tener muy poco'".\[3\] Esto encaja con su hallazgo de que la mitad del gain está en umbrales de ±1.000 pesos: el modelo usa los montos sobre todo como indicador de actividad, cero o distinto de cero. El cero fijo preserva esa señal exactamente.

Hay que leer estos números con cautela. Son puntajes únicos de leaderboard sobre datos de 2021, con inflación distinta a la de 2019. La misma autora reconoce que la diferencia entre 6018 y 6019 "es ruido".\[3\] Lovrich reporta que agregar flags de cero movió la ganancia de ~457M a ~460M, una diferencia "menor al desvío entre semillas de ~4-5M".\[21\] Rossi (2019) encontró lo contrario, pero con un diseño mucho más pobre.

**P3: árboles y deflactación.** Hay tres argumentos de por qué deflactar puede no ayudar o empeorar:
- **Escala de los cortes.** Un reescalado por mes del orden de pocos puntos porcentuales (≈3,4% mensual promedio con 50% anual) solo mueve de lado a los clientes cercanos a cada corte. Ustedes lo midieron: ~2%.
- **Corte de LightGBM.** LightGBM agrupa cada variable en hasta max_bin contenedores con bordes elegidos para "distribute the training data evenly over all bins".\[22\]\[23\] Un desplazamiento chico de escala apenas cambia la asignación a contenedores.
- **Información nominal.** Si el monto nominal lleva información propia, por ejemplo un sueldo que no se actualizó o una comisión fija, el deflactor introduce ruido: una caída real que el cliente no percibe como tal.

El tercer punto se apoya en la ilusión monetaria, documentada en encuestas (Shafir et al., 1997).\[24\] Su traslado a modelos de churn es una hipótesis mía, no un resultado publicado.

**P4: NIC 29 / RT 6 como guía.** El aporte útil de la NIC 29 es conceptual. Los saldos del mes son partidas monetarias, que no se reexpresan dentro del mes.\[7\]\[25\] El problema aparece al comparar contra meses anteriores, igual que la NIC 29 reexpresa los estados comparativos. En su modelo eso equivale a la única parte de la deflación que no es una transformación monótona por mes: el delta real x_t − x_{t−1}·(IPC_t/IPC_{t−1}). La norma prefiere explícitamente un índice general único.\[26\]\[27\] Pedir RIPTE para sueldos o tasa de plazo fijo para saldos no tiene respaldo en la NIC 29. Si existe, viene de los manuales de cuentas nacionales que cita el documento del equipo, que no verifiqué. El propio documento advierte que esa bibliografía "claramente la busqué con IA y hay que verificar todo".\[28\]

**P5: índices por segmento.** CENTRORA (UBA) construye inflación por quintil con la ENGHo 2017/18 e ilustra que, con 10% de inflación general, los hogares más pobres enfrentarían 13,2%.\[13\] UNLPam y Equilibra reconstruyen un IPC con ponderadores del segundo quintil para líneas de pobreza.\[14\]\[29\] Ninguno lo aplica a modelos predictivos. Para un modelo mensual, la diferencia entre quintiles es de pocos puntos anuales, o sea fracciones de punto por mes. Por el argumento de P3, no debería mover los cortes.

**P6: índice no publicado.** La FACPCE publica su serie "una vez que tome conocimiento público la variación mensual del IPC Nacional por el INDEC", es decir, con rezago.\[30\] Para producción hay dos opciones:
- **Usar el último índice publicado o la mediana del REM del mes corriente.** El REM se releva los últimos 3 días hábiles del mes y desde enero de 2019 encuesta el período corriente.\[15\]
- **Preferir transformaciones que solo usan el corte transversal del mismo mes**, como ranking, mediana o cocientes. No necesitan ningún índice externo ni introducen fuga de información, porque al momento de predecir están disponibles todos los clientes del mes.

## Referencias

Marco **[completa]** las que leí enteras y **[resumen]** las que conozco solo por el resumen, el fragmento de búsqueda o el informe del subagente.

1. Equipo DMEyF (Marasco, Esquivel, Arias), "Investigación DMEyF", Google Doc interno **[completa]**. https://docs.google.com/document/d/1slozcvKEpcd3q56sGjMIJ7xreX6nCf_ApeNZlQZ9DHc/edit
2. Rossi, S. (2019). "Ajuste por inflación", RPubs **[completa]**. https://rstudio-pubs-static.s3.amazonaws.com/541496_43efdbd2d850471d869a26999eea1dcf.html
3. Dominguez, A. (2026). Primera Competencia DMEyF 2026, repositorio GitHub **[completa]**. https://github.com/Ani-victoria/dmeyf2026-competencia01
4. Larrea, E. y Carraud. "¿Qué efecto tiene la aplicación de técnicas de corrección del data drifting sobre variables monetarias…?", GitHub **[resumen]**. https://github.com/enriquelarreamcd-svg/g2dr-carraud-larrea
5. Otros repositorios DMEyF 2026 con ranking de cero fijo **[resumen]**: https://github.com/SofiaForni/primera_entrega_EYF ; https://github.com/LuisDanielSuarez/dmeyf-competencia1 ; https://github.com/agustinlovrich/dmeyf-primera-competencia ; https://github.com/SerenaDituro/Competencia1_DMEyF_2026 ; https://github.com/mariofreites/dmeyf-primera-competencia ; https://github.com/ezequielabregu/DMEyF_competencia_1
6. Galili, T. y Meilijson, I. (2016). "Improving Decision Tree Predictions via Transformations", arXiv:1611.04561 **[completa]**. https://arxiv.org/abs/1611.04561
7. Breiman, L., Friedman, J., Olshen, R. y Stone, C. (1984). *Classification and Regression Trees*. CRC. Citado vía Galili y Meilijson; no leído directamente.
8. Guo et al. "Gradient Boosting With Piece-Wise Linear Regression Trees", arXiv:1802.05640 (descripción de los bins de histograma) **[resumen]**. https://arxiv.org/pdf/1802.05640
9. LightGBM, documentación de parámetros (max_bin) **[resumen]**. https://testlightgbm.readthedocs.io/en/latest/Parameters.html
10. IFRS Foundation. NIC 29 / IAS 29, *Financial Reporting in Hyperinflationary Economies* **[resumen: párrafos 12, 13 y 37 vía fragmentos]**. https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2026/issued/ias29.html
11. FACPCE. Resolución Técnica N° 6 (modif. 2018, Res. JG 539/18) **[resumen]**. https://www.facpce.org.ar/wp-content/uploads/2020/05/RT06-modificaciones2018.pdf
12. FACPCE. Guía de aplicación de las normas contables sobre ajuste por inflación (RT 6 y NIC 29), 2021 **[resumen]**. https://www.facpce.org.ar/wp-content/uploads/2021/05/Guia-de-aplicacion-de-las-normas-contables-sobre-AxI-Parte-1-version-2021.pdf
13. Bolstad, B. M., Irizarry, R. A., Åstrand, M. y Speed, T. P. (2003). "A comparison of normalization methods for high density oligonucleotide array data based on variance and bias", *Bioinformatics* 19(2):185–193 **[resumen]**. https://www.molgen.mpg.de/3716346/quantile_normalization.pdf
14. Shafir, E., Diamond, P. y Tversky, A. (1997). "Money Illusion", *Quarterly Journal of Economics* 112(2):341–374 **[resumen]**. https://econpapers.repec.org/RePEc:oup:qjecon:v:112:y:1997:i:2:p:341-374.
15. du Pisanie, J., Allison, J., Budde, C. y Visagie, J. (2023). "A critical review of existing and new population stability testing procedures in credit risk scoring", arXiv:2303.01227 **[resumen; el subagente leyó ~40%]**. https://arxiv.org/html/2303.01227
16. John, S. (Kenyatta University). "Fair and Explainable Credit-Scoring under Concept Drift", arXiv:2511.03807 **[resumen]**. https://arxiv.org/pdf/2511.03807
17. Gayler, R. W. (2006). "Comment: Classifier Technology and the Illusion of Progress—Credit Scoring", *Statistical Science* 21(1):19–23, arXiv:math/0606452 **[resumen]**. https://arxiv.org/pdf/math/0606452
18. Peykani, P., Sargolzaei, M., Oprean-Stan, C., Kamyabfar, H. y Reghabi, M. (2025). "The effect of macroeconomic shocks on non-performing loans and credit risk in the Iranian banking system using time-varying parameter vector autoregressions", *PLOS One* 20(8):e0329587 **[resumen]**. https://pmc.ncbi.nlm.nih.gov/articles/PMC12331042/
19. Min, J. H. y Yolalan, R. et al. (2003). "A credit scoring approach for the commercial banking sector", *Socio-Economic Planning Sciences* **[resumen]**. https://people.sabanciuniv.edu/atilgan/FE500_Fall2013/16Nov2013_RehaYolalan/SocEconPlanSci2003_CreditScoring.pdf
20. Siddiqi, N. (2017). *Intelligent Credit Scoring*, 2.ª ed., Wiley **[resumen: solo catálogo y fragmentos; no verifiqué pasajes sobre inflación]**. https://onlinelibrary.wiley.com/doi/book/10.1002/9781119282396
21. mratsim, "feature_engineering_ideas.md", Home Credit Default Risk (Kaggle) **[resumen]**. https://github.com/mratsim/home-credit-default-risk/blob/master/feature_engineering_ideas.md
22. CENTRORA-UBA. "Inflación por Ingresos" **[resumen]**. https://centrora.economicas.uba.ar/3141-2/
23. UNLPam. "Informe sobre el cálculo de la inflación argentina con IPC base diciembre 2023=100 y ponderadores ENGHo 2017/18" **[resumen]**. https://www.eco.unlpam.edu.ar/wp-content/uploads/2025/04/Informe-sobre-metodlogia-de-IPC-VF.pdf
24. Equilibra. Documento de Trabajo N° 8, "Nuevas líneas de pobreza en Argentina" **[resumen]**. https://equilibra.ar/wp-content/uploads/2025/08/DT-8.pdf
25. BCRA. "Relevamiento de Expectativas de Mercado (REM): consideraciones metodológicas" **[resumen]**. https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/Consideraciones%20del%20Relevamiento%20de%20Expectativas%20de%20Mercado%20(REM).pdf
26. Forte, F. D. (BBVA Research). "Pronóstico de inflación de corto plazo en Argentina con modelos Random Forest", *Ensayos Económicos* (84):141–159, BCRA, doi:10.64285/ensayosbcra84.y2024.672 (número fechado 2024, publicado en línea en 2025) **[resumen]**. https://www.investigacioneseconomicas.bcra.gob.ar/ensayos_economicos_bcra/article/view/672

Lo que **no encontré**, dicho explícitamente:
- Estudios de bancos argentinos, turcos, brasileños, venezolanos o israelíes (años 80) sobre inflación en modelos de clientes.
- Una cita verificada de Siddiqi sobre variables de ingreso afectadas por inflación.
- Trabajos que usen índices por segmento de la ENGHo en modelos predictivos.
- Trabajos que prueben con datos el argumento de la "información nominal propia" dentro de un modelo.

Tampoco verifiqué las referencias de cuentas nacionales del documento del equipo (Manual IPC, SNA 2008, Handbook de Eurostat).

## Pruebas recomendadas, en orden de prioridad

1. **Ranking por mes con cero fijo, en dos variantes.**
   - (a) Rankear los valores y después calcular lags y deltas sobre los rankings.
   - (b) Calcular lags y deltas en pesos y después rankear todo por mes.

   *Por qué:* es la única técnica con evidencia favorable, aunque informal, en el mismo problema y el mismo banco (Dominguez; Larrea y Carraud; uso generalizado en DMEyF 2026). Ataca también el aguinaldo de junio, que cae dentro de su ventana de entrenamiento 201903–06. Las dos variantes separan si la ganancia viene de los niveles o de los deltas. Rossi (2019) encontró lo contrario sin cero fijo, así que el brazo "ranking sin cero fijo" vale como control. La normalización por cuantiles contra un mes de referencia no hace falta como brazo aparte, porque en niveles es equivalente.

2. **Cocientes intra-mes y deltas relativos, agregados a los nominales.** Calcular 10–20 cocientes con sentido de negocio (consumo/límite, saldo/sueldo, cuota/sueldo, comisiones/saldo) y el log con signo de x_t/x_{t−1}, con tratamiento explícito de ceros.

   *Por qué:* son invariantes, exacta o casi exactamente, a cualquier deflactor común. Por eso hacen innecesaria la discusión IPC contra RIPTE. Además tienen respaldo como práctica estándar en scoring: utilización en Siddiqi (no verificado en texto), ratios con "Top predictive power" en Home Credit, ratios en scoring turco (Min y Yolalan).\[17\]

3. **Prueba explícita de la "información nominal propia".** Comparar tres conjuntos:
   - solo nominal;
   - solo transformada (ranking o deflactada);
   - nominal más transformada.

   Si gana el tercero, o si el modelo sigue cortando la versión nominal teniendo la otra disponible, hay evidencia de que el monto nominal informa algo por sí mismo.

   *Por qué:* convierte su resultado ("deflactar empeora un poco") en una hipótesis contrastable. Se apoya en la ilusión monetaria (Shafir et al., 1997) y en que deflactar por IPC no superó claramente al nominal en Rossi (2019).\[2\]

4. **División por la mediana mensual de cada columna, como control barato.** Si empata con IPC y con grupos, confirma con un tercer deflactor que la escala por mes no importa a los árboles. Si se acerca al ranking, indica que lo que ayuda es absorber también aguinaldo y estacionalidad, no la inflación.

   *Por qué:* es coherente con la teoría de invariancia (Breiman et al., vía Galili y Meilijson) y con su propia observación de que deflactar mueve solo ~2% de clientes por corte.

5. **Protocolo de comparación que separe señal de ruido.** Correr al menos 10–20 semillas por brazo y una prueba pareada (Wilcoxon, como Abregú).\[31\] Evaluar en más de un mes, por ejemplo 201908 y 201910 rotando cuál es validación y cuál es test.

   *Por qué:* todas las diferencias reportadas en la práctica informal son del orden del desvío entre semillas (Lovrich: ~3M contra un desvío de ~4–5M; Dominguez: 6018 contra 6019 "es ruido"; Larrea y Carraud advierten "un solo mes de validación").\[4\]\[21\] Sin esto, cualquier ganador puede ser azar.

## Advertencias

- Toda la evidencia comparativa es de práctica informal, no revisada por pares. Usa datos de 2021 (salvo Rossi, 2019), con inflación y contexto distintos de los de 2019, y en general un único mes de evaluación.
- Varias afirmaciones de esta revisión son razonamiento propio a partir de la teoría y no resultados publicados. Las principales son la equivalencia entre normalización por cuantiles y ranking para árboles, la invariancia de los cocientes y la interpretación del rol de los umbrales chicos. Conviene presentarlas así en el informe.
- Las citas que conozco solo por el resumen (en especial NIC 29, RT 6, Siddiqi y Bolstad) deben chequearse contra el texto completo antes de citarlas textualmente.

## Fuentes

1. [A credit scoring approach for the commercial banking sector](https://people.sabanciuniv.edu/atilgan/FE500_Fall2013/16Nov2013_RehaYolalan/SocEconPlanSci2003_CreditScoring.pdf)
2. [Ajuste por inflación](https://rstudio-pubs-static.s3.amazonaws.com/541496_43efdbd2d850471d869a26999eea1dcf.html)
3. [GitHub - Ani-victoria/dmeyf2026-competencia01](https://github.com/Ani-victoria/dmeyf2026-competencia01)
4. [GitHub - enriquelarreamcd-svg/g2dr-carraud-larrea: “¿Qué efecto tiene la aplicación de técnicas de corrección del data drifting sobre variables monetarias en el desempeño del modelo” ? · GitHub](https://github.com/enriquelarreamcd-svg/g2dr-carraud-larrea)
5. <https://arxiv.org/pdf/1611.04561>
6. [EconPapers: Money Illusion](https://econpapers.repec.org/RePEc:oup:qjecon:v:112:y:1997:i:2:p:341-374.)
7. [946 Indian Accounting Standard (Ind AS) 29](https://webtel.in/image/INDAS29.pdf)
8. [IAS 29 Financial Reporting in Hyperinflationary Economies](https://www.icaew.com/technical/corporate-reporting/ifrs/ifrs-accounting-standards-tracker/ias-29-financial-reporting-in-hyperinflationary-economies)
9. [Ias29](https://slideshare.net/IFRS_IAS_COMPILED/ias29)
10. [IAS 29 Financial Reporting in Hyperinflationary Economies](https://www.readyratios.com/reference/ifrs/ias_29_financial_reporting_in_hyperinflationary_economies.html)
11. [Federación Argentina de Consejos Profesionales de Ciencias Económicas 1](https://www.facpce.org.ar/wp-content/uploads/2020/05/RT06-modificaciones2018.pdf)
12. [Informe sobre el cálculo de la inflación argentina con IPC ...](https://www.eco.unlpam.edu.ar/wp-content/uploads/2025/04/Informe-sobre-metodlogia-de-IPC-VF.pdf)
13. [Inflación por Ingresos - CENTRORA - UBA](https://centrora.economicas.uba.ar/3141-2/)
14. [DOCUMENTO DE TRABAJO N°8 NUEVAS LÍNEAS DE POBREZA EN ARGENTINA: ACTUALIZACIÓN](https://equilibra.ar/wp-content/uploads/2025/08/DT-8.pdf)
15. [Relevamiento de Expectativas de Mercado (REM) Julio 2023](<https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/Consideraciones%20del%20Relevamiento%20de%20Expectativas%20de%20Mercado%20(REM).pdf>)
16. [GitHub - LuisDanielSuarez/dmeyf-competencia1 · GitHub](https://github.com/LuisDanielSuarez/dmeyf-competencia1)
17. [home-credit-default-risk/feature\_engineering\_ideas.md at master · mratsim/home-credit-default-risk · GitHub](https://github.com/mratsim/home-credit-default-risk/blob/master/feature_engineering_ideas.md)
18. [Population Stability Index (PSI) & CSI Explained - DexLab Analytics](https://www.dexlabanalytics.com/blog/population-stability-index-psi-csi-scorecard-monitoring)
19. [(PDF) The Population Resemblance Statistic: A Chi-Square Measure of Fit for Banking](https://www.researchgate.net/publication/372583818_The_Population_Resemblance_Statistic_A_Chi-Square_Measure_of_Fit_for_Banking)
20. [A critical review of existing and new population stability testing procedures in credit risk scoring](https://arxiv.org/html/2303.01227)
21. [GitHub - agustinlovrich/dmeyf-primera-competencia: Entrega Competencia 01 (DMEyF 2026): predicción de BAJA+2 en 202108. Reproducible end-to-end. · GitHub](https://github.com/agustinlovrich/dmeyf-primera-competencia)
22. [Gradient Boosting With Piece-Wise Linear Regression Trees](https://arxiv.org/pdf/1802.05640)
23. [Parameters - LightGBM documentation - Read the Docs](https://testlightgbm.readthedocs.io/en/latest/Parameters.html)
24. [MONEY ILLUSION, FINANCIAL LITERACY AND NUMERACY: EXPERIMENTAL EVIDENCE](https://www.sciencedirect.com/science/article/am/pii/S0167487019300352)
25. [IAS 29 Financial Reporting in Hyperinflationary Economies: Mechanics and Relevance for Indian Multinationals](https://globalfinx.in/dip-ifrs/blog/ias-29-hyperinflationary-economies-indian-multinationals)
26. [International Accounting Standard 29Financial Reporting in Hyperinflationary Economies](https://www.ifrs.org/content/dam/ifrs/publications/html-standards/english/2026/issued/ias29.html)
27. [I AS 2 9 Financial Reporting in Hyperinflationary Economies](https://bdchatterjee.com/wp-content/uploads/2026/08/IAS_29_Hyperinflationary_Economies.pdf)
28. [Google Drive](https://drive.google.com/open?id=1slozcvKEpcd3q56sGjMIJ7xreX6nCf_ApeNZlQZ9DHc)
29. [1 NUEVAS LÍNEAS DE POBREZA EN ARGENTINA: ACTUALIZACIÓN DE](https://www.eco.unlpam.edu.ar/wp-content/uploads/2025/08/Nuevas-lineas-de-pobreza-en-Argentina_-actualizacion-de-canastas-y-correccion-por-subdeclaracion-de-ingresos.pdf)
30. [Resolución Técnica N° 6 “Estados Contables en Moneda Homogénea”](https://www.consejo.org.ar/storage/attachments/RT%206%20TO.pdf-VeL5bDeAz5.pdf)
31. [GitHub - ezequielabregu/DMEyF\_competencia\_1 · GitHub](https://github.com/ezequielabregu/DMEyF_competencia_1)
