"""Paso 5: dataset de un brazo del experimento. Features (fe.features_mes) + clase ternaria, un parquet por mes.

Uso:
    python src/02_dataset.py                                        # baseline, sin deflactar -> datasets/fe_base
    python src/02_dataset.py --brazo ipc --desfase 1                # todo con IPC del mes anterior -> datasets/fe_ipc_d1
    python src/02_dataset.py --brazo ipc --desfase 0                # todo con IPC del mismo mes -> datasets/fe_ipc_d0
    python src/02_dataset.py --brazo grupo                          # cada grupo con su deflactor -> datasets/fe_grupo

Meses: 201903–201910 (201901–201902 solo aportan lags; 201911–201912 solo la clase de 201909–201910).
"""
import argparse
import os
import sys
import time

import duckdb

sys.path.insert(0, os.path.dirname(__file__))
from deflactar import brazo_grupo, brazo_ipc  # noqa: E402
from fe import _mes_mas, clase_ternaria, columnas_crudas, es_monetaria, features_mes  # noqa: E402

MESES = [201903, 201904, 201905, 201906, 201907, 201908, 201909, 201910]


def main(a):
    salida = a.salida or {"base": "datasets/fe_base", "grupo": "datasets/fe_grupo"}.get(
        a.brazo, f"datasets/fe_{a.brazo}_d{a.desfase}")
    os.makedirs(salida, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    monetarias = [c for c in columnas_crudas(con, a.historia, MESES[0]) if es_monetaria(c)]
    if a.brazo == "base":
        deflactor = None
    elif a.brazo == "ipc":
        deflactor = brazo_ipc(monetarias, a.desfase)
    else:  # el desfase de cada grupo está fijo en deflactar.GRUPOS
        deflactor = brazo_grupo(monetarias, con, a.historia, [_mes_mas(MESES[0], -k) for k in (2, 1)] + MESES)
    print(f"Brazo {a.brazo} · {len(deflactor or {})} columnas transformadas -> {salida}", flush=True)
    t0 = time.time()
    for mes in MESES:
        fe = features_mes(con, a.historia, mes, deflactor)
        cl = clase_ternaria(con, a.historia, mes)
        destino = os.path.join(salida, f"{mes}.parquet").replace("\\", "/")
        con.sql("SELECT fe.*, cl.clase_ternaria FROM fe JOIN cl USING (numero_de_cliente)") \
           .write_parquet(destino + ".tmp", compression="zstd")
        os.replace(destino + ".tmp", destino)
        n, ncol = con.sql(f"SELECT count(*) FROM '{destino}'").fetchone()[0], len(fe.columns) + 1
        print(f"{mes}: {n:,} filas · {ncol} columnas · {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--historia", default="historia/mensual")
    p.add_argument("--salida", default=None)
    p.add_argument("--brazo", choices=["base", "ipc", "grupo"], default="base")
    p.add_argument("--desfase", type=int, default=1, help="meses de atraso del índice (0 = mismo mes)")
    main(p.parse_args())
