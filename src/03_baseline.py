"""Paso 6: LightGBM con el esquema del baseline de Bolaños. Sirve para cualquier dataset con el formato
de 02_dataset.py, así que los brazos del experimento de deflactación corren con el mismo script.

Uso:
    python src/03_baseline.py --dataset datasets/fe_base --nombre baseline [--trials 50] [--semilla 102191]

Esquema:
    Optuna (TPE)  entrena 201903–201906 · valida 201908 con AUC (ordena los trials y hace el early stopping)
    Envíos        se elige N en la curva de ganancia de 201908, de a 500 envíos
    Test          con el mismo esquema de entrenamiento (201903–201906), mide la ganancia en 201910 con ese N
                  (--entrena-test 0308 reentrena sumando 201907–08: solo para el análisis de sensibilidad)
Target binario: BAJA+1 y BAJA+2 contra CONTINUA. La ganancia cuenta solo BAJA+2.
El estudio se guarda en SQLite: si se corta, se relanza el mismo comando y retoma.
"""
import argparse
import json
import os
import sys
import time

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from comun import (ENTRENA, MESES_TEST, FIJOS, PASO_ENVIOS, TEST, VALIDA,  # noqa: E402
                   cargar, curva_ganancia, mejor_n, progreso)


def main(a):
    os.makedirs("modelos", exist_ok=True)
    salida = os.path.join("reportes", a.nombre)
    os.makedirs(salida, exist_ok=True)
    t0 = time.time()

    Xtr, ytr, _ = cargar(a.dataset, ENTRENA)
    Xva, yva, b2va = cargar(a.dataset, [VALIDA])
    dtr = lgb.Dataset(Xtr, ytr, params={"feature_pre_filter": False}, free_raw_data=False).construct()
    dva = lgb.Dataset(Xva, yva, reference=dtr).construct()
    print(f"Datos: train {len(ytr):,} filas · valid {len(yva):,} · {Xtr.shape[1]} features · "
          f"{time.time() - t0:.0f} s", flush=True)

    def objetivo(trial):
        params = dict(FIJOS, seed=a.semilla,
                      learning_rate=trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
                      num_leaves=trial.suggest_int("num_leaves", 8, 1024, log=True),
                      min_data_in_leaf=trial.suggest_int("min_data_in_leaf", 10, 5000, log=True),
                      feature_fraction=trial.suggest_float("feature_fraction", 0.1, 1.0),
                      bagging_fraction=trial.suggest_float("bagging_fraction", 0.5, 1.0))
        t_trial = time.time()
        m = lgb.train(params, dtr, num_boost_round=5000, valid_sets=[dva],
                      callbacks=[lgb.early_stopping(100, verbose=False),
                                 progreso(f"trial {trial.number}", t0, cada=50)])
        auc = m.best_score["valid_0"]["auc"]
        n, gan = mejor_n(curva_ganancia(m.predict(Xva, num_iteration=m.best_iteration), b2va))
        trial.set_user_attr("best_iteration", m.best_iteration)
        trial.set_user_attr("envios_201908", n)
        trial.set_user_attr("ganancia_201908", gan)
        hechos = trial.number + 1
        previos = [t.value for t in estudio.trials if t.state == optuna.trial.TrialState.COMPLETE]
        mejor_auc = max(previos + [auc])
        eta = (time.time() - t0) / max(hechos - hechos_al_inicio, 1) * (a.trials - hechos) / 60
        print(f"  trial {trial.number:>3}/{a.trials} · AUC {auc:.5f} (mejor {mejor_auc:.5f}) · "
              f"iter {m.best_iteration:>4} · ganancia 201908 {gan / 1e6:,.1f} M con {n:,} · "
              f"{time.time() - t_trial:.0f} s el trial · faltan ~{eta:.0f} min", flush=True)
        return auc

    estudio = optuna.create_study(
        study_name=a.nombre, direction="maximize", load_if_exists=True,
        storage=f"sqlite:///modelos/{a.nombre}_optuna.db",
        sampler=optuna.samplers.TPESampler(seed=a.semilla))
    hechos_al_inicio = len(estudio.trials)
    faltan = a.trials - len([t for t in estudio.trials if t.state == optuna.trial.TrialState.COMPLETE])
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    if faltan > 0:
        estudio.optimize(objetivo, n_trials=faltan)
    estudio.trials_dataframe().to_csv(os.path.join(salida, "trials.csv"), index=False)

    mejor = estudio.best_trial
    iteraciones = mejor.user_attrs["best_iteration"]
    n_envios = mejor.user_attrs["envios_201908"]
    params = dict(FIJOS, seed=a.semilla, **mejor.params)
    print(f"Mejor trial {mejor.number}: AUC {mejor.value:.5f} · {iteraciones} iter · N = {n_envios:,}", flush=True)
    del dtr, dva, Xtr, Xva

    # test: modelo con los params e iteraciones del mejor trial, entrenado en los meses de --entrena-test,
    # y el N elegido en 201908
    Xf, yf, _ = cargar(a.dataset, MESES_TEST[a.entrena_test])
    print(f"Modelo final: entrena {a.entrena_test} · {len(yf):,} filas ({iteraciones} iter)", flush=True)
    final = lgb.train(params, lgb.Dataset(Xf, yf, params={"feature_pre_filter": False}),
                      num_boost_round=iteraciones, callbacks=[progreso("final", t0, cada=100)])
    final.save_model(f"modelos/{a.nombre}_final.txt")
    del Xf
    Xte, _, b2te = cargar(a.dataset, [TEST])
    curva = curva_ganancia(final.predict(Xte), b2te)
    n_max, gan_max = mejor_n(curva)
    pd.DataFrame({"envios": np.arange(PASO_ENVIOS, len(curva) + 1, PASO_ENVIOS)}) \
      .assign(ganancia=lambda d: curva[d.envios - 1]) \
      .to_csv(os.path.join(salida, "curva_201910.csv"), index=False)

    resultado = dict(dataset=a.dataset, semilla=a.semilla, entrena_test=a.entrena_test, trials=len(estudio.trials),
                     mejor_trial=mejor.number, auc_201908=mejor.value, params=mejor.params,
                     iteraciones=iteraciones, envios=n_envios,
                     ganancia_201908=mejor.user_attrs["ganancia_201908"],
                     ganancia_201910=float(curva[n_envios - 1]),
                     baja2_201910=int(b2te.sum()),
                     max_201910_informativo=dict(envios=n_max, ganancia=gan_max),
                     segundos=round(time.time() - t0))
    with open(os.path.join(salida, "resultado.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(json.dumps(resultado, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", default="datasets/fe_base")
    p.add_argument("--nombre", default="baseline")
    p.add_argument("--trials", type=int, default=50)
    p.add_argument("--semilla", type=int, default=102191)
    p.add_argument("--entrena-test", choices=sorted(MESES_TEST), default="0306")
    main(p.parse_args())
