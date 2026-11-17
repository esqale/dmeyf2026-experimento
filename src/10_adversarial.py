"""Validación adversarial de los montos (D17): ¿deflactar les saca el drift a las columnas monetarias?

Uso:
    python src/10_adversarial.py [--brazos fe_base fe_ipc_d1 fe_grupo] [--semillas 5]

Para cada brazo, par de meses y conjunto de columnas (las 73 monetarias del mes, o esas con lags y deltas):
- multivariada: LightGBM que predice el mes, AUC en un 30% estratificado, una vez por semilla;
- univariada: AUC de cada columna sola; drift = |AUC − 0,5|.
Escribe reportes/adversarial/{multivariada,univariada,resumen}.csv.
"""
import argparse
import os
import sys
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(__file__))
from fe import es_monetaria  # noqa: E402

SEMILLA_MADRE = 102191  # las mismas semillas que 04_semillas.py
PARES = [(201903, 201910), (201908, 201910)]
SUFIJOS = ("_lag1", "_lag2", "_delta1", "_delta2")


def conjuntos(columnas):
    crudas = [c for c in columnas if es_monetaria(c) and not c.endswith(SUFIJOS)]
    historicas = [c for c in columnas if c.endswith(SUFIJOS) and c.rsplit("_", 1)[0] in set(crudas)]
    return {"mes": crudas, "mes_lags_deltas": crudas + historicas}


def leer(carpeta, a, b, columnas):
    df = pd.concat([pq.read_table(os.path.join("datasets", carpeta, f"{m}.parquet"), columns=columnas)
                    .to_pandas().assign(_y=int(m == b)) for m in (a, b)], ignore_index=True)
    return df[columnas].astype("float32"), df["_y"].to_numpy()


def multivariada(X, y, semilla):
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, stratify=y, random_state=semilla)
    m = lgb.train({"objective": "binary", "metric": "auc", "verbosity": -1, "seed": semilla,
                   "learning_rate": 0.05, "num_leaves": 31, "num_threads": os.cpu_count()},
                  lgb.Dataset(Xtr, ytr), num_boost_round=300, valid_sets=[lgb.Dataset(Xte, yte)],
                  callbacks=[lgb.early_stopping(30, verbose=False)])
    imp = pd.Series(m.feature_importance("gain"), index=X.columns)
    return m.best_score["valid_0"]["auc"], imp.idxmax()


def univariada(X, y):
    filas = []
    for c in X.columns:
        v = X[c].to_numpy(dtype="float64")
        finitos = np.isfinite(v)
        if np.unique(v[finitos]).size + (not finitos.all()) < 2:
            filas.append(dict(columna=c, auc=0.5, drift=0.0))
            continue
        v = np.where(finitos, v, v[finitos].min() - 1 if finitos.any() else 0)  # NaN = valor más bajo
        auc = roc_auc_score(y, v)
        filas.append(dict(columna=c, auc=auc, drift=abs(auc - 0.5)))
    return pd.DataFrame(filas)


def main(a):
    sys.stdout.reconfigure(encoding="utf-8")
    salida = os.path.join("reportes", "adversarial")
    os.makedirs(salida, exist_ok=True)
    semillas = np.random.default_rng(SEMILLA_MADRE).integers(1, 2**31 - 1, size=20).tolist()[:a.semillas]
    columnas = pq.read_schema(os.path.join("datasets", a.brazos[0], "201903.parquet")).names
    multi, uni, t0 = [], [], time.time()
    for nombre_cols, cols in conjuntos(columnas).items():
        for ma, mb in PARES:
            for brazo in a.brazos:
                X, y = leer(brazo, ma, mb, cols)
                u = univariada(X, y).assign(brazo=brazo, columnas=nombre_cols, par=f"{ma}-{mb}")
                uni.append(u)
                for s in semillas:
                    auc, top = multivariada(X, y, s)
                    multi.append(dict(brazo=brazo, columnas=nombre_cols, par=f"{ma}-{mb}", semilla=s,
                                      auc=auc, columna_top=top))
                print(f"{nombre_cols:16s} {ma}-{mb} {brazo:10s} AUC multi "
                      f"{np.mean([r['auc'] for r in multi[-len(semillas):]]):.4f} · drift univ mediano "
                      f"{u.drift.median():.4f} · {time.time() - t0:.0f} s", flush=True)
    multi, uni = pd.DataFrame(multi), pd.concat(uni, ignore_index=True)
    multi.to_csv(os.path.join(salida, "multivariada.csv"), index=False)
    uni.to_csv(os.path.join(salida, "univariada.csv"), index=False)
    resumen = (multi.groupby(["columnas", "par", "brazo"], sort=False)
               .agg(auc_multi=("auc", "mean"), auc_multi_desvio=("auc", "std"))
               .join(uni.groupby(["columnas", "par", "brazo"], sort=False)
                     .agg(drift_mediano=("drift", "median"), drift_medio=("drift", "mean"),
                          columnas_drift_05=("drift", lambda d: int((d > 0.05).sum())),
                          n_columnas=("drift", "size"))))
    resumen.to_csv(os.path.join(salida, "resumen.csv"))
    pd.set_option("display.width", 200)
    print("\n", resumen.round(4).to_string())


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--brazos", nargs="+", default=["fe_base", "fe_ipc_d1", "fe_grupo"])
    p.add_argument("--semillas", type=int, default=5)
    main(p.parse_args())
