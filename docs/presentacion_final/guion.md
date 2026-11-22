# Guion del video · Inflación 1

Base: "Guion Video v1" de Alex, reconstruido diapositiva por diapositiva sobre `index.html`. Los números salen del repo (`DECISIONES.md`, `docs/investigacion.md`).

---

## Diapositiva 1 · Portada (0:00 – 0:45) · Persona 1

Hola a todos. Hoy vamos a presentar los resultados de nuestro experimento colaborativo sobre el impacto de la inflación en los modelos de predicción de abandono de clientes, o churn, de una entidad bancaria. La inflación es el aumento continuo y generalizado de los precios, y afecta directamente los hábitos de consumo de las personas. Cuando entrenamos un modelo con datos monetarios de distintos meses, nos enfrentamos a un problema: un peso de enero no vale lo mismo que un peso de diciembre.

## Diapositiva 2 · Hipótesis (0:45 – 2:30) · Persona 1

Para poder comparar montos de meses distintos usamos una técnica económica llamada deflactar: llevar todos los valores a los precios de un mismo mes de referencia. Se divide el monto por el índice de precios de su mes y se multiplica por el índice del mes de referencia. Por ejemplo, si en enero de 2019 el IPC era 100 y un cliente gastó 50.000 pesos, su gasto real es de 50.000. Si en enero de 2020 el IPC se duplicó a 200 y otro cliente gastó 60.000 pesos, a precios de 2019 gastó apenas 30.000. A simple vista parecía gastar más, pero en términos reales consumió bastante menos.

A partir de esto planteamos nuestra hipótesis: usar un deflactor distinto para cada grupo de variables da más ganancia que dividir todas las variables por el IPC. ¿Por qué lo pensamos? Porque dentro de un banco las variables no se mueven todas al mismo ritmo. Un consumo con tarjeta sigue la inflación mes a mes. Una comisión se mantiene quieta durante meses y de repente pega un salto. Y un límite de tarjeta puede quedar congelado todo un año. Si dividimos las tres por el IPC, arreglamos los consumos, pero a las comisiones y a los límites les inventamos una caída que nunca existió.

Por eso esperábamos que el modelo sin deflactar tuviera la ganancia más baja, el deflactado todo por IPC quedara en el medio y el de un deflactor por grupo lograra la más alta. Y sabríamos que nos equivocamos si los dos deflactados empataban, si el de grupos perdía, o si ninguno le ganaba al modelo sin deflactar.

Le doy el pase a Persona 2 para que nos cuente cómo diseñamos el experimento.

## Diapositiva 3 · Objetivos (2:30 – 3:30) · Persona 2

Gracias. Para poner a prueba esta hipótesis trabajamos únicamente con datos de 2019 y nos fijamos cinco objetivos:

1. Medir cuánto cuesta usar el índice del mes anterior, que es el único disponible en la vida real al momento de predecir, en lugar del índice del mes corriente.
2. Medir cuánto varía la ganancia por simple azar al cambiar la semilla del modelo, para saber si una diferencia es real o es ruido.
3. Clasificar las 73 columnas monetarias del dataset según quién fija el valor y cómo se ajusta, y asignarle a cada grupo su deflactor.
4. Comparar tres modelos, o "brazos", con LightGBM: sin deflactar, todo dividido por el IPC, y cada grupo con su propio deflactor.
5. Y la pregunta previa a la del deflactor por grupo: ¿deflactar mejora frente a no deflactar? ¿Corregir la inflación sirve de algo en este problema?

## Diapositiva 4 · Diseño 1/2, el baseline (3:30 – 4:15) · Persona 2

Los tres brazos son exactamente el mismo modelo: lo único que cambia es cómo se tratan las 73 columnas monetarias antes de armar los lags y los deltas. Usamos las 152 columnas del dataset más sus lags y deltas de uno y dos meses, 760 variables en total. Entrenamos con marzo a junio, validamos en agosto y medimos la ganancia en octubre, después de reentrenar con marzo a agosto.

Tomamos tres decisiones que condicionan todo. Primero, se deflacta antes de calcular lags y deltas, porque un delta sobre montos nominales mezcla el cambio real del cliente con la inflación. Segundo, los tres brazos usan los mismos hiperparámetros, los del baseline, para que lo único que cambie sea el dato; como eso puede favorecer al modelo sin deflactar, lo repetimos con una optimización propia para cada brazo. Y tercero, los tres corren con las mismas 20 semillas, para compararlos de a pares.

La métrica principal es la ganancia con 5.000 envíos, un número que elegimos en agosto sin mirar octubre. Como apoyo miramos la ganancia media en la zona plana de la curva, entre 3.000 y 6.500 envíos.

## Diapositiva 5 · Diseño 2/2, los deflactores (4:15 – 5:30) · Persona 2

¿Cómo agrupamos las 73 columnas monetarias? Con reglas según quién fija cada valor y cómo se ajusta. Los consumos, movimientos y préstamos los dividimos por el IPC del INDEC, del mes anterior, que es el que está publicado al predecir. El sueldo, por el índice de salarios RIPTE. Los saldos en pesos y los plazos fijos, por la tasa de plazo fijo acumulada del Banco Central. Las columnas de dólares que el banco informa en pesos, por el tipo de cambio de fin de mes, y la compra y venta de dólares, por el tipo de cambio promedio. Las comisiones, por su valor más frecuente en cada mes dentro del propio dataset. Por ejemplo, un cliente paga 925 pesos de mantenimiento en julio y 1.092 en agosto: sin deflactar, el modelo ve una suba de 166 pesos, como si a ese cliente le hubiera pasado algo. Pero en agosto el banco subió la comisión de lista para todos. Dividido por la comisión más frecuente de cada mes, el cliente queda igual en los dos meses: el aumento de lista desaparece, porque no dice nada de ese cliente. Y los consumos de tarjeta en dólares no se tocan, porque ya están en dólares.

Los límites de tarjeta son el caso especial: quedan congelados durante meses, así que dividirlos por el IPC les inventa una caída. En su lugar los reemplazamos por cocientes de uso: cuánto consume el cliente sobre su límite. Como reemplazan a los límites y no se suman, los tres brazos tienen exactamente las mismas 760 variables.

Al explorar los datos confirmamos la intuición de los escalones: la comisión de mantenimiento más frecuente pasó de 723 a 1.092 pesos en el año, con un salto del 18% en agosto, y los límites de tarjeta no se movieron entre julio y agosto. También tuvimos sorpresas: los préstamos hipotecarios no se mueven como UVA y no hay montos de mora en pesos, así que los grupos previstos para el CER y la tasa activa quedaron vacíos. Y la columna de plazo fijo en pesos se mueve exactamente como el dólar, así que la tratamos como una columna en dólares.

## Diapositiva 6 · Limitaciones (5:30 – 6:15) · Persona 3

Gracias. Antes de ver los números, hay limitaciones que condicionan lo que podemos concluir. La más importante: toda la comparación se mide en un solo mes de test, octubre de 2019, con 632 bajas. Acertar unas decenas de clientes más o menos mueve la ganancia en decenas de millones. Y ese mes cae justo después de las PASO de agosto y del cepo de septiembre, con un dólar que saltó un 35% en agosto: es un período atípico, y no sabemos si el resultado vale igual en un período normal.

Además, la ventana es corta: aunque 2019 cerró con una inflación del 54%, entre marzo y octubre los precios suben solo un 27%. En octubre, justo nuestro mes de test, las comisiones y la rentabilidad valen cero para todos los clientes, así que ningún deflactor puede cambiar algo en esas columnas. Y la clasificación en grupos es una decisión nuestra, no un dato: por ejemplo, ningún índice sigue bien a los saldos, que crecen menos que la tasa de plazo fijo y que el IPC.

Por último, una aclaración: deflactar solo puede tener efecto entre meses. Dentro de un mismo mes, dividir a todos los clientes por la misma constante no cambia su orden.

## Diapositiva 7 · Resultados 1/4, el ruido de semilla (6:15 – 6:45) · Persona 3

Ahora sí, los resultados. Primero, cuánto se mueve la ganancia por azar. Corrimos el modelo sin deflactar con 20 semillas distintas: con 5.000 envíos da en promedio 284 millones, con un desvío de 3,3 millones. Cada punto de la figura es una semilla: la misma receta, solo cambiando la semilla, da entre 279 y 289 millones. Por eso no alcanza con correr cada brazo una vez: corremos cada uno con 20 semillas y comparamos los promedios. Así, una diferencia de 2 o 3 millones entre brazos ya se distingue del azar; una de 1 millón, no. Si miramos el promedio de la zona plana, entre 3.000 y 6.500 envíos, el desvío baja a 1,9 millones, porque depende menos del corte exacto.

## Diapositiva 8 · Resultados 2/4, los tres brazos (6:45 – 7:45) · Persona 3

Ahora la comparación principal, con los hiperparámetros del baseline y las mismas 20 semillas. El modelo sin deflactar da 284 millones con 5.000 envíos. Deflactar todo con el IPC del mes anterior da 282,3: con 5.000 envíos la diferencia no se distingue del azar, pero en la zona plana pierde casi 5 millones y no le gana al baseline en ninguna de las 20 semillas. El brazo por grupo da 284,4 con 5.000 envíos, empatado con el baseline, y en la zona plana pierde 3,5 millones.

O sea: la primera parte de la hipótesis se cumple, porque deflactar por grupo le gana a deflactar todo por IPC, por unos 2 millones. Pero no es robusta: cuando repetimos todo con una optimización de hiperparámetros propia para cada brazo, por grupo e IPC empatan. Y la segunda parte no se cumple: ninguna forma de deflactar le gana al modelo sin deflactar, ni con los hiperparámetros del baseline ni con los propios. El orden real quedó al revés de lo esperado en los extremos: el modelo sin deflactar arriba y el IPC abajo.

## Diapositiva 9 · Resultados 3/4, el índice del mes anterior y la pista del mes (7:45 – 8:30) · Persona 3

Sobre el primer objetivo: en la práctica, al predecir un mes, su IPC todavía no está publicado, así que hay que usar el del mes anterior. Comparamos las dos versiones con 20 semillas: usar el del mes anterior cuesta entre 1,4 y 1,7 millones, algo chico, del orden del ruido de una semilla. Y aun con el índice verdadero, deflactar no le gana al modelo sin deflactar.

¿Por qué pierde deflactar? Una explicación posible era que los montos sin deflactar le dicen al modelo en qué mes está, y deflactar borra esa pista. Lo probamos devolviéndole el mes como variable al brazo de IPC, con el criterio escrito antes de correrlo. Resultado: empate, no recupera nada, ni con los hiperparámetros del baseline ni con los propios. Así que la pérdida no viene de la pista del mes, sino del monto nominal en sí.

## Diapositiva 10 · Resultados 4/4, ¿deflactar le saca el drift a los montos? (8:30 – 9:15) · Persona 3

Para entender por qué deflactar no ayuda, hicimos una validación adversarial: entrenamos un modelo que intenta distinguir clientes de marzo de clientes de octubre usando solo las columnas monetarias. Si una columna los distingue fácil, es que cambió entre meses, y si deflactar funcionara, tendría que dejar de distinguirlos. Deflactar reduce ese cambio un 30%, menos de la mitad que habíamos fijado como criterio.

¿Por qué tan poco? Porque lo que más cambia en los montos no es la inflación: son cortes de los datos. La rentabilidad, las comisiones y los márgenes valen cero para todos en octubre, y las transferencias recibidas casi no existen antes de junio. Ningún deflactor toca eso. Donde sí hay inflación, en consumos, saldos y límites, deflactar la corrige, pero ese cambio era chico. Y en el modelo, deflactar con IPC cambia de lado de un corte a solo el 2% de los clientes: mueve muy poco.

## Diapositiva 11 · Discusión 1/2, resultados contra hipótesis (9:15 – 10:00) · Persona 3

Volviendo a la hipótesis: no se sostiene, y la pregunta previa tampoco. Deflactar no le gana a no deflactar: con 5.000 envíos empatan y en la zona plana los deflactados pierden en casi todas las semillas. Por grupo sí le gana al IPC, pero solo con los hiperparámetros del baseline; con una optimización propia para cada brazo, empatan.

¿Por qué? Porque corregíamos la parte chica del problema: lo que más cambia entre meses en los montos son cortes de los datos, y la inflación, que deflactar sí corrige, era un cambio chico. Y no es una cuestión de qué índice elegimos: probamos ocho variantes más, desde el IPC del mismo mes hasta la mediana de cada columna, y ninguna le gana al modelo sin deflactar.

## Diapositiva 12 · Discusión 2/2, otras fuentes y qué sí funcionó (10:00 – 11:00) · Persona 3

Si comparamos con la bibliografía: Eurostat recomienda deflactar cada flujo con su propio índice, que es justamente lo que probamos, y no le ganó a no deflactar; esa recomendación sirve para medir la economía, no para predecir bajas. La norma contable, la NIC 29, pide un único índice general, y eso sí coincide con lo que vimos: los índices por grupo no tienen una ventaja robusta. Y Breiman ya anticipaba el límite: como un árbol no cambia si se transforma cada variable de forma monótona, deflactar solo puede actuar entre meses.

Al ver el resultado negativo probamos correcciones que no dividen los montos, y una funcionó muy bien: calcular los deltas como tasa de crecimiento en lugar de diferencia en pesos. Le gana al modelo sin deflactar por 5 millones con 5.000 envíos y por 2 en la zona plana, se repite en otro mes de test, septiembre, y se sostiene con hiperparámetros propios. El ranking del cliente dentro de su mes también mejora con 5.000 envíos, pero empata en la zona plana. En vez de corregir el nivel de cada monto, corrigen el cambio entre meses. O sea: lo que falla no es corregir la inflación, sino corregirla dividiendo los montos por un índice.

## Diapositiva 13 · Conclusiones (11:00 – 11:45) · Persona 3

En conclusión: deflactar los montos no mejora la ganancia del modelo de churn. Deflactar por grupo le gana a deflactar todo por IPC, pero no de forma robusta. El dato más claro: en la zona plana, el modelo sin deflactar le gana al IPC en las 20 semillas y al brazo por grupo en 19. Cumplimos los cinco objetivos, y la razón del resultado es que corregíamos la parte chica del problema.

Nuestras recomendaciones para la comisión son tres. No dividan los montos por un índice: cuesta trabajo y resta ganancia. Si igual deflactan, usen el índice del mes anterior: es el único disponible al predecir y cuesta poco. Y antes de corregir nada, midan qué está cambiando entre meses con una validación adversarial.

## Diapositiva 14 · Futuros problemas y experimentos (11:45 – 12:30) · Persona 3

Nos quedan preguntas abiertas que salen de nuestros propios resultados. La más llamativa: deflactar cambia de lado de un corte a solo el 2% de los clientes, ¿cómo puede entonces costar entre 3,5 y 4,9 millones en casi todas las semillas? Segunda: si lo que se pierde al deflactar es el monto en pesos, ¿ese monto informa por sí mismo? Se puede probar sacando los montos del mes y dejando solo lags y deltas. Y tercera: los deltas relativos suben la ganancia sin mejorar el AUC, ¿mejoran el orden solo cerca del corte?

Como extensiones, lo primero es confirmar los deltas relativos: calcular los deltas como tasa de crecimiento sumó 5 millones en septiembre y en octubre, pero es todo 2019, y falta probarlo en otros años y con más inflación antes de recomendarlo. Y lo segundo, combinarlos con el ranking dentro del mes, porque las dos correcciones que funcionaron actúan sobre cosas distintas.

## Diapositiva 15 · Anexo (12:30 – 12:45) · Persona 3

Todo el experimento está en nuestro repositorio de GitHub: los scripts numerados en el orden en que se corren, las decisiones y resultados con sus criterios en DECISIONES.md, y el informe completo en docs/investigacion.md. El README explica cómo reproducirlo desde el dataset de la cátedra. Muchas gracias.
