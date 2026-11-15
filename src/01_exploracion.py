"""Paso 3: exploración básica y target, sobre historia/mensual/*.parquet (duckdb, sin cargar todo).

Uso:
    python src/01_exploracion.py [carpeta_historia] [carpeta_salida]

Genera en reportes/paso3/:
    a_meses.csv          filas, clientes, duplicados, altas y bajas por mes (los 32 meses, descriptivo)
    b_clase.csv          CONTINUA / BAJA+1 / BAJA+2 por mes, 201901–201910, desde la presencia en t+1 y t+2
    b_reapariciones.csv  clientes que "se dieron de baja" y vuelven a aparecer dentro de 2019
    c_vacias_2019.csv    % de ceros y de nulos por columna y mes, 201901–201912
    c_sospechosas.csv    columnas casi vacías en 201905 o 201910 que no lo están en los meses vecinos
    d_cliente_48000000.csv  trayectoria del cliente 48000000
"""
import os
import sys

import duckdb
import pandas as pd

HISTORIA = sys.argv[1] if len(sys.argv) > 1 else "historia/mensual"
SALIDA = sys.argv[2] if len(sys.argv) > 2 else "reportes/paso3"
UMBRAL_VACIA = 0.99  # proporción de ceros + nulos para decir "casi vacía"

os.makedirs(SALIDA, exist_ok=True)
sys.stdout.reconfigure(encoding="utf-8")
con = duckdb.connect()
con.execute("SET memory_limit='6GB'")
con.execute(f"CREATE VIEW crudo AS SELECT * FROM read_parquet('{HISTORIA}/??????.parquet')")
# índice de mes consecutivo: permite sumar 1 o 2 meses sin pelear con el cambio de año
con.execute("""
    CREATE TABLE presencia AS
    SELECT DISTINCT numero_de_cliente, foto_mes,
           (foto_mes // 100) * 12 + foto_mes % 100 AS periodo
    FROM crudo
""")


def guardar(df, nombre):
    df.to_csv(os.path.join(SALIDA, nombre), index=False)
    return df


# ---------------------------------------------------------------- a) filas, clientes, altas y bajas
a = guardar(con.sql("""
    WITH filas AS (
        SELECT foto_mes, count(*) AS filas, count(DISTINCT numero_de_cliente) AS clientes,
               count(*) - count(numero_de_cliente) AS id_nulos
        FROM crudo GROUP BY foto_mes
    ),
    altas AS (   -- está en t y no estaba en t-1
        SELECT p.foto_mes, count(*) AS altas
        FROM presencia p LEFT JOIN presencia q
          ON q.numero_de_cliente = p.numero_de_cliente AND q.periodo = p.periodo - 1
        WHERE q.numero_de_cliente IS NULL GROUP BY p.foto_mes
    ),
    bajas AS (   -- estaba en t-1 y no está en t (se imputa al mes t)
        SELECT p.periodo + 1 AS periodo, count(*) AS bajas
        FROM presencia p LEFT JOIN presencia q
          ON q.numero_de_cliente = p.numero_de_cliente AND q.periodo = p.periodo + 1
        WHERE q.numero_de_cliente IS NULL GROUP BY 1
    )
    SELECT f.foto_mes, f.filas, f.clientes, f.filas - f.clientes AS duplicados, f.id_nulos,
           a.altas, b.bajas
    FROM filas f
    LEFT JOIN altas a USING (foto_mes)
    LEFT JOIN bajas b ON b.periodo = (f.foto_mes // 100) * 12 + f.foto_mes % 100
    ORDER BY f.foto_mes
""").df(), "a_meses.csv")
a.loc[a.index[0], "altas"] = None  # el primer mes no tiene mes anterior
print("\n=== a) Filas, clientes, altas y bajas por mes ===")
print(a.to_string(index=False))

# ---------------------------------------------------------------- b) clase ternaria (solo 2019)
con.execute("""
    CREATE TABLE clase AS
    SELECT p.numero_de_cliente, p.foto_mes,
           CASE WHEN p1.numero_de_cliente IS NULL THEN 'BAJA+1'
                WHEN p2.numero_de_cliente IS NULL THEN 'BAJA+2'
                ELSE 'CONTINUA' END AS clase_ternaria
    FROM presencia p
    LEFT JOIN presencia p1 ON p1.numero_de_cliente = p.numero_de_cliente AND p1.periodo = p.periodo + 1
    LEFT JOIN presencia p2 ON p2.numero_de_cliente = p.numero_de_cliente AND p2.periodo = p.periodo + 2
    WHERE p.foto_mes BETWEEN 201901 AND 201910
""")
b = guardar(con.sql("""
    SELECT foto_mes, count(*) AS clientes,
           count(*) FILTER (clase_ternaria = 'CONTINUA') AS continua,
           count(*) FILTER (clase_ternaria = 'BAJA+1') AS baja1,
           count(*) FILTER (clase_ternaria = 'BAJA+2') AS baja2,
           round(100 * count(*) FILTER (clase_ternaria = 'BAJA+2') / count(*), 3) AS pct_baja2,
           round(100 * count(*) FILTER (clase_ternaria <> 'CONTINUA') / count(*), 3) AS pct_binaria
    FROM clase GROUP BY foto_mes ORDER BY foto_mes
""").df(), "b_clase.csv")
print("\n=== b) Clase ternaria por mes (presencia en t+1 y t+2) ===")
print(b.to_string(index=False))

# ¿la baja es definitiva? clientes con BAJA+1/BAJA+2 en t que vuelven a aparecer después, dentro de 2019
r = guardar(con.sql("""
    SELECT c.foto_mes, c.clase_ternaria, count(DISTINCT c.numero_de_cliente) AS bajas,
           count(DISTINCT v.numero_de_cliente) AS vuelven_en_2019,
           round(100 * count(DISTINCT v.numero_de_cliente) / count(DISTINCT c.numero_de_cliente), 2) AS pct_vuelven
    FROM clase c
    LEFT JOIN presencia v
      ON v.numero_de_cliente = c.numero_de_cliente AND v.foto_mes <= 201912
     AND v.periodo > (c.foto_mes // 100) * 12 + c.foto_mes % 100
                     + CASE c.clase_ternaria WHEN 'BAJA+1' THEN 1 ELSE 2 END
    WHERE c.clase_ternaria <> 'CONTINUA'
    GROUP BY 1, 2 ORDER BY 1, 2
""").df(), "b_reapariciones.csv")
print("\n=== b) Bajas que vuelven a aparecer más adelante (solo hasta 201912) ===")
print(r.to_string(index=False))

# ---------------------------------------------------------------- c) columnas casi vacías, 2019
columnas = [c for c in con.sql("SELECT * FROM crudo LIMIT 0").columns
            if c not in ("numero_de_cliente", "foto_mes")]
partes = []
for c in columnas:
    partes.append(f'avg(CASE WHEN "{c}" = 0 THEN 1.0 ELSE 0.0 END) AS "z|{c}"')
    partes.append(f'1 - count("{c}") / count(*) AS "n|{c}"')
ancho = con.sql(f"""
    SELECT foto_mes, {', '.join(partes)}
    FROM crudo WHERE foto_mes BETWEEN 201901 AND 201912 GROUP BY foto_mes ORDER BY foto_mes
""").df()
largo = ancho.melt(id_vars="foto_mes")
largo[["medida", "columna"]] = largo["variable"].str.split("|", n=1, expand=True)
vac = largo.pivot_table(index=["columna", "foto_mes"], columns="medida", values="value").reset_index()
vac = vac.rename(columns={"z": "pct_cero", "n": "pct_nulo"})
vac["pct_vacia"] = vac["pct_cero"] + vac["pct_nulo"]
guardar(vac, "c_vacias_2019.csv")

pv = vac.pivot(index="columna", columns="foto_mes", values="pct_vacia")
print(f"\n=== c) Columnas con ceros + nulos > {UMBRAL_VACIA:.0%}, por mes (2019) ===")
print((pv > UMBRAL_VACIA).sum().to_string())

sosp = []
for mes, vecinos in ((201905, (201904, 201906)), (201910, (201909, 201911))):
    for col in pv.index[pv[mes] > UMBRAL_VACIA]:
        v = pv.loc[col, list(vecinos)]
        if v.max() <= UMBRAL_VACIA:  # solo las que se "vacían" en ese mes
            fila = vac[(vac.columna == col) & (vac.foto_mes == mes)].iloc[0]
            sosp.append(dict(mes=mes, columna=col,
                             pct_cero=round(fila.pct_cero, 4), pct_nulo=round(fila.pct_nulo, 4),
                             vacia_ant=round(v.iloc[0], 4), vacia_sig=round(v.iloc[1], 4)))
sosp = guardar(pd.DataFrame(sosp), "c_sospechosas.csv")
print("\n=== c) Casi vacías en el mes pero no en los vecinos ===")
print(sosp.to_string(index=False))

# ---------------------------------------------------------------- d) cliente 48000000
d = guardar(con.sql("""
    SELECT foto_mes, cliente_edad, cliente_antiguedad, cproductos, ctrx_quarter, mrentabilidad,
           mcuentas_saldo, active_quarter
    FROM crudo WHERE numero_de_cliente = 48000000 ORDER BY foto_mes
""").df(), "d_cliente_48000000.csv")
print("\n=== d) Cliente 48000000 ===")
print(d.to_string(index=False))
vecinos = con.sql("""
    SELECT count(DISTINCT numero_de_cliente) AS ids_cercanos
    FROM presencia WHERE numero_de_cliente BETWEEN 47999000 AND 48001000 AND numero_de_cliente <> 48000000
""").fetchone()[0]
print(f"Otros ids entre 47.999.000 y 48.001.000: {vecinos}")
