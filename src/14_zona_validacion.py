"""D22: zona plana definida con la curva del baseline en 201908 (validación) y no en 201910 (test).

1. Entrena el baseline con 201903-06 y sus hiperparámetros, con las mismas 20 semillas de 04_semillas, y predice
   201908. Reanudable: guarda la curva de cada semilla.
2. Zona = tramo continuo de cortes de a 500 alrededor del máximo de la curva promedio con ganancia >= 95% del máximo.
3. Recalcula la ganancia en esa zona para cada brazo con sus probabilidades guardadas y la compara, pareada por
   semilla, contra su baseline (Wilcoxon), junto a la zona 3.000-6.500.

Uso (desde la raíz del repo): python src/14_zona_validacion.py [brazo ...]
Salidas en reportes/zona_validacion/: curvas_201908.csv, zona.json, comparacion.csv
"""
import json
import os
import sys

import lightgbm as lgb
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(__file__))
from comun import ENTRENA, FIJOS, PASO_ENVIOS, VALIDA, ZONA_PLANA, cargar, curva_ganancia  # noqa: E402

SALIDA = "reportes/zona_validacion"
UMBRAL = 0.95
CORTES = np.arange(PASO_ENVIOS, 20001, PASO_ENVIOS)
# brazo -> (referencia, mes de test)
BRAZOS = {b: ("baseline", 201910) for b in [
    "ipc_d1", "ipc_d0", "grupo", "ipc_d1_opt", "grupo_opt", "ipc_d1_mes", "ipc_d1_mes_opt", "grupo_saldos_ipc",
    "mediana", "grupo_mes", "ranking", "ranking_post", "ranking_sin_cero", "nominal_ranking", "delta_log",
    "delta_log_opt"]}
BRAZOS["delta_log_t201909"] = ("baseline_t201909", 201909)


def curvas_201908():
    archivo = os.path.join(SALIDA, "curvas_201908.csv")
    hechas = pd.read_csv(archivo) if os.path.exists(archivo) else pd.DataFrame(columns=["envios"])
    base = json.load(open("reportes/baseline/resultado.json", encoding="utf-8"))
    semillas = np.random.default_rng(102191).integers(1, 2**31 - 1, size=20).tolist()
    faltan = [s for s in semillas if f"s{s}" not in hechas.columns]
    if faltan:
        X, y, _ = cargar("datasets/fe_base", ENTRENA)
        d = lgb.Dataset(X, y, params={"feature_pre_filter": False}, free_raw_data=False).construct()
        Xva, _, b2va = cargar("datasets/fe_base", [VALIDA])
        if hechas.empty:
            hechas = pd.DataFrame({"envios": CORTES})
        for s in faltan:
            m = lgb.train(dict(FIJOS, **base["params"], seed=s), d, num_boost_round=base["iteraciones"])
            hechas[f"s{s}"] = curva_ganancia(m.predict(Xva), b2va)[CORTES - 1]
            hechas.to_csv(archivo, index=False)
            print(f"201908 · semilla {s} · máximo {hechas[f's{s}'].max() / 1e6:,.1f} M", flush=True)
    return hechas


def zona(curvas):
    media = curvas.drop(columns="envios").mean(axis=1).to_numpy()
    i = int(np.argmax(media))
    ok = media >= UMBRAL * media[i]
    a = b = i
    while a > 0 and ok[a - 1]:
        a -= 1
    while b < len(ok) - 1 and ok[b + 1]:
        b += 1
    return int(curvas.envios[a]), int(curvas.envios[b]), int(curvas.envios[i]), float(media[i])


def ganancia_zona(nombre, mes, desde, hasta):
    clase = pd.read_parquet(f"datasets/fe_base/{mes}.parquet", columns=["numero_de_cliente", "clase_ternaria"])
    b2 = dict(zip(clase.numero_de_cliente, clase.clase_ternaria == "BAJA+2"))
    p = pd.read_parquet(f"reportes/{nombre}/probs_{mes}.parquet")
    y = p.numero_de_cliente.map(b2).to_numpy(bool)
    cortes = np.arange(desde, hasta + 1, PASO_ENVIOS)
    return pd.Series({int(c[1:]): curva_ganancia(p[c].to_numpy(), y)[cortes - 1].mean() / 1e6
                      for c in p.columns if c.startswith("s")})


def veredicto(d, p):
    return "empata" if p >= 0.05 else ("mejora" if d > 0 else "empeora")


def main(brazos):
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(SALIDA, exist_ok=True)
    desde, hasta, n_max, g_max = zona(curvas_201908())
    json.dump(dict(desde=desde, hasta=hasta, umbral=UMBRAL, max_envios=n_max, max_ganancia_media=g_max),
              open(os.path.join(SALIDA, "zona.json"), "w"), indent=2)
    print(f"Zona de validación: {desde:,}–{hasta:,} envíos (máximo de 201908 en {n_max:,}, {g_max / 1e6:,.1f} M)")
    filas = []
    for b in brazos:
        ref, mes = BRAZOS[b]
        if not os.path.exists(f"reportes/{b}/probs_{mes}.parquet"):
            print(f"{b}: sin probabilidades, se saltea")
            continue
        fila = dict(brazo=b, referencia=ref, mes_test=mes)
        for etiqueta, (z0, z1) in [("vieja", ZONA_PLANA), ("validacion", (desde, hasta))]:
            g, r = ganancia_zona(b, mes, z0, z1), ganancia_zona(ref, mes, z0, z1)
            d = (g - r).dropna()
            p = stats.wilcoxon(d).pvalue
            fila |= {f"dif_{etiqueta}": d.mean(), f"gana_{etiqueta}": int((d > 0).sum()), f"p_{etiqueta}": p,
                     f"veredicto_{etiqueta}": veredicto(d.mean(), p)}
        fila["cambia"] = fila["veredicto_vieja"] != fila["veredicto_validacion"]
        filas.append(fila)
    t = pd.DataFrame(filas)
    t.to_csv(os.path.join(SALIDA, "comparacion.csv"), index=False)
    pd.set_option("display.width", 220)
    print(t.round(4).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1:] or list(BRAZOS))
