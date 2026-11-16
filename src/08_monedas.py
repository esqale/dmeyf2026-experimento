"""Paso 10, decisión 2: ¿en qué moneda están las columnas "dólares"? ¿Están cruzadas las de plazo fijo?

Uso:
    python src/08_monedas.py [carpeta_historia]

Tres pruebas, todas con 2019:
    a) Mediana mes a mes (clientes con valor > 0), normalizada a 201901 = 1, contra el tipo de cambio.
       Una columna en pesos al tipo de cambio sube con el dólar (+35% a fin de agosto); una en USD no.
    b) Tarjetas: si mconsumototal = mconsumospesos + mconsumosdolares × TC, los "dólares" están en USD.
       Se mide la mediana de (total − pesos) / dólares por mes y se compara con el tipo de cambio.
    c) Nivel: mediana y percentiles de cada columna en 201907, para ver si los montos son de pesos o de USD.
Salidas en reportes/paso10/: monedas_mediana_mensual.csv, monedas_identidad_tarjeta.csv
"""
import os
import sys

import duckdb
import pandas as pd

HISTORIA = sys.argv[1] if len(sys.argv) > 1 else "historia/mensual"
SALIDA = "reportes/paso10"
os.makedirs(SALIDA, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 250)

MESES = [201900 + m for m in range(1, 13)]
COLS = ["mcaja_ahorro_dolares", "minversion1_dolares", "mplazo_fijo_dolares", "mplazo_fijo_pesos",
        "Visa_msaldodolares", "Master_msaldodolares",
        "Visa_mconsumosdolares", "Master_mconsumosdolares", "Visa_mpagosdolares", "Master_mpagosdolares",
        "Visa_madelantodolares", "Master_madelantodolares",
        "Visa_mconsumospesos", "mcaja_ahorro", "minversion1_pesos"]

con = duckdb.connect()
con.execute("SET memory_limit='6GB'")
f = lambda m: f"read_parquet('{HISTORIA}/{m}.parquet')"  # noqa: E731
ind = pd.read_csv("datos_externos/indices_mensuales.csv", index_col="foto_mes").loc[MESES]

# a) mediana mensual normalizada
filas = []
for m in MESES:
    r = con.sql("SELECT " + ", ".join(f'median("{c}") FILTER ("{c}" > 0) AS "{c}"' for c in COLS)
                + f" FROM {f(m)}").df().iloc[0]
    filas.append(r.rename(m))
med = pd.DataFrame(filas)
med.index.name = "foto_mes"
norm = med / med.iloc[0]
norm["TC_fin"] = ind.tc_mayorista_fin / ind.tc_mayorista_fin.iloc[0]
norm["IPC"] = ind.ipc / ind.ipc.iloc[0]
norm.round(3).to_csv(os.path.join(SALIDA, "monedas_mediana_mensual.csv"))
print("a) Mediana mensual (> 0), 201901 = 1:")
print(norm.T.round(2).to_string())

# b) identidad de las tarjetas
filas = []
for m in MESES:
    for t in ("Visa", "Master"):
        r = con.sql(f"""
            SELECT median(("{t}_mconsumototal" - "{t}_mconsumospesos") / "{t}_mconsumosdolares") AS implicito,
                   avg((abs("{t}_mconsumototal" - "{t}_mconsumospesos") < 1)::INT) AS total_igual_pesos,
                   count(*) AS n
            FROM {f(m)} WHERE "{t}_mconsumosdolares" > 1
        """).df().iloc[0]
        filas.append(dict(foto_mes=m, tarjeta=t, tc_implicito=r.implicito,
                          pct_total_igual_pesos=r.total_igual_pesos, n=int(r.n),
                          tc_prom=ind.tc_mayorista_prom.loc[m]))
ident = pd.DataFrame(filas)
ident.round(4).to_csv(os.path.join(SALIDA, "monedas_identidad_tarjeta.csv"), index=False)
print("\nb) (total − pesos) / dólares, clientes con consumos en dólares:")
print(ident.round(3).to_string(index=False))

# c) niveles en 201907
print("\nc) Niveles en 201907 (clientes con valor > 0):")
niv = con.sql("SELECT " + ", ".join(
    f'quantile_cont("{c}", [0.25, 0.5, 0.75]) FILTER ("{c}" > 0) AS "{c}"' for c in COLS)
    + f" FROM {f(201907)}").df().iloc[0]
print(pd.DataFrame(niv.tolist(), index=niv.index, columns=["p25", "p50", "p75"]).round(0).to_string())
print(f"Tipo de cambio 201907: {ind.tc_mayorista_prom.loc[201907]:.2f}")

# plazo fijo: ¿quién tiene cada uno? (si los dólares acompañan a la caja en dólares)
print("\nPlazo fijo en 201907: % de tenedores que también tienen caja de ahorro en dólares > 0")
print(con.sql(f"""
    SELECT 'mplazo_fijo_pesos' AS col, count(*) n, avg((mcaja_ahorro_dolares > 0)::INT) con_caja_usd
    FROM {f(201907)} WHERE mplazo_fijo_pesos > 0
    UNION ALL
    SELECT 'mplazo_fijo_dolares', count(*), avg((mcaja_ahorro_dolares > 0)::INT)
    FROM {f(201907)} WHERE mplazo_fijo_dolares > 0
    UNION ALL
    SELECT 'todos', count(*), avg((mcaja_ahorro_dolares > 0)::INT) FROM {f(201907)}
""").df().round(3).to_string(index=False))
