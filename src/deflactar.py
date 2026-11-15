"""Divisores por columna y mes para fe.features_mes(deflactor=...). Un brazo del experimento = una función acá.

Los índices se normalizan a 201901 = 1, para que los montos deflactados queden en pesos de enero de 2019.
`desfase` es cuántos meses atrás se toma el índice:
    0 = índice del mismo mes (no disponible al momento de predecir para IPC y RIPTE, que salen a mediados de t+1)
    1 = índice del mes anterior (objetivo 1 del experimento)
"""
import pandas as pd

from fe import _mes_mas

INDICES = "datos_externos/indices_mensuales.csv"
BASE = 201901


def serie_normalizada(columna, archivo=INDICES):
    ind = pd.read_csv(archivo, index_col="foto_mes")[columna].dropna()
    return ind / ind.loc[BASE]


def divisores(columnas, serie, desfase=0):
    """{columna: {foto_mes: divisor}}: todas las columnas con el mismo índice, tomado `desfase` meses atrás."""
    idx = serie_normalizada(serie)
    por_mes = {m: float(idx.loc[_mes_mas(m, -desfase)]) for m in idx.index if _mes_mas(m, -desfase) in idx.index}
    return {c: por_mes for c in columnas}


def brazo_ipc(columnas_monetarias, desfase=1):
    """Brazo 2: las 73 columnas monetarias divididas por el IPC."""
    return divisores(columnas_monetarias, "ipc", desfase)
