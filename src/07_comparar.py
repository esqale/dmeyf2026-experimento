"""Paso 11: compara brazos del experimento, pareando por semilla (todos usan las mismas semillas de 04_semillas.py).

Uso:
    python src/07_comparar.py baseline ipc_d1 ipc_d0 [--salida reportes/comparacion.csv]

El primer brazo es la referencia. Para cada otro brazo y cada métrica informa la media, la diferencia media
contra la referencia, cuántas semillas gana, el test de Wilcoxon pareado (bilateral) y el t pareado.
"""
import argparse
import os
import sys

import pandas as pd
from scipy import stats

# Máximo de la curva: métrica adicional (D16). Es optimista, porque supone conocido el mejor N del mes de test;
# se informa porque es la métrica de la versión de Manuel y para ver que la conclusión no depende de la métrica.
METRICAS = {"ganancia_n_fijo": "Ganancia N fijo (M)", "ganancia_zona_plana": "Ganancia zona plana (M)",
            "max_informativo": "Máximo de la curva (M, optimista)", "auc_201910": "AUC 201910"}


def leer(nombre):
    r = pd.read_csv(os.path.join("reportes", nombre, "semillas.csv")).set_index("semilla")
    for m in ("ganancia_n_fijo", "ganancia_zona_plana", "max_informativo"):
        r[m] = r[m] / 1e6
    return r


def main(a):
    sys.stdout.reconfigure(encoding="utf-8")
    brazos = {n: leer(n) for n in a.brazos}
    ref_nombre, ref = a.brazos[0], brazos[a.brazos[0]]
    filas = []
    for nombre, r in brazos.items():
        comunes = ref.index.intersection(r.index)
        for m, etiqueta in METRICAS.items():
            fila = dict(brazo=nombre, metrica=etiqueta, semillas=len(r), media=r[m].mean(), desvio=r[m].std())
            if nombre != ref_nombre:
                d = r.loc[comunes, m] - ref.loc[comunes, m]
                fila.update(pareadas=len(comunes), dif_media=d.mean(), dif_desvio=d.std(),
                            gana=int((d > 0).sum()),
                            p_wilcoxon=stats.wilcoxon(d).pvalue if len(d) > 5 and d.abs().sum() > 0 else None,
                            p_t=stats.ttest_rel(r.loc[comunes, m], ref.loc[comunes, m]).pvalue)
            filas.append(fila)
    t = pd.DataFrame(filas)
    t.to_csv(a.salida, index=False)
    pd.set_option("display.width", 200)
    print(f"Referencia: {ref_nombre}\n")
    print(t.round(4).to_string(index=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("brazos", nargs="+")
    p.add_argument("--salida", default="reportes/comparacion.csv")
    main(p.parse_args())
