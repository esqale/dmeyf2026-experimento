"""Figuras de docs/investigacion.md (Resultados).

Uso (desde la raíz del repo): python src/13_figuras.py
Necesita reportes/<brazo>/semillas.csv, reportes/{ranking,delta_log}/curva_por_n.csv y reportes/adversarial/univariada.csv.
Salidas en docs/figuras/: diferencias_vs_baseline.png, curva_por_n.png, ruido_semillas.png,
comparacion_principal.png y adversarial_columnas.png
"""
import os

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SALIDA = "docs/figuras"
# (etiqueta, brazo, referencia, familia)
FILAS = [
    ("Todo con IPC (mes anterior)", "ipc_d1", "baseline", 2),
    ("Todo con IPC (mismo mes)", "ipc_d0", "baseline", 2),
    ("Por grupo", "grupo", "baseline", 2),
    ("IPC, Optuna propia", "ipc_d1_opt", "baseline", 2),
    ("Por grupo, Optuna propia", "grupo_opt", "baseline", 2),
    ("IPC + foto_mes", "ipc_d1_mes", "baseline", 2),
    ("IPC + foto_mes, Optuna propia", "ipc_d1_mes_opt", "baseline", 2),
    ("Por grupo, saldos con IPC", "grupo_saldos_ipc", "baseline", 2),
    ("Por grupo + foto_mes", "grupo_mes", "baseline", 2),
    ("Mediana del mes", "mediana", "baseline", 2),
    ("Ranking sin cero fijo (G0)", "ranking_sin_cero", "baseline", 4),
    ("Ranking después de deltas (G2)", "ranking_post", "baseline", 4),
    ("Pesos + ranking (M)", "nominal_ranking", "baseline", 4),
    ("Ranking por mes (G)", "ranking", "baseline", 4),
    ("Deltas relativos (H)", "delta_log", "baseline", 4),
    ("Deltas relativos (H), Optuna propia", "delta_log_opt", "baseline", 4),
    ("Deltas relativos (H), test 201909", "delta_log_t201909", "baseline_t201909", 4),
]
COLOR = {2: "#b23a2e", 4: "#0f6e78"}


def dif(brazo, ref, metrica):
    a = pd.read_csv(f"reportes/{brazo}/semillas.csv").set_index("semilla")[metrica]
    b = pd.read_csv(f"reportes/{ref}/semillas.csv").set_index("semilla")[metrica]
    d = (a - b).dropna() / 1e6
    m, e = d.mean(), stats.t.ppf(0.975, len(d) - 1) * d.std() / np.sqrt(len(d))
    return m, e


def diferencias():
    fig, ejes = plt.subplots(1, 2, figsize=(11, 7), sharey=True)
    y = np.arange(len(FILAS))[::-1]
    for ax, (metrica, titulo) in zip(ejes, [("ganancia_n_fijo", "Ganancia con N = 5.000"),
                                            ("ganancia_zona_plana", "Ganancia en la zona plana (3.000–6.500)")]):
        for yi, (_, brazo, ref, fam) in zip(y, FILAS):
            m, e = dif(brazo, ref, metrica)
            ax.errorbar(m, yi, xerr=e, fmt="o", color=COLOR[fam], capsize=3)
        ax.axvline(0, color="#5a6b76", lw=1)
        ax.set_title(titulo, fontsize=11)
        ax.set_xlabel("Diferencia contra el baseline (millones)", fontsize=9)
        ax.grid(axis="x", alpha=.3)
    ejes[0].set_yticks(y, [f[0] for f in FILAS], fontsize=9)
    fig.legend(handles=[plt.Line2D([], [], marker="o", ls="", color=COLOR[2], label="Familia 2: dividir por un índice"),
                        plt.Line2D([], [], marker="o", ls="", color=COLOR[4], label="Familia 4: corregir sin dividir")],
               loc="lower center", ncol=2, frameon=False)
    fig.suptitle("Media de las 20 diferencias pareadas por semilla, con su intervalo de confianza del 95%. "
                 "Test en 201910, salvo la última fila (201909, contra el baseline de 201909).", fontsize=9, y=.995)
    fig.tight_layout(rect=(0, .04, 1, .97))
    fig.savefig(f"{SALIDA}/diferencias_vs_baseline.png", dpi=150)


def curva():
    g = pd.read_csv("reportes/ranking/curva_por_n.csv")
    g = g[(g.referencia == "baseline") & (g.brazo == "ranking")]
    h = pd.read_csv("reportes/delta_log/curva_por_n.csv")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(g.envios, g.ref_media, color="#5a6b76", marker=".", label="Baseline (sin deflactar)")
    ax.plot(g.envios, g.brazo_media, color="#c98a1b", marker=".", label="Ranking por mes (G)")
    ax.plot(h.envios, h.brazo_media, color="#0f6e78", marker=".", label="Deltas relativos (H)")
    ax.axvspan(3000, 6500, color="#0f6e78", alpha=.06, label="Zona plana")
    ax.axvline(5000, color="#5a6b76", ls="--", lw=1)
    ax.set_xlabel("Clientes contactados (N)")
    ax.set_ylabel("Ganancia en 201910 (millones, media de 20 semillas)")
    ax.grid(alpha=.3)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(f"{SALIDA}/curva_por_n.png", dpi=150)


def ruido():
    b = pd.read_csv("reportes/baseline/semillas.csv")
    fig, ejes = plt.subplots(1, 2, figsize=(11, 3.6), sharey=False)
    for ax, (metrica, titulo) in zip(ejes, [("ganancia_n_fijo", "Ganancia con N = 5.000"),
                                            ("ganancia_zona_plana", "Ganancia en la zona plana (3.000–6.500)")]):
        v = b[metrica] / 1e6
        m, s = v.mean(), v.std()
        ax.axhspan(m - s, m + s, color="#b23a2e", alpha=.1, label="±1 desvío")
        ax.axhline(m, color="#b23a2e", lw=1.5, label=f"media {m:.1f} M")
        ax.plot(range(1, len(v) + 1), v, "o", color="#b23a2e")
        ax.set_title(f"{titulo} · desvío {s:.1f} M", fontsize=11)
        ax.set_xlabel("Semilla", fontsize=9)
        ax.set_xticks(range(1, len(v) + 1, 2))
        ax.grid(axis="y", alpha=.3)
    ejes[0].set_ylabel("Millones, test 201910")
    fig.suptitle("Baseline sin deflactar con 20 semillas distintas. Línea: media; banda: ±1 desvío.", fontsize=10)
    fig.tight_layout()
    fig.savefig(f"{SALIDA}/ruido_semillas.png", dpi=150)


def comparacion_principal():
    brazos = [("Sin deflactar", "baseline"), ("Todo con IPC", "ipc_d1"), ("Por grupo", "grupo")]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    y = np.arange(len(brazos))[::-1]
    for k, (metrica, etiqueta, color) in enumerate([("ganancia_n_fijo", "N = 5.000", "#b23a2e"),
                                                     ("ganancia_zona_plana", "Zona plana", "#2b2f38")]):
        medias = [pd.read_csv(f"reportes/{br}/semillas.csv")[metrica].mean() / 1e6 for _, br in brazos]
        desvios = [pd.read_csv(f"reportes/{br}/semillas.csv")[metrica].std() / 1e6 for _, br in brazos]
        ax.barh(y + (.2 if k == 0 else -.2), medias, height=.38, xerr=desvios, color=color, alpha=.85,
                label=etiqueta, capsize=3)
        for yi, m in zip(y, medias):
            ax.text(272.4, yi + (.2 if k == 0 else -.2), f"{m:.1f}", va="center", fontsize=8, color="white",
                    fontweight="bold")
    ax.set_yticks(y, [b[0] for b in brazos])
    ax.set_xlim(272, 292)
    ax.set_xlabel("Ganancia media en 201910 (millones, 20 semillas; barra = ±1 desvío)", fontsize=9)
    ax.grid(axis="x", alpha=.3)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_title("Comparación principal, con los hiperparámetros del baseline", fontsize=11)
    fig.tight_layout()
    fig.savefig(f"{SALIDA}/comparacion_principal.png", dpi=150)


def adversarial():
    u = pd.read_csv("reportes/adversarial/univariada.csv")
    u = u[(u.par == "201903-201910") & (u.columnas == "mes")]
    t = u.pivot_table(index="columna", columns="brazo", values="drift").sort_values("fe_base", ascending=False)
    t = t.head(16)[::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    y = np.arange(len(t))
    for k, (brazo, etiqueta, color) in enumerate([("fe_base", "Sin deflactar", "#2b2f38"),
                                                   ("fe_ipc_d1", "Todo con IPC", "#b23a2e"),
                                                   ("fe_grupo", "Por grupo", "#c98a1b")]):
        ax.barh(y + (1 - k) * .27, t[brazo], height=.26, color=color, label=etiqueta)
    ax.set_yticks(y, t.index, fontsize=8)
    ax.set_xlabel("Cuánto distingue 201903 de 201910 la columna sola (|AUC − 0,5|; 0 = nada, 0,5 = perfecto)",
                  fontsize=9)
    ax.grid(axis="x", alpha=.3)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_title("Las 16 columnas monetarias que más cambian entre 201903 y 201910", fontsize=11)
    fig.tight_layout()
    fig.savefig(f"{SALIDA}/adversarial_columnas.png", dpi=150)


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    diferencias()
    curva()
    ruido()
    comparacion_principal()
    adversarial()
    print("ok")
