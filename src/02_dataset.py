"""Paso 5: dataset de un brazo del experimento. Features (fe.features_mes) + clase ternaria, un parquet por mes.

Uso:
    python src/02_dataset.py                                        # baseline, sin deflactar -> datasets/fe_base
    python src/02_dataset.py --brazo ipc --desfase 1                # todo con IPC del mes anterior -> datasets/fe_ipc_d1
    python src/02_dataset.py --brazo ipc --desfase 0                # todo con IPC del mismo mes -> datasets/fe_ipc_d0
    python src/02_dataset.py --brazo grupo                          # cada grupo con su deflactor -> datasets/fe_grupo
    python src/02_dataset.py --brazo ipc --con-mes                  # brazo E: IPC + foto_mes -> datasets/fe_ipc_d1_mes
    python src/02_dataset.py --brazo ranking                        # brazo G: ranking por mes -> datasets/fe_ranking
    python src/02_dataset.py --brazo delta_log                      # brazo H: deltas relativos -> datasets/fe_delta_log

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
    salida = a.salida or {"base": "datasets/fe_base", "grupo": "datasets/fe_grupo", "ranking": "datasets/fe_ranking",
                          "delta_log": "datasets/fe_delta_log"}.get(
        a.brazo, f"datasets/fe_{a.brazo}_d{a.desfase}") + ("_mes" if a.con_mes else "")
    os.makedirs(salida, exist_ok=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    monetarias = [c for c in columnas_crudas(con, a.historia, MESES[0]) if es_monetaria(c)]
    transformacion = a.brazo if a.brazo in ("ranking", "delta_log") else None  # D19
    if a.brazo in ("base", "ranking", "delta_log"):
        deflactor = None
    elif a.brazo == "ipc":
        deflactor = brazo_ipc(monetarias, a.desfase)
    else:  # el desfase de cada grupo está fijo en deflactar.GRUPOS
        deflactor = brazo_grupo(monetarias, con, a.historia, [_mes_mas(MESES[0], -k) for k in (2, 1)] + MESES)
    print(f"Brazo {a.brazo} · {len(deflactor or {}) or (73 if transformacion else 0)} columnas transformadas -> {salida}",
          flush=True)
    t0 = time.time()
    for mes in MESES:
        fe = features_mes(con, a.historia, mes, deflactor, transformacion)
        cl = clase_ternaria(con, a.historia, mes)
        destino = os.path.join(salida, f"{mes}.parquet").replace("\\", "/")
        extra = ", fe.foto_mes AS foto_mes_feature" if a.con_mes else ""  # brazo diagnóstico E (D15)
        con.sql(f"SELECT fe.*{extra}, cl.clase_ternaria FROM fe JOIN cl USING (numero_de_cliente)") \
           .write_parquet(destino + ".tmp", compression="zstd")
        os.replace(destino + ".tmp", destino)
        n, ncol = con.sql(f"SELECT count(*) FROM '{destino}'").fetchone()[0], len(fe.columns) + 1
        print(f"{mes}: {n:,} filas · {ncol} columnas · {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--historia", default="historia/mensual")
    p.add_argument("--salida", default=None)
    p.add_argument("--brazo", choices=["base", "ipc", "grupo", "ranking", "delta_log"], default="base")
    p.add_argument("--desfase", type=int, default=1, help="meses de atraso del índice (0 = mismo mes)")
    p.add_argument("--con-mes", action="store_true", help="agrega foto_mes como feature (brazo diagnóstico E)")
    main(p.parse_args())
