"""Paso 8: tabla mensual de índices externos para deflactar (201811–202110).

Uso:
    python src/05_indices.py [--bajar]

--bajar vuelve a descargar las series a datos_externos/crudo/. Sin esa opción usa lo que ya está bajado
(así la tabla se reproduce aunque las APIs cambien: la v3 del BCRA ya fue dada de baja).

Fuentes
    datos.gob.ar (API de series)
        148.3_INIVELNAL_DICI_M_26  IPC nacional, nivel general, base dic-2016 = 100 (INDEC)
        158.1_REPTE_0_0_5          RIPTE, en pesos (Secretaría de Seguridad Social)
    BCRA, API de estadísticas monetarias v4.0 (idVariable)
        5     tipo de cambio mayorista de referencia, Com. A 3500 (diaria)
        7     BADLAR bancos privados, % TNA (diaria) — solo referencia
        12    tasa de depósitos a 30 días, % TNA (diaria)
        1190  tasa de plazo fijo en pesos de personas humanas, % TNA (diaria)
        14    tasa de préstamos personales, % TNA (diaria)
        1215  tasa de financiaciones con tarjetas de crédito, % TNA (mensual; el BCRA la publica solo hasta 202004)
        30    CER, base 2/2/2002 = 1 (diaria)
        31    UVA, en pesos (diaria)

Salida: datos_externos/indices_mensuales.csv, una fila por foto_mes:
    nivel del mes para IPC y RIPTE; promedio y último dato del mes para las series diarias;
    índices acumulados de tasas (base 201811 = 1): idx_t = idx_{t-1} * (1 + TNA_t/100 * días_del_mes/365).
"""
import argparse
import calendar
import json
import os
import urllib.request

import pandas as pd

CRUDO = "datos_externos/crudo"
SALIDA = "datos_externos/indices_mensuales.csv"
DESDE, HASTA = "2018-11-01", "2021-10-31"
DATOSGOB = {"ipc": "148.3_INIVELNAL_DICI_M_26", "ripte": "158.1_REPTE_0_0_5"}
BCRA = {5: "tc_mayorista", 7: "badlar", 12: "tasa_pf30", 1190: "tasa_pf_personas",
        14: "tasa_personales", 1215: "tasa_tarjetas", 30: "cer", 31: "uva"}
TASAS = ["tasa_pf30", "tasa_pf_personas", "tasa_personales", "tasa_tarjetas", "badlar"]
TRAMOS = [("2018-11-01", "2019-10-31"), ("2019-11-01", "2020-10-31"), ("2020-11-01", "2021-10-31")]


def bajar(url, destino):
    pedido = urllib.request.Request(url, headers={"User-Agent": "dmeyf2026-experimento/1.0"})  # sin esto, 403
    with urllib.request.urlopen(pedido, timeout=60) as r, open(destino, "wb") as f:
        f.write(r.read())


def descargar():
    os.makedirs(CRUDO, exist_ok=True)
    ids = ",".join(DATOSGOB.values())
    bajar(f"https://apis.datos.gob.ar/series/api/series/?ids={ids}&start_date={DESDE}&end_date={HASTA}"
          "&format=csv&limit=1000", f"{CRUDO}/datosgob_ipc_ripte.csv")
    for i in BCRA:
        for d, h in TRAMOS:  # la API devuelve como máximo 1000 filas por pedido
            bajar(f"https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/{i}?desde={d}&hasta={h}&limit=1000",
                  f"{CRUDO}/bcra_{i}_{d}.json")


def leer_bcra(i):
    filas = []
    for d, _ in TRAMOS:
        res = json.load(open(f"{CRUDO}/bcra_{i}_{d}.json", encoding="utf-8"))["results"]
        filas += res[0]["detalle"] if res else []
    s = pd.DataFrame(filas)
    s["fecha"] = pd.to_datetime(s["fecha"])
    return s.drop_duplicates("fecha").sort_values("fecha")


def main(a):
    if a.bajar:
        descargar()
    g = pd.read_csv(f"{CRUDO}/datosgob_ipc_ripte.csv", parse_dates=["indice_tiempo"])
    g = g.rename(columns={"ipc_nivel_general_nacional": "ipc"})
    tabla = pd.DataFrame({"foto_mes": g.indice_tiempo.dt.year * 100 + g.indice_tiempo.dt.month,
                          "ipc": g.ipc, "ripte": g.ripte}).set_index("foto_mes")

    for i, nombre in BCRA.items():
        s = leer_bcra(i)
        s["foto_mes"] = s.fecha.dt.year * 100 + s.fecha.dt.month
        por_mes = s.groupby("foto_mes")["valor"]
        if nombre in TASAS:
            tabla[nombre] = por_mes.mean()  # tasa promedio del mes
        else:
            tabla[f"{nombre}_prom"] = por_mes.mean()   # para flujos del mes
            tabla[f"{nombre}_fin"] = por_mes.last()    # para saldos a fin de mes

    tabla = tabla.sort_index()
    dias = pd.Series([calendar.monthrange(m // 100, m % 100)[1] for m in tabla.index], index=tabla.index)
    for t in TASAS:
        factor = (1 + tabla[t] / 100 * dias / 365).where(tabla[t].notna())
        tabla[f"idx_{t}"] = factor.fillna(1).cumprod() / factor.fillna(1).iloc[0]
        tabla.loc[tabla[t].isna(), f"idx_{t}"] = None
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    tabla.reset_index().to_csv(SALIDA, index=False, float_format="%.6f")
    pd.set_option("display.width", 250)
    print(tabla.loc[201812:202001].round(3).to_string())
    print(f"\nFaltantes por columna (201811–202110):\n{tabla.isna().sum()[tabla.isna().sum() > 0].to_string()}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--bajar", action="store_true")
    main(p.parse_args())
