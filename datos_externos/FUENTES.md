# Fuentes de los índices y verificación de la bibliografía (Paso 8)

Verificado el 2026-11-15. La tabla `indices_mensuales.csv` se arma con `python src/05_indices.py` a partir de lo
descargado en `crudo/` (con `--bajar` se vuelve a descargar).

## Series usadas

| Columna | Serie | Fuente | Frecuencia |
|---|---|---|---|
| `ipc` | IPC nacional, nivel general, base dic-2016 = 100 (`148.3_INIVELNAL_DICI_M_26`) | INDEC vía datos.gob.ar | mensual |
| `ripte` | RIPTE en pesos (`158.1_REPTE_0_0_5`) | Seguridad Social vía datos.gob.ar | mensual |
| `tc_mayorista_prom/fin` | Tipo de cambio mayorista de referencia, Com. A 3500 (id 5) | BCRA API v4.0 | diaria |
| `tasa_pf30`, `idx_tasa_pf30` | Tasa de depósitos a 30 días, % TNA (id 12) | BCRA | diaria |
| `tasa_pf_personas` | Plazo fijo en pesos de personas humanas, % TNA (id 1190) | BCRA | diaria |
| `tasa_personales` | Préstamos personales, % TNA (id 14) | BCRA | diaria |
| `tasa_tarjetas` | Financiaciones con tarjeta, % TNA (id 1215). **Termina en 202004.** | BCRA | mensual |
| `badlar` | BADLAR bancos privados (id 7). Solo de referencia | BCRA | diaria |
| `cer_prom/fin` | CER, base 2/2/2002 = 1 (id 30) | BCRA | diaria |
| `uva_prom/fin` | UVA en pesos (id 31) | BCRA | diaria |

- **Series diarias:** `_prom` es el promedio del mes y se usa para flujos (consumos). `_fin` es el último dato del mes y se usa para saldos, que en el dataset son fotos a fin de mes.
- **Índices de tasas:** `idx_*` acumulan la tasa del mes, con base 201811 = 1: `idx_t = idx_{t-1} · (1 + TNA_t/100 · días/365)`.

**Controles contra valores publicados:**
- La inflación de 2019 da 53,8% (dic-19 / dic-18), igual que la de INDEC.
- El tipo de cambio mayorista sube de 44,9 a 59,1 después de las PASO de agosto de 2019.
- La UVA al 31/12/2019 da 47,16.

**Datos a tener en cuenta para el experimento:**
- La UVA es el CER reescalado: UVA = 14,05 × CER(t−1) / CER(31/3/2016) (Com. "A" 5945 / "A" 6069). Como deflactores son el mismo índice, no hace falta probar los dos.
- El CER se construye a partir del IPC con unos dos meses de rezago. Por eso, deflactar con CER se parece a deflactar con un IPC de hace dos meses.
- Las series del BCRA del mes t ya están publicadas cuando llega el archivo del mes t. El IPC no: sale a mediados de t+1, y eso es el objetivo 1. El RIPTE también se publica con rezago, y su calendario está **pendiente de verificar**.

## Verificación de la bibliografía de `docs/investigacion.md`

✅ = existe y la cita es correcta · ⚠️ = existe pero hay que corregir algo · ❓ = no se pudo confirmar

| Cita | Estado | Nota |
|---|---|---|
| IMF et al., *Consumer Price Index Manual: Concepts and Methods* (2020) | ✅ | La página del FMI responde. |
| CPI Manual 2020, cap. 10 "Scanner Data" | ✅ | El capítulo existe y es nuevo en la edición 2020. El link `.ashx` le devuelve 403 a un script, pero sí aparece en el buscador. |
| SNA 2008, cap. 15 "Price and volume measures" | ✅ | El PDF responde. |
| Eurostat, *Handbook on Prices and Volume Measures in National Accounts* (2016), KS-GQ-14-005 | ✅ | La página responde. La clasificación A/B/C de métodos es de este manual. |
| IMF, *Quarterly National Accounts Manual* (2017), capítulo de deflación | ✅ | Conviene poner el número de capítulo (es el cap. 8, "Price and Volume Measures"). |
| INDEC, metodología del IPC, base dic-2016 = 100 | ✅ | El PDF `metodologia_ipc_nacional_2019.pdf` responde. |
| RIPTE, Resolución 2-E/2018, Anexo II | ⚠️ | La resolución existe, pero otra fuente cita el Anexo III. Además, **la metodología vigente es la de la Res. SSS 3/2021**. Conviene citar las dos. |
| INDEC, Índice de salarios, Decreto 1242/2002, art. 2 | ✅ | El art. 2 aprueba la metodología del Coeficiente de Variación de Salarios (Anexo II). El Decreto 815/2024 la cambió, pero no afecta a 2019. |
| BCRA, estadísticas de tasas de interés | ✅ | Ahora se usa la API v4.0. La v3 está dada de baja. |
| Decreto 214/2002, art. 4 (crea el CER) | ✅ | |
| Ley 25.827 y Com. "A" 5945 (UVA) | ⚠️ | La Com. "A" 5945 (y la "A" 6069) es correcta. La Ley 25.827 aparece citada como marco de la UVA, pero **no se pudo confirmar el artículo**. No hay que confundirla con la UVI, que es de la Ley 27.271. |
| BCRA, Com. "A" 3500 (tipo de cambio de referencia) | ✅ | |
| Siddiqi (2017), *Intelligent Credit Scoring*, 2.ª ed., Wiley | ✅ | |
| Kaufman, Rosset, Perlich y Stitelman (2012), *ACM TKDD* 6(4), art. 15 | ✅ | La versión de KDD 2011 tiene tres autores, pp. 556–563. |
| Fed, SR 11-7 (2011) | ⚠️ | **Fue reemplazada por la SR 26-2 (abril de 2026)** y el link viejo da 404. Se puede citar como guía vigente en 2019, aclarando que fue reemplazada. |
| Dietterich (1998), *Neural Computation* 10(7), 1895–1923 | ✅ | |
| Demšar (2006), *JMLR* 7, 1–30 | ✅ | |
| Bergmeir y Benítez (2012), *Information Sciences* 191, 192–213 | ✅ | |
| Hastie, Tibshirani y Friedman (2009), *ESL*, 2.ª ed., cap. 9–10 | ✅ | |
| Ke et al. (2017), LightGBM, *NeurIPS* 30 | ✅ | El paper se centra en GOSS y EFB. El agrupamiento en histogramas (`max_bin`) es parte del algoritmo, pero no es el aporte central del paper. |
| Gama et al. (2014), *ACM Computing Surveys* 46(4), art. 44 | ✅ | |

Fuentes de la verificación:
- RIPTE: <https://www.argentina.gob.ar/trabajo/seguridadsocial/ripte>
- UVA: <https://www.bcra.gob.ar/archivos/Pdfs/comytexord/A6069.pdf>
- Decreto 1242/2002: <https://biblioteca.afip.gob.ar/dcp/DEC_C_001242_2002_07_12>
- CPI Manual: <https://www.imf.org/en/data/statistics/cpi-manual>
- SR 26-2: <https://www.federalreserve.gov/supervisionreg/srletters/SR2602.pdf>
