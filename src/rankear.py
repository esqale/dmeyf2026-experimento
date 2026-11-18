"""Ranking por mes de las columnas monetarias (D19, D20), en pandas: en DuckDB, 73 funciones de ventana por mes
tardaban ~8 min por mes; acá son segundos.

Con cero fijo: 0 queda en 0, cada positivo va a su cume_dist entre los positivos del mes (de 1/n a 1) y cada
negativo a menos su cume_dist entre los negativos, ordenados desde el cero (de -1/n a -1). NULL sigue NULL.
Sin cero fijo: cume_dist entre todos los valores no nulos del mes, ceros incluidos.
cume_dist(x) = cantidad de valores <= x / n, que es rank(method="max") / n.
"""
import os

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from fe import es_monetaria


def rankear_serie(x, cero_fijo=True):
    x = pd.Series(x, dtype="float64")
    r = pd.Series(np.nan, index=x.index)
    if not cero_fijo:
        ok = x.notna()
        r[ok] = x[ok].rank(method="max") / ok.sum()
        return r
    r[x == 0] = 0.0
    pos, neg = x > 0, x < 0
    if pos.any():
        r[pos] = x[pos].rank(method="max") / pos.sum()
    if neg.any():
        r[neg] = -((-x[neg]).rank(method="max") / neg.sum())
    return r


def rankear_tabla(df, columnas, cero_fijo=True):
    out = df.copy()
    for c in columnas:
        out[c] = rankear_serie(df[c], cero_fijo).astype("float32")
    return out


def rankear_historia(origen, destino, meses, cero_fijo=True):
    """Copia los parquets mensuales de `origen` a `destino` con las 73 monetarias rankeadas dentro de cada mes."""
    os.makedirs(destino, exist_ok=True)
    for m in meses:
        df = pq.read_table(os.path.join(origen, f"{m}.parquet")).to_pandas()
        cols = [c for c in df.columns if c not in ("numero_de_cliente", "foto_mes") and es_monetaria(c)]
        rankear_tabla(df, cols, cero_fijo).to_parquet(os.path.join(destino, f"{m}.parquet"), index=False)


def es_derivada_monetaria(columna, monetarias):
    return columna in monetarias or columna.rsplit("_", 1)[0] in monetarias
