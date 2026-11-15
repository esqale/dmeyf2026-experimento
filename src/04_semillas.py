"""Paso 7: ruido por semilla. Reentrena el modelo final (201903–201908) con K semillas y mide en 201910.

Uso:
    python src/04_semillas.py --dataset datasets/fe_base --nombre baseline [--params reportes/baseline/resultado.json]
                              [--semillas 20] [--envios 5000]

- Hiperparámetros e iteraciones: los del resultado.json indicado (por defecto, el del baseline). Así los brazos
  del experimento se comparan con los mismos hiperparámetros y solo cambia el dataset.
- Semillas: las mismas K para todos los brazos (generadas desde 102191), para poder hacer comparaciones pareadas.
- Métricas por semilla: ganancia con N fijo (--envios, elegido en 201908 por el baseline), promedio de la zona
  plana de la curva, máximo de la curva (solo informativo) y AUC de 201910.
- Reanudable: si reportes/<nombre>/semillas.csv ya tiene una semilla, la saltea.
Salidas en reportes/<nombre>/: semillas.csv, probs_201910.parquet (probabilidad por cliente y semilla), log.
"""
import argparse
import json
import os
import sys
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.dirname(__file__))
from comun import (ENTRENA_FINAL, FIJOS, TEST, cargar, curva_ganancia,  # noqa: E402
                   ganancia_zona_plana, mejor_n, progreso)

SEMILLA_MADRE = 102191


def main(a):
    salida = os.path.join("reportes", a.nombre)
    os.makedirs(salida, exist_ok=True)
    with open(a.params, encoding="utf-8") as f:
        base = json.load(f)
    semillas = np.random.default_rng(SEMILLA_MADRE).integers(1, 2**31 - 1, size=a.semillas).tolist()
    archivo = os.path.join(salida, "semillas.csv")
    hechas = pd.read_csv(archivo) if os.path.exists(archivo) else pd.DataFrame()
    archivo_probs = os.path.join(salida, "probs_201910.parquet")
    probs = pd.read_parquet(archivo_probs) if os.path.exists(archivo_probs) else None

    t0 = time.time()
    Xf, yf, _ = cargar(a.dataset, ENTRENA_FINAL)
    dtr = lgb.Dataset(Xf, yf, params={"feature_pre_filter": False}, free_raw_data=False).construct()
    df_te = pd.read_parquet(os.path.join(a.dataset, f"{TEST}.parquet"), columns=["numero_de_cliente"])
    Xte, yte, b2te = cargar(a.dataset, [TEST])
    if probs is None:
        probs = df_te.copy()
    print(f"{a.nombre}: {len(yf):,} filas de train · params de {a.params} · {base['iteraciones']} iter · "
          f"N = {a.envios:,} · {time.time() - t0:.0f} s", flush=True)

    filas = hechas.to_dict("records")
    for i, s in enumerate(semillas, 1):
        if len(hechas) and s in set(hechas["semilla"]):
            continue
        t1 = time.time()
        params = dict(FIJOS, **base["params"], seed=s)
        m = lgb.train(params, dtr, num_boost_round=base["iteraciones"],
                      callbacks=[progreso(f"semilla {i}", t0, cada=100)])
        p = m.predict(Xte)
        curva = curva_ganancia(p, b2te)
        n_max, g_max = mejor_n(curva)
        filas.append(dict(semilla=s, ganancia_n_fijo=float(curva[a.envios - 1]),
                          ganancia_zona_plana=ganancia_zona_plana(curva),
                          max_informativo=g_max, envios_max=n_max, auc_201910=roc_auc_score(yte, p)))
        probs[f"s{s}"] = p.astype(np.float32)
        pd.DataFrame(filas).to_csv(archivo, index=False)
        probs.to_parquet(archivo_probs, index=False)
        g = pd.DataFrame(filas)["ganancia_n_fijo"] / 1e6
        eta = (time.time() - t0) / i * (len(semillas) - i) / 60
        print(f"  semilla {i:>2}/{len(semillas)} · {filas[-1]['ganancia_n_fijo'] / 1e6:,.1f} M con {a.envios:,} · "
              f"media {g.mean():,.1f} M · desvío {g.std():,.1f} M · {time.time() - t1:.0f} s · "
              f"faltan ~{eta:.0f} min", flush=True)

    r = pd.DataFrame(filas)
    print("\nResumen (M):")
    print((r[["ganancia_n_fijo", "ganancia_zona_plana", "max_informativo"]] / 1e6)
          .describe().round(1).to_string(), flush=True)
    print(f"AUC 201910: media {r.auc_201910.mean():.5f} · desvío {r.auc_201910.std():.5f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="datasets/fe_base")
    p.add_argument("--nombre", default="baseline")
    p.add_argument("--params", default="reportes/baseline/resultado.json")
    p.add_argument("--semillas", type=int, default=20)
    p.add_argument("--envios", type=int, default=5000)
    main(p.parse_args())
