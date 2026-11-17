"""Dónde cortan los árboles en las variables monetarias (D18). No entrena nada: lee un modelo guardado.

Uso:
    python src/11_cortes.py [--modelo modelos/baseline_final.txt] [--nominal datasets/fe_base]
                            [--deflactado datasets/fe_ipc_d1] [--mes 201910]

(a) Qué parte del gain de los cortes monetarios está en umbrales en cero (|umbral| <= 1 peso), por tipo.
(b) Qué fracción de los clientes del mes queda del otro lado de cada corte si el valor viene del dataset
    deflactado en vez del nominal, promediada con peso por gain.
Escribe reportes/cortes/{cortes,resumen}.csv.
"""
import argparse
import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(__file__))
from fe import es_monetaria  # noqa: E402

CERO = 1.0  # pesos


def tipo(columna):
    for s in ("lag", "delta"):
        if columna.rsplit("_", 1)[-1].startswith(s):
            return s
    return "mes"


def main(a):
    sys.stdout.reconfigure(encoding="utf-8")
    salida = os.path.join("reportes", "cortes")
    os.makedirs(salida, exist_ok=True)
    arboles = lgb.Booster(model_file=a.modelo).trees_to_dataframe()
    cortes = arboles[arboles.split_feature.notna()].copy()
    total_gain = cortes.split_gain.sum()
    cortes["monetaria"] = cortes.split_feature.map(lambda c: es_monetaria(c))
    mon = cortes[cortes.monetaria].copy()
    mon["tipo"] = mon.split_feature.map(tipo)
    mon["en_cero"] = mon.threshold.abs() <= CERO

    columnas = sorted(mon.split_feature.unique())
    nom = pq.read_table(os.path.join(a.nominal, f"{a.mes}.parquet"), columns=columnas).to_pandas()
    dfl = pq.read_table(os.path.join(a.deflactado, f"{a.mes}.parquet"), columns=columnas).to_pandas()
    cambia = []
    for c, u in zip(mon.split_feature, mon.threshold):
        x, z = nom[c].to_numpy(dtype="float64"), dfl[c].to_numpy(dtype="float64")
        ambos = ~np.isnan(x) & ~np.isnan(z)  # NaN va siempre al mismo lado
        cambia.append(float(((x[ambos] <= u) != (z[ambos] <= u)).sum() / len(x)))
    mon["cambia_de_lado"] = cambia
    mon[["tree_index", "split_feature", "tipo", "threshold", "split_gain", "en_cero", "cambia_de_lado"]] \
        .to_csv(os.path.join(salida, "cortes.csv"), index=False)

    def resumir(g):
        return pd.Series(dict(cortes=len(g), gain_pct_del_modelo=100 * g.split_gain.sum() / total_gain,
                              pct_gain_en_cero=100 * g.split_gain[g.en_cero].sum() / g.split_gain.sum(),
                              pct_cortes_en_cero=100 * g.en_cero.mean(),
                              pct_clientes_cambian=100 * np.average(g.cambia_de_lado, weights=g.split_gain)))
    resumen = pd.concat([mon.groupby("tipo").apply(resumir, include_groups=False),
                         resumir(mon).to_frame("todas").T])
    resumen.to_csv(os.path.join(salida, "resumen.csv"))
    pd.set_option("display.width", 200)
    print(f"Modelo {a.modelo}: {len(cortes):,} cortes, {len(mon):,} sobre variables monetarias\n")
    print(resumen.round(2).to_string())
    top = (mon.groupby("split_feature")
           .agg(gain=("split_gain", "sum"), cortes=("split_gain", "size"),
                pct_gain_en_cero=("en_cero", lambda e: 100 * mon.loc[e.index, "split_gain"][e].sum()
                                  / mon.loc[e.index, "split_gain"].sum()),
                cambia=("cambia_de_lado", "mean"))
           .sort_values("gain", ascending=False).head(15))
    top["gain"] = 100 * top.gain / total_gain
    print("\nLas 15 monetarias con más gain (gain en % del modelo, cambia = fracción media de clientes):")
    print(top.round(3).to_string())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--modelo", default="modelos/baseline_final.txt")
    p.add_argument("--nominal", default="datasets/fe_base")
    p.add_argument("--deflactado", default="datasets/fe_ipc_d1")
    p.add_argument("--mes", type=int, default=201910)
    main(p.parse_args())
