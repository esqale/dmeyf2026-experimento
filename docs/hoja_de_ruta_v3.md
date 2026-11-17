# Hoja de ruta v3: un solo repo, lo que falta hasta el video

Escrita el 17/11 después de revisar el repo de Manuel ([vmanuelmarasco/experimento-deflactar](https://github.com/vmanuelmarasco/experimento-deflactar), estado al 17/11). Reemplaza a la v2. Entrega del video: lunes 23/11 antes del mediodía.

## Cómo trabajamos

- **Hay un solo repo:** este (`esqale/dmeyf2026-experimento`). El de Manuel queda como antecedente: no se copian sus notebooks, y lo que sirva se reescribe como script en `src/`.
- **`main` tiene lo que ya está cerrado** (R1–R8).
- **Lo nuevo se hace en la rama `nuevas-pruebas`.** Cada prueba lleva su script, su resultado en `reportes/` y su entrada en `DECISIONES.md`. Cuando está documentada, se pasa a `main`.
- **Reglas de siempre:**
  - Las mismas 20 semillas.
  - Wilcoxon pareado.
  - Métrica principal: ganancia con N = 5.000. Secundarias: zona plana, máximo de la curva y AUC.
  - Si una prueba es nueva, el criterio se escribe antes de correrla.

## 1. Lo que ya está (en `main`)

| | Resultado |
|---|---|
| Hipótesis | **No se confirma.** Deflactar no mejora la ganancia, ni con IPC ni por grupo. El baseline gana en las 20 semillas en la zona plana. |
| Por grupo contra IPC | Con los hiperparámetros del baseline, por grupo gana por +2,1 M (R4). Con Optuna propia por brazo empatan (R5). **No es robusto.** |
| Objetivo 1 (índice del mes anterior) | Cuesta ~1,5 M frente al del mismo mes (R3). Es un costo chico. |
| Objetivo 2 (ruido) | Desvío de ±3,3 M con N fijo. Sin las 20 semillas y el chequeo de Optuna, el +2,1 M habría parecido un hallazgo. |
| IPC + `foto_mes` | Empata con el IPC solo (R6, y R7 con Optuna propia). Devolverle el mes al modelo no recupera nada. |
| Métrica | Con el máximo de la curva (D16) el orden de los brazos es el mismo. |
| Modelo base nuestro contra el de Manuel | Los hiperparámetros de Manuel en nuestro pipeline empatan en ganancia, y nuestro AUC es mejor (R8). **Por eso el repo principal es este.** |

## 2. Qué aporta el repo de Manuel y cómo queda

| Prueba de Manuel (5 semillas) | Lo que concluye él | Lo que da con 20 semillas (nuestro) | Qué hacemos |
|---|---|---|---|
| Tres brazos | Sin deflactar > IPC > por grupo | Mismo resultado de fondo | Ya está |
| "Deflactar estabiliza": el desvío baja de 4,6 M a 1,1–2,1 M | Hallazgo lateral | **No se replica:** el desvío es igual o mayor al deflactar (2,1 M contra 2,1–3,4 M). Sí se replica que se mandan algo más de envíos (4.000 contra 4.400–4.750). | Documentarlo (tarea A) |
| IPC + `foto_mes` | Recupera un tercio (+1,2 M, 5/5 semillas) | Empate (+0,7 M, p = 0,49; con Optuna propia, −0,7 M) | Documentarlo (A) |
| `foto_mes` numérico | Octubre queda fuera del rango de entrenamiento, y el árbol lo trata como agosto | Vale también para nuestro R6 | Anotarlo como limitación (A) |
| Índice del mes anterior | Da igual (+1,0 M) | Cuesta 1,7 M (p = 0,04). La conclusión práctica es la misma: es chico. | Documentarlo (A) |
| Mes de referencia del índice | No importa: cambiar la base multiplica todo por una constante | Vale igual para nosotros | Una línea en el documento (A) |
| Validación adversarial (qué columnas delatan el mes) | El drift viene de columnas no monetarias (`tmobile_app` no existe antes de 201907, fechas de tarjeta, rentabilidad). Deflactar no lo saca. | No lo corrimos. `tmobile_app` nula hasta 201906 está verificada en nuestros datos. | **Prueba nueva, mejorada (tarea B)** |

## 3. Lo que falta, por prioridad

| # | Tarea | Tipo | Tiempo | Para cuándo |
|---|---|---|---|---|
| **A ✔** | Registrar R9, la comparación con las pruebas de Manuel (tabla de la sección 2), en `DECISIONES.md` y `investigacion.md` | Solo documentación | 30 min | mié 18/11 |
| **B ✔** | Validación adversarial **solo con las 73 columnas monetarias**: nominal contra IPC contra por grupo, 201903 contra 201910, varias semillas. Responde directamente si deflactar les saca el drift a los montos (Manuel la corrió con todas las columnas, y por eso el AUC queda pegado a 1 y no se puede comparar). Criterio escrito antes (D17). | Prueba nueva, `src/10_adversarial.py` | ~1 h | mié 18/11 |
| C ✔ | Pasar `nuevas-pruebas` a `main` con A y B | Repo | 10 min | jue 19/11 |
| D | Guion y diapositivas del video (plantilla de 15 diapositivas) | Entrega | 1 día | vie 20/11 |
| E | Grabar y subir el video | Entrega | — | dom 22/11 (margen hasta el lunes 23/11 a las 12) |

**Hecho fuera de la lista:** dónde caen los cortes de los árboles (D18, R11). La explicación "la señal está en el cero" queda descartada: los cortes caen en montos chicos, y deflactar cambia de lado solo al ~2% de los clientes por corte.

### Otras formas de corregir la inflación (decidido el 17/11)

El tema del experimento es la inflación, así que solo entran pruebas que la corrigen de otra manera. Un dato ordena la lista: **a un árbol no le importa una transformación monótona aplicada igual a todos los meses** (el log de una columna da el mismo modelo). Solo puede cambiar algo una transformación que trate distinto a cada mes o que cambie los lags y deltas.

Todas usan el mismo protocolo: criterio escrito antes, 20 semillas pareadas, hiperparámetros del baseline y la rama `nuevas-pruebas`. Cada una lleva ~1 h 15 min.

| # | Prueba | Qué hace | Cuándo |
|---|---|---|---|
| G | **Ranking por mes con cero fijo** | El 0 queda en 0; positivos y negativos se rankean entre sí dentro de cada mes, con su signo. Saca el nivel de precios sin ningún índice. | Antes del video |
| H | **Deltas relativos** | Montos del mes y lags nominales. Los deltas pasan a ser tasas de crecimiento: diferencia del log con signo. | Antes del video |
| I | Normalización por cuantiles contra 201901 | Lleva la distribución de cada mes a la de 201901. Es como el ranking, pero conserva los montos en pesos de enero. | Si sobra tiempo |
| J | Por grupo con IPC en las 8 columnas de saldos | Cambia la decisión más débil del brazo por grupo, que es la crítica más previsible en clase. | Después del video |
| K | Dividir cada columna por su propia mediana mensual | Un índice por columna sacado del dato. Trampa: la mediana también cambia por quién tiene el producto. | Después del video |
| L | Por grupo + `foto_mes` | Completa R6–R7. Se espera empate. | Después del video |

**Descartadas, y por qué:**
- Log con signo en los montos del mes: el árbol da el mismo modelo. Lo que sí cambia, los deltas, es la prueba H.
- Z-score con media y desvío: corre el cero y lo dominan los extremos. La versión robusta es la K.
- Índice para clase alta (canasta de la ENGHo por tramo de ingreso): efecto chico en 2019, se mezcla con la señal de baja y no hay tiempo.
- Ratios entre columnas: no corrigen los montos, agregan variables nuevas.
- Otra unidad (dólar, RIPTE): es el brazo IPC con otra serie.

**No son inflación; van al pipeline productivo (trabajo B):**
- Sacar las columnas rotas en 201910: rentabilidad, márgenes y comisiones valen 0 para todos (R10).
- Pesar las filas de entrenamiento según cuánto se parecen al mes de test.
- Entrenar con meses más cercanos.

En el experimento, los cortes de los datos entran solo como contexto (R10): el drift grande no es inflación.

**Bibliografía:** se le pide a una investigación profunda el prompt del 17/11, centrado en inflación. Sus resultados pueden reordenar G–L.

**Quedan fuera** (van a "Futuros experimentos" del documento):
- Otro mes de test.
- Ventanas largas de 2020–21.
- Optuna con varias semillas.
- Corrección por comparaciones múltiples.

**Ya no hace falta:** el brazo D de la v2 (nominal + ratios). Nuestro brazo por grupo *reemplaza* los límites por los ratios y no los agrega, así que no tiene features extra que controlar.

**Estado al 17/11:** A, B y C hechas (R9, D17, R10; merge a `main`). También R11. G y H en curso. La rama `nuevas-pruebas` sigue abierta para las pruebas que vengan.

## 4. Para el grupo

- Acordar que el repo principal es este y que Manuel suma sus pruebas acá, en una rama.
- Repartir el guion del video.
