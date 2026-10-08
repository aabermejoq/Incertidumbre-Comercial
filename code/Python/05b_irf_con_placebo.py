"""Gráfica de las IRF promedio CON el tramo placebo (h = −6..12), a partir de outputs/tables/irf_promedio_mensual_covid.csv.

Para h < 0 la "respuesta" es el nivel en t+h respecto a t−1 (−Σ_{j=h+1..−1} β_j): si el diseño es válido, debe ser cero.
h = −1 vale cero por construcción (es la normalización). En las especificaciones con el rezago propio de la variable
(E1, T1, T2), h = −2 también es casi cero por construcción, porque ese mes es un control.
Bandas simétricas al 68% y 90% alrededor de la estimación (error estándar por permutación); eje centrado en cero.

Uso (desde code/Python):  python 05b_irf_con_placebo.py      Salida: outputs/figures/irf_promedio_mensual_covid_placebo.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RAIZ = Path(__file__).resolve().parents[1].parent
irf = pd.read_csv(RAIZ / "outputs/tables/irf_promedio_mensual_covid.csv")
AZUL, T1, T2, GRID, SUP = "#2a78d6", "#0b0b0b", "#52514e", "#e9e8e4", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": T2,
                     "xtick.color": T2, "ytick.color": T2, "figure.facecolor": SUP, "axes.facecolor": SUP})
NOMBRES = {"produccion": "Producción real", "empleo": "Empleo", "horas": "Horas trabajadas",
           "exportaciones": "Exportaciones (Banxico)", "importaciones_eeuu": "Importaciones de EE.UU. desde México"}
fig, ejes = plt.subplots(5, 2, figsize=(11, 15), sharex=True)
for i, v in enumerate(NOMBRES):
    sub = irf[irf.variable == v].copy()
    sub["inf90"], sub["sup90"] = sub.respuesta - 1.645 * sub.ee, sub.respuesta + 1.645 * sub.ee
    sub["inf68"], sub["sup68"] = sub.respuesta - sub.ee, sub.respuesta + sub.ee
    lim = 1.1 * np.abs(sub[["inf90", "sup90"]].values).max()
    for j, m in enumerate(["completa", "sin pandemia"]):
        a, d = ejes[i, j], sub[sub.muestra == m].sort_values("h")
        a.axvspan(-6.3, -0.5, color="#f0efec", lw=0, zorder=0)
        a.fill_between(d.h, d.inf90, d.sup90, color=AZUL, alpha=0.12, lw=0, label="IC 90%")
        a.fill_between(d.h, d.inf68, d.sup68, color=AZUL, alpha=0.25, lw=0, label="IC 68%")
        a.axhline(0, color=T2, lw=0.9)
        a.axvline(-0.5, color=T2, lw=0.8, ls=(0, (3, 3)))
        a.plot(d.h, d.respuesta, color=AZUL, lw=2)
        a.set_ylim(-lim, lim); a.set_xlim(-6.3, 12)
        a.grid(axis="y", color=GRID, lw=0.8); a.set_axisbelow(True)
        for s_ in ("top", "right", "left"): a.spines[s_].set_visible(False)
        a.tick_params(length=0)
        a.set_title(f"{NOMBRES[v]} · {m} ({d.especificacion.iloc[0]})", loc="left", color=T1, fontsize=10, fontweight="bold")
        if j == 0: a.set_ylabel("% respecto a t−1")
        a.set_xticks([-6, -4, -2, 0, 2, 4, 6, 8, 10, 12])
        if i == 0:
            a.text(-3.4, lim * 0.85, "placebo", ha="center", color=T2, fontsize=8.5)
ejes[0, 0].legend(loc="lower right", frameon=False, fontsize=8)
for a in ejes[-1]: a.set_xlabel("meses respecto al choque (h)")
fig.text(0.01, 0.995, "Respuesta a una sorpresa del TPU de 1 desv. est., con placebo (promedio de las ramas)", fontsize=13, fontweight="bold", color=T1, va="top")
fig.text(0.01, 0.982, "Nivel respecto al mes previo al choque (t−1). Zona gris: meses antes del choque, donde la respuesta debe ser cero.\n"
         "Bandas: intervalos de confianza al 68% y 90% (error estándar por permutación). h = −1 es cero por construcción.", fontsize=8.5, color=T2, va="top")
fig.text(0.01, 0.003, "Variaciones mensuales; controles: IP de EE.UU., tipo de cambio, VIX, arancel de la rama, índice EMV de enfermedades infecciosas\n"
         "y dicótomas abr-jun 2020; especificación elegida por placebo y BIC. Choque: sorpresa del TPU con control de COVID.", fontsize=8, color=T2)
plt.tight_layout(rect=(0, 0.02, 1, 0.968))
fig.savefig(RAIZ / "outputs/figures/irf_promedio_mensual_covid_placebo.png", dpi=150)
print("Guardado: outputs/figures/irf_promedio_mensual_covid_placebo.png")
pre = irf[irf.h <= -2].assign(fuera90=lambda d: (d.respuesta - 1.645 * d.ee > 0) | (d.respuesta + 1.645 * d.ee < 0))
print(pre[pre.fuera90][["variable", "muestra", "h", "respuesta", "ee", "p"]].round(2).to_string(index=False))
