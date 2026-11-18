"""Paso 5: dataset de un brazo del experimento. Features (fe.features_mes) + clase ternaria, un parquet por mes.

Uso:
    python src/02_dataset.py                                        # baseline, sin deflactar -> datasets/fe_base
    python src/02_dataset.py --brazo ipc --desfase 1                # todo con IPC del mes anterior -> datasets/fe_ipc_d1
    python src/02_dataset.py --brazo ipc --desfase 0                # todo con IPC del mismo mes -> datasets/fe_ipc_d0
    python src/02_dataset.py --brazo grupo                          # cada grupo con su deflactor -> datasets/fe_grupo
    python src/02_dataset.py --brazo ipc --con-mes                  # brazo E: IPC + foto_mes -> datasets/fe_ipc_d1_mes
    python src/02_dataset.py --brazo ranking                        # brazo G: ranking por mes -> datasets/fe_ranking
    python src/02_dataset.py --brazo delta_log                      # brazo H: deltas relativos -> datasets/fe_delta_log
    python src/02_dataset.py --brazo ranking_post                   # G2: ranking después de lags y deltas
    python src/02_dataset.py --brazo ranking_sin_cero               # G0: ranking sin cero fijo
    python src/02_dataset.py --brazo nominal_ranking                # M: fe_base + fe_ranking (sufijo _rk)
    python src/02_dataset.py --brazo grupo_saldos_ipc               # J: por grupo con IPC en los 8 saldos
    python src/02_dataset.py --brazo mediana                        # K: cada columna / su mediana del mes
    python src/02_dataset.py --brazo grupo --con-mes                # L: por grupo + foto_mes -> datasets/fe_grupo_mes

Meses: 201903–201910 (201901–201902 solo aportan lags; 201911–201912 solo la clase de 201909–201910).
"""
import argparse
import os
import sys
import time

import duckdb
import pyarrow.parquet as pq

sys.path.insert(0, os.path.dirname(__file__))
from deflactar import brazo_grupo, brazo_ipc, brazo_mediana  # noqa: E402
from rankear import es_derivada_monetaria, rankear_historia, rankear_tabla  # noqa: E402
from fe import _mes_mas, clase_ternaria, columnas_crudas, es_monetaria, features_mes  # noqa: E402

MESES = [201903, 201904, 201905, 201906, 201907, 201908, 201909, 201910]
TRANSFORMACIONES = ("ranking", "delta_log", "ranking_post", "ranking_sin_cero")
RANKING_PREVIO = {"ranking": True, "ranking_sin_cero": False}  # rankean la historia antes de lags y deltas


def ranking_post(salida):
    """Prueba G2 (D20): las features de fe_base (lags y deltas en pesos) con cada monetaria rankeada en su mes."""
    for mes in MESES:
        df = pq.read_table(f"datasets/fe_base/{mes}.parquet").to_pandas()
        crudas = {c for c in df.columns if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria")
                  and es_monetaria(c) and "_lag" not in c and "_delta" not in c}
        cols = [c for c in df.columns if es_derivada_monetaria(c, crudas)]
        destino = f"{salida}/{mes}.parquet"
        rankear_tabla(df, cols).to_parquet(destino + ".tmp", index=False)
        os.replace(destino + ".tmp", destino)
        print(f"{mes}: {len(cols)} columnas rankeadas", flush=True)


def nominal_ranking(salida):
    """Prueba M (D20): las 760 features nominales + las 365 monetarias rankeadas de fe_ranking, con sufijo _rk."""
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    rk = [c for c in con.sql("SELECT * FROM 'datasets/fe_ranking/201903.parquet' LIMIT 0").columns
          if c not in ("numero_de_cliente", "foto_mes", "clase_ternaria") and es_monetaria(c)]
    sel = ", ".join(f'r."{c}" AS "{c}_rk"' for c in rk)
    for mes in MESES:
        destino = f"{salida}/{mes}.parquet"
        con.sql(f"""SELECT b.* EXCLUDE (clase_ternaria), {sel}, b.clase_ternaria
                    FROM 'datasets/fe_base/{mes}.parquet' b
                    JOIN 'datasets/fe_ranking/{mes}.parquet' r USING (numero_de_cliente)""") \
           .write_parquet(destino + ".tmp", compression="zstd")
        os.replace(destino + ".tmp", destino)
        print(f"{mes}: {len(rk)} columnas rankeadas agregadas", flush=True)


def main(a):
    salida = a.salida or ("datasets/fe_base" if a.brazo == "base" else
                          f"datasets/fe_ipc_d{a.desfase}" if a.brazo == "ipc" else
                          f"datasets/fe_{a.brazo}") + ("_mes" if a.con_mes else "")
    os.makedirs(salida, exist_ok=True)
    if a.brazo == "nominal_ranking":
        return nominal_ranking(salida)
    if a.brazo == "ranking_post":
        return ranking_post(salida)
    historia = a.historia
    if a.brazo in RANKING_PREVIO:
        historia = f"{a.historia}_{a.brazo}"
        rankear_historia(a.historia, historia, [_mes_mas(MESES[0], -k) for k in (2, 1)] + MESES,
                         cero_fijo=RANKING_PREVIO[a.brazo])
        print(f"Historia rankeada en {historia}", flush=True)
    con = duckdb.connect()
    con.execute("SET memory_limit='6GB'")
    monetarias = [c for c in columnas_crudas(con, a.historia, MESES[0]) if es_monetaria(c)]
    transformacion = "delta_log" if a.brazo == "delta_log" else None  # D19
    meses_lags = [_mes_mas(MESES[0], -k) for k in (2, 1)] + MESES
    if a.brazo in ("base", "delta_log", *RANKING_PREVIO):
        deflactor = None
    elif a.brazo == "mediana":
        deflactor = brazo_mediana(monetarias, con, a.historia, meses_lags)
    elif a.brazo == "grupo_saldos_ipc":
        deflactor = brazo_grupo(monetarias, con, a.historia, meses_lags, saldos_ipc=True)
    elif a.brazo == "ipc":
        deflactor = brazo_ipc(monetarias, a.desfase)
    else:  # el desfase de cada grupo está fijo en deflactar.GRUPOS
        deflactor = brazo_grupo(monetarias, con, a.historia, meses_lags)
    print(f"Brazo {a.brazo} · {len(deflactor or {}) or (73 if transformacion else 0)} columnas transformadas -> {salida}",
          flush=True)
    t0 = time.time()
    for mes in MESES:
        fe = features_mes(con, historia, mes, deflactor, transformacion)
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
    p.add_argument("--brazo", choices=["base", "ipc", "grupo", "grupo_saldos_ipc", "mediana", "nominal_ranking", *TRANSFORMACIONES], default="base")
    p.add_argument("--desfase", type=int, default=1, help="meses de atraso del índice (0 = mismo mes)")
    p.add_argument("--con-mes", action="store_true", help="agrega foto_mes como feature (brazo diagnóstico E)")
    main(p.parse_args())
