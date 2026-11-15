"""Constantes y funciones compartidas por el baseline (03), las semillas (04) y los brazos del experimento."""
import os
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

GANANCIA_ACIERTO = 1_072_500
COSTO_ENVIO = 27_500
PASO_ENVIOS = 500
ZONA_PLANA = (3000, 6500)  # envíos donde la curva del baseline en 201910 es plana (R1)

ENTRENA = [201903, 201904, 201905, 201906]
VALIDA = 201908
# Test en 201910: se reentrena sumando 201907–08 (ENTRENA_EXTENDIDO), como fija el esquema de referencia.
# Usar el modelo entrenado solo en ENTRENA queda como análisis de sensibilidad.
ENTRENA_EXTENDIDO = [201903, 201904, 201905, 201906, 201907, 201908]
MESES_TEST = {"0306": ENTRENA, "0308": ENTRENA_EXTENDIDO}
TEST = 201910
NO_FEATURES = ("numero_de_cliente", "foto_mes", "clase_ternaria")

FIJOS = dict(objective="binary", metric="auc", bagging_freq=1, verbose=-1,
             num_threads=os.cpu_count(), feature_pre_filter=False)


def cargar(carpeta, meses):
    df = pd.concat([pq.read_table(os.path.join(carpeta, f"{m}.parquet")).to_pandas() for m in meses],
                   ignore_index=True)
    X = df.drop(columns=list(NO_FEATURES))
    y = (df["clase_ternaria"] != "CONTINUA").astype(np.int8).to_numpy()
    baja2 = (df["clase_ternaria"] == "BAJA+2").to_numpy()
    return X, y, baja2


def curva_ganancia(prob, baja2):
    """Ganancia acumulada al enviar a los N de mayor probabilidad, para N = 1..len."""
    orden = np.argsort(-prob, kind="stable")
    return np.cumsum(np.where(baja2[orden], GANANCIA_ACIERTO, -COSTO_ENVIO))


def mejor_n(curva):
    """Máximo de la curva mirando solo cortes de a PASO_ENVIOS envíos."""
    cortes = np.arange(PASO_ENVIOS, len(curva) + 1, PASO_ENVIOS)
    n = int(cortes[np.argmax(curva[cortes - 1])])
    return n, float(curva[n - 1])


def ganancia_zona_plana(curva):
    """Promedio de la curva en los cortes de a PASO_ENVIOS dentro de ZONA_PLANA: depende menos del N elegido."""
    cortes = np.arange(ZONA_PLANA[0], ZONA_PLANA[1] + 1, PASO_ENVIOS)
    return float(curva[cortes - 1].mean())


def progreso(etiqueta, t0, cada):
    """Callback de LightGBM: imprime una línea cada `cada` iteraciones para ver que avanza."""
    def _cb(env):
        it = env.iteration + 1
        if it % cada == 0:
            auc = f" · AUC {env.evaluation_result_list[0][2]:.5f}" if env.evaluation_result_list else ""
            print(f"      {etiqueta} · iter {it:>4}{auc} · {time.time() - t0:.0f} s", flush=True)
    return _cb
