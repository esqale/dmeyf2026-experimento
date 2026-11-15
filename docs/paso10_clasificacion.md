# Paso 10 · Clasificación de las columnas monetarias y su deflactor (propuesta para discutir)

Hay 73 columnas monetarias: las que empiezan con `m`, `Visa_m` o `Master_m`. Los números salen de `src/06_monetarias.py` (tabla completa en `reportes/paso10/inventario.csv`).

**Cómo leer la evidencia:**
- **crec. anual** es la mediana, entre clientes con valor > 0 en los dos meses, de valor 201912 / valor 201901. Compara al mismo cliente consigo mismo.
- **salto ago** es lo mismo entre 201907 y 201908. A fin de agosto de 2019 el dólar subió 35% y el IPC 4%.

**Valores de referencia en el mismo período:**

| Índice | crec. anual | salto ago |
|---|---|---|
| IPC | 1,495 | 1,040 |
| RIPTE | 1,402 | 1,019 |
| Tasa de plazo fijo acumulada | 1,530 | 1,045 |
| Tasa de préstamos personales acumulada | 1,839 | 1,059 |
| CER (fin de mes) | 1,473 | 1,024 |
| Tipo de cambio (fin de mes) | **1,617** | **1,347** |

## Propuesta por grupo

| # | Grupo | Columnas | Deflactor | Evidencia | Para discutir |
|---|---|---|---|---|---|
| 1 | **Consumos y movimientos en pesos** | `mautoservicio`, `mtarjeta_visa/master_consumo`, `Visa/Master_mconsumospesos`, `_mconsumototal`, `_madelantopesos`, `_mpagado`, `_mpagospesos`, `_mpagominimo`, `mcuenta_debitos_automaticos`, `mttarjeta_visa/master_debitos_automaticos`, `mpagodeservicios`, `mpagomiscuentas`, `mtransferencias_recibidas/emitidas`, `mextraccion_autoservicio`, `mcheques_*` (4), `matm`, `matm_other`, descuentos (3) | IPC, promedio del mes | crec. 1,29–1,66 (tarjetas 1,36–1,48, cerca del IPC). Salto de agosto ≈ 1,00. | `mtransferencias_recibidas` da 3,7 porque recién se empieza a informar en 201906 (cambio de composición). `_mpagospesos` es negativo (signo del pago): dividir no cambia el signo. |
| 2 | **Sueldo** | `mpayroll`, `mpayroll2` | RIPTE | crec. 2,0 contra RIPTE 1,40. **Diciembre incluye aguinaldo** (×1,5): 2,0 / 1,5 ≈ 1,34. | Junio y diciembre suben por el aguinaldo con cualquier deflactor. Hay que verificar si el RIPTE incluye el SAC. |
| 3 | **Saldos y plazos fijos en pesos** | `mcuenta_corriente`, `mcuenta_corriente_adicional`, `mcaja_ahorro`, `mcaja_ahorro_adicional`, `mcuentas_saldo`, `minversion1_pesos`, `minversion2` | Tasa de plazo fijo acumulada, fin de mes | crec. 1,36–1,43: **no se parece ni a la tasa (1,53) ni al IPC (1,50)**. | Es el deflactor más discutible, como ya decía `docs/investigacion.md`. Propuesta: correr las dos variantes (tasa e IPC) y reportarlas. |
| 4 | **Comisiones** | `mcomisiones`, `mcomisiones_mantenimiento`, `mcomisiones_otras` | Valor modal del mes (desde el dataset) | La moda de mantenimiento pasa de 723,5 (ene) a 1.092,1 (dic), +51% ≈ IPC, y **salta 18% de golpe en agosto**. Es el patrón "quieta y salta" de la hipótesis. | **En 201905 y 201910 estas columnas valen 0 para todos (D4)**, así que la moda no existe. Propuesta: usar la moda del mes anterior. `mcomisiones` y `mcomisiones_otras` tienen la misma moda y el mismo crecimiento, y pueden ser casi la misma variable. |
| 5 | **Límites** | `Visa/Master_mlimitecompra`, `_mfinanciacion_limite` | Se reemplaza por un cociente: `mconsumototal / mlimitecompra` y `msaldototal / mfinanciacion_limite` | Salto de agosto = 1,000 exacto y crec. anual 2,67: **están quietos y suben de a escalones**. Es la hipótesis confirmada. | ¿Se reemplaza el límite por el cociente o se agrega el cociente y se deja el límite? Para un "brazo" limpio conviene reemplazar. |
| 6 | **Dólares** (están en pesos al tipo de cambio) | `mcaja_ahorro_dolares`, `minversion1_dolares`, `Visa/Master_msaldodolares` | Tipo de cambio, fin de mes | `mcaja_ahorro_dolares`: crec. 1,617 y salto 1,347, **idénticos al tipo de cambio**. O sea, el dataset los informa en pesos. Dividir por el tipo de cambio da dólares. | — |
| 6b | **Consumos y pagos en dólares de tarjeta** | `Visa/Master_mconsumosdolares`, `_mpagosdolares`, `_madelantodolares` | **Ninguno** (parecen estar en dólares de verdad) | crec. ≈ 1,0 y salto ≈ 1,0, con moda 1,16. No se mueven con el tipo de cambio. | Confirmar mirando más meses. Si están en USD, dividirlos por el tipo de cambio los rompe. |
| 7 | **Plazo fijo: posibles columnas invertidas** | `mplazo_fijo_pesos`, `mplazo_fijo_dolares` | ? | **`mplazo_fijo_pesos` se mueve como el dólar** (1,618 y 1,347), y `mplazo_fijo_dolares` no (1,19 y 1,03). | Puede que las etiquetas estén cruzadas en el dataset. Hay que mirarlo antes de asignar. Solo el 0,6% de los clientes tiene `mplazo_fijo_pesos`. |
| 8 | **Préstamos** | `mprestamos_personales`, `_prendarios`, `_hipotecarios` | La propuesta original era CER para los UVA | Hipotecarios: crec. 0,95. **Un préstamo UVA en pesos subiría alrededor de 1,4** (CER +47%, menos la amortización). Personales 0,75 y prendarios 0,77: son saldos que se van pagando. | **No hay evidencia de que haya préstamos UVA.** Propuesta: IPC, o no deflactar, porque el saldo baja por la amortización. El grupo "CER" quedaría vacío. |
| 9 | **Mora y punitorios** | — | Tasa activa | **No hay ninguna columna en pesos de mora o punitorios.** `Visa/Master_delinquency` y `Finiciomora` no son montos. | El grupo queda vacío. ¿Usar la tasa de tarjetas para la deuda financiada (`msaldototal`)? Esa serie el BCRA la publica solo hasta 202004. |
| 10 | **Rentabilidad y márgenes del banco** | `mrentabilidad`, `mrentabilidad_annual`, `mactivos_margen`, `mpasivos_margen` | IPC (propuesta) | crec. 0,81–1,38, con valores negativos. `_annual` suma 12 meses. | Están rotas en 201905 y 201910 (D4). No las pone el cliente sino el banco: ¿IPC o dejarlas sin deflactar? |
| 11 | **Compra y venta de dólares** | `mforex_buy`, `mforex_sell` | Tipo de cambio, promedio del mes | crec. 0,26–0,46: cae por **el cepo de septiembre de 2019**, no por precios. | Tipo de cambio o IPC. El cepo es un quiebre de comportamiento que ningún deflactor arregla. |

## Datos generales que aparecieron

- **Los montos parecen multiplicados por 1,173.** Las modas son 5.865 (= 5.000 × 1,173), 11.730, 117,30, 1.173 y 23.460. Es seguramente la anonimización de la cátedra. Como es un factor constante, no afecta a los árboles ni a la deflactación.
- **El brazo "todo con IPC"** divide las 73 columnas por el IPC, incluidos los dólares y los límites. Así queda definido, y es lo que la hipótesis espera que funcione peor que el brazo por grupos.
- **Objetivo 1:** el IPC y el RIPTE del mes t se publican después, así que al momento de predecir se usa el de t-1. Las series del BCRA (tasas, tipo de cambio, CER) ya están disponibles cuando llega el mes.

## Decisiones que necesitamos tomar entre los tres
1. Grupo 3 (saldos): ¿tasa, IPC o las dos variantes?
2. Grupos 6b y 7: ¿confirmamos las monedas antes de asignar? Es media hora de análisis.
3. Grupos 8 y 9 quedan casi vacíos: ¿se reformula la tabla de deflactores de `docs/investigacion.md`, o se dice explícitamente en el video que el dataset no tiene esas columnas? Esto último también es un resultado.
4. Grupo 5: ¿se reemplaza el límite por el cociente o se agrega el cociente?
5. Grupo 10: ¿IPC o sin deflactar?
