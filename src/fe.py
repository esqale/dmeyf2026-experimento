"""Feature engineering y clase: una sola definición para todos los brazos del experimento.

features_mes(): para la foto t devuelve las columnas crudas + lag1, lag2, delta1, delta2 de cada variable.
    El lag k es el valor del MISMO cliente en el mes t-k (por calendario, no "la fila anterior"):
    si el cliente no estaba en t-k, el lag queda NULL.
    Opcional `deflactor` = {columna: {foto_mes: divisor}}: cada valor se divide por el divisor de SU mes
    (el valor de t por el de t, el lag1 por el de t-1, ...) ANTES de calcular lags y deltas.
    Si en vez del dict hay un nombre de columna ({columna: "otra"}), la columna se reemplaza por el cociente
    otra / columna del mismo cliente y mes (límites de tarjeta en el brazo "por grupo"; 0 en el divisor da NULL).
    Sin deflactor, el resultado es exactamente el del baseline.
clase_ternaria(): CONTINUA / BAJA+1 / BAJA+2 desde la presencia del cliente en t+1 y t+2. Solo entrenamiento.

Las dos funciones reciben la carpeta con un <yyyymm>.parquet por mes y trabajan sobre duckdb,
leyendo solo los meses que necesitan.
"""
import os

NO_FEATURES = ("numero_de_cliente", "foto_mes")
LAGS = (1, 2)


def _mes_mas(mes, k):
    """Suma k meses a un yyyymm (k puede ser negativo)."""
    a, m = divmod(mes // 100 * 12 + mes % 100 - 1 + k, 12)
    return a * 100 + m + 1


def _archivo(carpeta, mes):
    return os.path.join(carpeta, f"{mes}.parquet").replace("\\", "/")


def es_monetaria(columna):
    """Columnas en pesos (o dólares): prefijo m, Visa_m, Master_m. Son 73 en este dataset."""
    return columna.startswith(("m", "Visa_m", "Master_m"))


def columnas_crudas(con, carpeta, mes):
    return [c for c in con.sql(f"SELECT * FROM read_parquet('{_archivo(carpeta, mes)}') LIMIT 0").columns
            if c not in NO_FEATURES]


def features_mes(con, carpeta, mes, deflactor=None):
    """Relación duckdb con numero_de_cliente, foto_mes y las features de la foto `mes`."""
    cols = columnas_crudas(con, carpeta, mes)
    deflactor = deflactor or {}

    def v(alias, c, m):  # valor de la columna c en el mes m, deflactado si corresponde
        if c not in deflactor:
            return f'{alias}."{c}"'
        if isinstance(deflactor[c], str):
            return f'({alias}."{deflactor[c]}" / NULLIF({alias}."{c}", 0))'
        return f'({alias}."{c}" / {float(deflactor[c][m])!r})'

    sel = ["t.numero_de_cliente", "t.foto_mes"]
    sel += [f'CAST({v("t", c, mes)} AS FLOAT) AS "{c}"' for c in cols]
    joins = []
    for k in LAGS:
        mes_k = _mes_mas(mes, -k)
        previo = _archivo(carpeta, mes_k)
        if os.path.exists(previo):
            joins.append(f"LEFT JOIN read_parquet('{previo}') l{k} USING (numero_de_cliente)")
            sel += [f'CAST({v(f"l{k}", c, mes_k)} AS FLOAT) AS "{c}_lag{k}"' for c in cols]
            sel += [f'CAST({v("t", c, mes)} - {v(f"l{k}", c, mes_k)} AS FLOAT) AS "{c}_delta{k}"' for c in cols]
        else:  # sin historia: mismas columnas, todo NULL
            sel += [f'CAST(NULL AS FLOAT) AS "{c}_lag{k}"' for c in cols]
            sel += [f'CAST(NULL AS FLOAT) AS "{c}_delta{k}"' for c in cols]
    return con.sql(f"""
        SELECT {', '.join(sel)}
        FROM read_parquet('{_archivo(carpeta, mes)}') t
        {' '.join(joins)}
    """)


def clase_ternaria(con, carpeta, mes):
    """Relación duckdb (numero_de_cliente, clase_ternaria) de la foto `mes`. Necesita t+1 y t+2."""
    f0, f1, f2 = (_archivo(carpeta, _mes_mas(mes, k)) for k in (0, 1, 2))
    for f in (f1, f2):
        if not os.path.exists(f):
            raise FileNotFoundError(f"La clase de {mes} necesita {f}")
    return con.sql(f"""
        SELECT t.numero_de_cliente,
               CASE WHEN p1.numero_de_cliente IS NULL THEN 'BAJA+1'
                    WHEN p2.numero_de_cliente IS NULL THEN 'BAJA+2'
                    ELSE 'CONTINUA' END AS clase_ternaria
        FROM (SELECT numero_de_cliente FROM read_parquet('{f0}')) t
        LEFT JOIN (SELECT numero_de_cliente FROM read_parquet('{f1}')) p1 USING (numero_de_cliente)
        LEFT JOIN (SELECT numero_de_cliente FROM read_parquet('{f2}')) p2 USING (numero_de_cliente)
    """)
