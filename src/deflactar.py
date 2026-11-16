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


# Brazo 3: cada grupo con su deflactor (clasificación y evidencia en docs/paso10_clasificacion.md, decisión D14).
# Desfase: 1 mes para IPC y RIPTE (se publican a mediados de t+1); 0 para las series del BCRA y la moda de
# comisiones, que ya están disponibles al predecir.
_TARJETA = ("msaldototal", "msaldopesos", "mconsumospesos", "madelantopesos", "mpagado", "mpagospesos",
            "mconsumototal", "mpagominimo")
GRUPOS = {
    # (índice, desfase): columnas
    ("ipc", 1): [  # 1. consumos y movimientos en pesos, 8. préstamos, 10. rentabilidad y márgenes
        "mautoservicio", "mtarjeta_visa_consumo", "mtarjeta_master_consumo", "mcuenta_debitos_automaticos",
        "mttarjeta_visa_debitos_automaticos", "mttarjeta_master_debitos_automaticos", "mpagodeservicios",
        "mpagomiscuentas", "mcajeros_propios_descuentos", "mtarjeta_visa_descuentos", "mtarjeta_master_descuentos",
        "mtransferencias_recibidas", "mtransferencias_emitidas", "mextraccion_autoservicio", "mcheques_depositados",
        "mcheques_emitidos", "mcheques_depositados_rechazados", "mcheques_emitidos_rechazados", "matm", "matm_other",
        *[f"{t}_{c}" for t in ("Visa", "Master") for c in _TARJETA],
        "mprestamos_personales", "mprestamos_prendarios", "mprestamos_hipotecarios",
        "mrentabilidad", "mrentabilidad_annual", "mactivos_margen", "mpasivos_margen"],
    ("ripte", 1): ["mpayroll", "mpayroll2"],  # 2. sueldo
    ("idx_tasa_pf30", 0): [  # 3. saldos en pesos (mplazo_fijo_dolares se comporta como pesos: D14)
        "mcuenta_corriente_adicional", "mcuenta_corriente", "mcaja_ahorro", "mcaja_ahorro_adicional",
        "mcuentas_saldo", "minversion1_pesos", "minversion2", "mplazo_fijo_dolares"],
    ("tc_mayorista_fin", 0): [  # 6. dólares expresados en pesos (mplazo_fijo_pesos se comporta como dólares: D14)
        "mcaja_ahorro_dolares", "minversion1_dolares", "mplazo_fijo_pesos",
        "Visa_msaldodolares", "Master_msaldodolares"],
    ("tc_mayorista_prom", 0): ["mforex_buy", "mforex_sell"],  # 11. compra y venta de dólares
}
COMISIONES = ["mcomisiones", "mcomisiones_mantenimiento", "mcomisiones_otras"]  # 4. moda mensual del mantenimiento
LIMITES = {f"{t}_mlimitecompra": f"{t}_mconsumototal" for t in ("Visa", "Master")}  # 5. se reemplazan por
LIMITES |= {f"{t}_mfinanciacion_limite": f"{t}_msaldototal" for t in ("Visa", "Master")}  # uso / límite
SIN_DEFLACTAR = [f"{t}_{c}" for t in ("Visa", "Master")  # 6b. ya están en USD
                 for c in ("mconsumosdolares", "mpagosdolares", "madelantodolares")]


def moda_comisiones(con, carpeta, meses):
    """Valor más frecuente (> 0) de mcomisiones_mantenimiento por mes, normalizado a BASE = 1.
    Si un mes no tiene moda (columna rota), se repite la del mes anterior."""
    modas, previa = {}, None
    for m in sorted(meses):
        r = con.sql(f"SELECT mode(mcomisiones_mantenimiento) FILTER (mcomisiones_mantenimiento > 0) "
                    f"FROM read_parquet('{carpeta}/{m}.parquet')").fetchone()[0]
        previa = r if r is not None else previa
        modas[m] = previa
    return {m: v / modas[BASE] for m, v in modas.items()}


def brazo_grupo(columnas_monetarias, con, carpeta, meses):
    """Brazo 3: {columna: {foto_mes: divisor}} por grupo, o {límite: columna de uso} para los cocientes."""
    d = {}
    for (serie, desfase), cols in GRUPOS.items():
        d |= divisores(cols, serie, desfase)
    com = moda_comisiones(con, carpeta, meses)
    d |= {c: com for c in COMISIONES}
    d |= LIMITES
    asignadas = set(d) | set(SIN_DEFLACTAR)
    faltan, sobran = set(columnas_monetarias) - asignadas, asignadas - set(columnas_monetarias)
    if faltan or sobran:
        raise ValueError(f"Clasificación incompleta. Sin grupo: {sorted(faltan)}. Inexistentes: {sorted(sobran)}")
    return d
