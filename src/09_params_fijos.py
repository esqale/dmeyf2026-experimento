"""Hiperparámetros dados de antemano (sin Optuna) en nuestro esquema: para comparar baselines de otra versión.

Uso:
    python src/09_params_fijos.py --nombre baseline_manuel --semilla 100129 \
        --params '{"num_leaves": 218, "learning_rate": 0.01818, ...}' [--dataset datasets/fe_base]

Entrena 201903–201906 con early stopping de 100 rondas sobre el AUC de 201908, igual que un trial de
03_baseline.py, para obtener las iteraciones y el N de 201908. Escribe reportes/<nombre>/resultado.json con el
mismo formato que 03_baseline.py, así 04_semillas.py lo puede usar con --params.
"""
import argparse
import json
import os
import sys
import time

import lightgbm as lgb

sys.path.insert(0, os.path.dirname(__file__))
from comun import ENTRENA, FIJOS, VALIDA, cargar, curva_ganancia, mejor_n, progreso  # noqa: E402


def main(a):
    sys.stdout.reconfigure(encoding="utf-8")
    salida = os.path.join("reportes", a.nombre)
    os.makedirs(salida, exist_ok=True)
    hiper = json.loads(a.params)
    t0 = time.time()
    Xtr, ytr, _ = cargar(a.dataset, ENTRENA)
    Xva, yva, b2va = cargar(a.dataset, [VALIDA])
    dtr = lgb.Dataset(Xtr, ytr, params={"feature_pre_filter": False})
    dva = lgb.Dataset(Xva, yva, reference=dtr)
    m = lgb.train(dict(FIJOS, seed=a.semilla, **hiper), dtr, num_boost_round=5000, valid_sets=[dva],
                  callbacks=[lgb.early_stopping(100, verbose=False), progreso("validación", t0, cada=100)])
    n, gan = mejor_n(curva_ganancia(m.predict(Xva, num_iteration=m.best_iteration), b2va))
    resultado = dict(dataset=a.dataset, semilla=a.semilla, origen="hiperparámetros fijos (09_params_fijos.py)",
                     auc_201908=m.best_score["valid_0"]["auc"], params=hiper, iteraciones=m.best_iteration,
                     envios=n, ganancia_201908=gan, segundos=round(time.time() - t0))
    with open(os.path.join(salida, "resultado.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--nombre", required=True)
    p.add_argument("--params", required=True, help="JSON con los hiperparámetros")
    p.add_argument("--semilla", type=int, default=102191)
    p.add_argument("--dataset", default="datasets/fe_base")
    main(p.parse_args())
