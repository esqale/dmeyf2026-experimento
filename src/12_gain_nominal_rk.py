"""Prueba M (D20, R14): en modelos finales de nominal_ranking, qué parte del gain monetario va a las nominales
y qué parte a las _rk. Entrena 3 modelos (semillas 1-3 de 04_semillas) con 201903-08 y los hiperparámetros del baseline.

Uso (desde la raíz del repo): python src/12_gain_nominal_rk.py
Salidas: reportes/nominal_ranking/gain_nominal_vs_rk.csv y gain_top30.csv
"""
import json
import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from comun import ENTRENA_EXTENDIDO, FIJOS, cargar  # noqa: E402
from fe import es_monetaria  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

base = json.load(open("reportes/baseline/resultado.json", encoding="utf-8"))
semillas = np.random.default_rng(102191).integers(1, 2**31 - 1, size=20).tolist()
X, y, _ = cargar("datasets/fe_nominal_ranking", ENTRENA_EXTENDIDO)
d = lgb.Dataset(X, y, params={"feature_pre_filter": False})
filas = []
for s in semillas[:3]:
    m = lgb.train(dict(FIJOS, **base["params"], seed=s), d, num_boost_round=base["iteraciones"])
    g = pd.Series(m.feature_importance("gain"), index=m.feature_name())
    rk = g[[c.endswith("_rk") for c in g.index]].sum()
    nom = g[[es_monetaria(c) and not c.endswith("_rk") for c in g.index]].sum()
    filas.append(dict(semilla=s, gain_total=g.sum(), gain_monetario_nominal=nom, gain_monetario_rk=rk,
                      share_nominal=nom / (nom + rk), share_monetario=(nom + rk) / g.sum()))
    print(filas[-1], flush=True)
    if s == semillas[0]:
        g.sort_values(ascending=False).head(30).to_csv("reportes/nominal_ranking/gain_top30.csv")
t = pd.DataFrame(filas)
t.to_csv("reportes/nominal_ranking/gain_nominal_vs_rk.csv", index=False)
print(t[["share_nominal", "share_monetario"]].describe().round(3))
