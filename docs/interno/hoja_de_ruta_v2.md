# Hoja de ruta v2 — Inflación 1, rehacer de punta a punta

> **Reemplazada por [hoja_de_ruta_v3.md](hoja_de_ruta_v3.md)** (17/11).

Receta para correr todo de nuevo incorporando lo mejor de la versión de Manuel. No es para hoy: es para tener claros los pasos. Entrega del video: 23/11 antes del mediodía.

## Idea central
Mantener nuestro diseño (20 semillas pareadas, N fijo y zona plana, índice del mes anterior, datos propios de dólares y comisiones) y sumarle tres cosas de Manuel: criterio de decisión fijado antes de correr, el brazo que prueba el mecanismo (IPC + foto_mes) y el control de los 20 features extra.

## Paso 0 · Acordar con el grupo
- Elegir un repo principal y dejar el otro como réplica independiente.
- Acordar métrica principal, semillas (las 20 de nuestro repo) y quién corre qué.
- Decidir dónde se corre (VM de Manuel de 64 GB o la nuestra) para no duplicar horas de cómputo.

## Paso 1 · Datos y clase
- Reconstruir `clase_ternaria` con el calendario completo cliente × mes (método de Manuel en DuckDB).
- Verificar paridad con nuestro parquet: 1.563.565 filas y 154 columnas en 2019, mismas clases por mes.
- Si no coincide, resolver la diferencia antes de seguir.

## Paso 2 · Índices
- Series: IPC, RIPTE, tipo de cambio, plazo fijo capitalizado, de datos.gob.ar.
- Chequear nuestros valores contra los de Manuel (IPC, RIPTE, TC y PF deberían coincidir).
- Aplicar el rezago de 1 mes a IPC y RIPTE. Dejar el índice del mes corriente solo como sensibilidad.
- Índice de comisiones: moda mensual de `mcomisiones_mantenimiento`.

## Paso 3 · Fijar el criterio de decisión antes de correr
Escribirlo en `DECISIONES.md` antes de ver resultados:
- Métrica primaria: ganancia en 201910 con N = 5.000. Secundarias: zona plana y AUC.
- Un brazo supera a otro si el Wilcoxon pareado da p < 0,05 y gana en al menos 15 de 20 semillas.
- Diferencias menores al ruido (desvío entre semillas) se declaran empate.

## Paso 4 · Grupos de deflactores (versión corregida)
- Consumos, movimientos, préstamos y rentabilidad: IPC.
- Sueldos: RIPTE.
- Saldos en pesos: tasa de plazo fijo.
- Dólares expresados en pesos (caja de ahorro, inversión, plazo fijo): tipo de cambio.
- Consumos y pagos en dólares de tarjeta: no deflactar.
- Comisiones: moda mensual.
- Límites: no deflactar; ratios de uso en su lugar.
- Dejar afuera el grupo "crédito con tasa activa" (no hay UVA ni mora en el dataset).

## Paso 5 · Brazos del experimento
| Brazo | Qué cambia | Pregunta que responde |
|---|---|---|
| A. Nominal | nada | control |
| B. Todo con IPC | 73 columnas ÷ IPC mes anterior | ¿deflactar sirve? |
| C. Por grupo | 7 grupos, cada uno con su deflactor | ¿el índice correcto sirve más? |
| D. Nominal + ratios | agrega los 4 ratios sin deflactar | ¿el 20 features extra del brazo C explican algo? |
| E. IPC + foto_mes | B más `foto_mes` como feature | ¿deflactar borra la señal temporal? |
| F. Por grupo + foto_mes | C más `foto_mes` | mismo chequeo para el brazo C |

D y E son los dos que hoy no tenemos.

## Paso 6 · Hiperparámetros
- Versión 1: los hiperparámetros del baseline para todos los brazos (aísla el efecto de deflactar).
- Versión 2: Optuna propia por brazo (50 trials, TPE), como indican los tutores.
- Repetir la búsqueda con 2 semillas de Optuna para medir cuánto mueve la suerte de la búsqueda.

## Paso 7 · Corridas
- 20 semillas pareadas por brazo y por versión de hiperparámetros.
- Guardar siempre `semillas.csv` y `curva_201910.csv` por brazo.
- Medir tiempos por brazo para no sorprenderse con el cómputo.

## Paso 8 · Tests estadísticos
- Wilcoxon pareado entre todos los pares relevantes, con corrección por comparaciones múltiples.
- Reportar diferencia media, semillas ganadas y p.
- Verificar si deflactar reduce la varianza: comparar desvíos con 20 semillas (con 5 no se distingue del ruido).

## Paso 9 · Mecanismo
- Resultado de E contra B: ¿`foto_mes` recupera lo perdido?
- Dónde caen los cortes de los árboles en las variables monetarias.
- Importancia por grupo de variables en cada brazo.

## Paso 10 · Sensibilidades
- Índice del mes corriente contra el del mes anterior.
- Brazo C con IPC en las 8 columnas de saldos (la decisión más débil).
- Un solo mes de test: si es posible, repetir con otro mes etiquetado.

## Paso 11 · Reportes y repo
- Regenerar tablas y gráficos con el mismo script.
- Actualizar `DECISIONES.md` y el README con los brazos nuevos.
- Verificar que el repo corre desde cero siguiendo el README.
- Pushear a GitHub antes de grabar.

## Paso 12 · Entrega
- Actualizar la presentación (15 diapositivas de la plantilla) y las diapositivas de resultados.
- Escribir el guion y grabar el video de 10 minutos como máximo.
- Subir el video antes del mediodía del 23/11 y preparar la discusión del 24/11.
