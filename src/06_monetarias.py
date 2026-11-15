"""Pasos 4 y 10: inventario de columnas monetarias de 2019 y cómo se mueven frente a cada índice.

Uso:
    python src/06_monetarias.py [carpeta_historia] [carpeta_salida]

Para cada columna monetaria (prefijo m, Visa_m, Master_m):
    pct_no_cero       clientes con valor distinto de 0 en 2019
    crec_anual        mediana, entre clientes con valor > 0 en 201901 y en 201912, de valor_201912 / valor_201901
    salto_ago         lo mismo entre 201907 y 201908 (el tipo de cambio sube ~35% a fin de agosto)
    moda_ene, moda_dic  valor más frecuente (> 0) en 201901 y 201912: muestra los montos "de lista" (comisiones)
Se compara contra los índices de datos_externos/indices_mensuales.csv en el mismo período.
Salida: reportes/paso10/inventario.csv
"""
import os
import sys

import duckdb
import pandas as pd

HISTORIA = sys.argv[1] if len(sys.argv) > 1 else "historia/mensual"
SALIDA = sys.argv[2] if len(sys.argv) > 2 else "reportes/paso10"
os.makedirs(SALIDA, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")

con = duckdb.connect()
con.execute("SET memory_limit='6GB'")
f = lambda m: f"read_parquet('{HISTORIA}/{m}.parquet')"  # noqa: E731
cols = [c for c in con.sql(f"SELECT * FROM {f(201901)} LIMIT 0").columns
        if c.startswith(("m", "Visa_m", "Master_m"))]


def razon_mediana(a, b):
    exprs = ", ".join(f'median(CASE WHEN x."{c}" > 0 AND y."{c}" > 0 THEN y."{c}" / x."{c}" END) AS "{c}"'
                      for c in cols)
    return con.sql(f"SELECT {exprs} FROM {f(a)} x JOIN {f(b)} y USING (numero_de_cliente)").df().iloc[0]


def moda(m):
    exprs = ", ".join(f'mode("{c}") FILTER ("{c}" > 0) AS "{c}"' for c in cols)
    return con.sql(f"SELECT {exprs} FROM {f(m)}").df().iloc[0]


no_cero = con.sql("SELECT " + ", ".join(f'avg(("{c}" <> 0)::INT) AS "{c}"' for c in cols)
                  + f" FROM read_parquet('{HISTORIA}/2019??.parquet')").df().iloc[0]
inv = pd.DataFrame({"pct_no_cero": no_cero, "crec_anual": razon_mediana(201901, 201912),
                    "salto_ago": razon_mediana(201907, 201908),
                    "moda_ene": moda(201901), "moda_dic": moda(201912)})
inv.index.name = "columna"
inv.round(4).to_csv(os.path.join(SALIDA, "inventario.csv"))

ind = pd.read_csv("datos_externos/indices_mensuales.csv", index_col="foto_mes")
ref = pd.DataFrame({
    "crec_anual": ind.loc[201912] / ind.loc[201901],
    "salto_ago": ind.loc[201908] / ind.loc[201907],
}).loc[["ipc", "ripte", "tc_mayorista_prom", "tc_mayorista_fin", "idx_tasa_pf30", "idx_tasa_personales",
        "cer_fin"]]
pd.set_option("display.width", 200)
print("Índices de referencia (mismo período):")
print(ref.round(3).to_string())
print(f"\n{len(cols)} columnas monetarias:")
print(inv.round(3).to_string())
