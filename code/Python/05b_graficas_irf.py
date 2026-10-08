"""Gráficas de las IRF promedio de las ramas, a partir de outputs/tables/irf_promedio_mensual_covid.csv (ver 05_irf_promedio.py).

Dos figuras (5 variables × 2 muestras):
  - irf_promedio_mensual_covid.png:          h = 0..12.
  - irf_promedio_mensual_covid_placebo.png:  h = −6..12; zona gris = meses antes del choque (−6 ≤ h < 0), línea punteada = choque (h = 0).
Respuesta = nivel en t+h respecto a t−1, en %. Bandas simétricas alrededor de la estimación: 68% (± 1 ee) y 90% (± 1.645 ee),
con ee = desviación estándar de la misma respuesta bajo 1,000 sorpresas permutadas. Eje vertical simétrico (el cero al centro)
y común a las dos muestras de cada variable. h = −1 es cero por construcción (mes de referencia); con el rezago propio como
control (E1, T1) también h = −2 es cero por construcción, así que el placebo informativo es h = −6..−3.

Uso (desde code/Python):  python 05b_graficas_irf.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

RAIZ = Path(__file__).resolve().parents[1].parent
irf = pd.read_csv(RAIZ / "outputs/tables/irf_promedio_mensual_covid.csv")
irf["inf90"], irf["sup90"] = irf.respuesta - 1.645 * irf.ee, irf.respuesta + 1.645 * irf.ee
irf["inf68"], irf["sup68"] = irf.respuesta - irf.ee, irf.respuesta + irf.ee

AZUL, T1, T2, GRID, SUP, GRIS = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#ecebe7"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": T2,
                     "xtick.color": T2, "ytick.color": T2, "figure.facecolor": SUP, "axes.facecolor": SUP})
NOMBRES = {"produccion": "Producción real", "empleo": "Empleo", "horas": "Horas trabajadas",
           "exportaciones": "Exportaciones (Banxico)", "importaciones_eeuu": "Importaciones de EE.UU. desde México"}
MUESTRAS = ["completa", "sin pandemia"]

def limites_simetricos(m):
    """Límite simétrico 'redondo' y marcas que incluyen el cero: ±k·paso con k ≤ 3."""
    crudo = m / 3
    mag = 10 ** np.floor(np.log10(crudo))
    paso = next(f * mag for f in (1, 2, 2.5, 5, 10) if f * mag >= crudo)
    k = int(np.ceil(m / paso - 1e-9))
    return k * paso, np.arange(-k, k + 1) * paso

def figura(h_min, archivo, titulo, subtitulo):
    fig, ejes = plt.subplots(5, 2, figsize=(11, 15.5))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.895, bottom=0.075, hspace=0.44, wspace=0.14)
    for i, v in enumerate(NOMBRES):
        fila = irf[(irf.variable == v) & (irf.h >= h_min)]
        lim, marcas = limites_simetricos(1.05 * np.abs(fila[["inf90", "sup90"]].values).max())
        for j, m in enumerate(MUESTRAS):
            a, d = ejes[i, j], fila[fila.muestra == m].sort_values("h")
            if h_min < 0:
                a.axvspan(h_min, 0, color=GRIS, lw=0, zorder=0)
                a.axvline(0, color=T2, lw=0.9, ls=(0, (3, 3)), zorder=1)
                if i == 0:
                    a.text(h_min / 2, lim * 0.86, "antes del choque\n(placebo)", ha="center", va="top", color=T2, fontsize=8)
            a.axhline(0, color=T2, lw=0.9, zorder=1)
            a.fill_between(d.h, d.inf90, d.sup90, color=AZUL, alpha=0.13, lw=0, zorder=2)
            a.fill_between(d.h, d.inf68, d.sup68, color=AZUL, alpha=0.28, lw=0, zorder=2)
            a.plot(d.h, d.respuesta, color=AZUL, lw=2, zorder=3)
            a.plot(d.h, d.respuesta, "o", color=AZUL, ms=3.2, zorder=4)
            a.set_xlim(h_min, 12)
            a.set_xticks(range(h_min, 13, 2) if h_min % 2 == 0 else range(h_min, 13))
            a.set_ylim(-lim, lim); a.set_yticks(marcas)
            a.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:g}".replace("-", "\u2212")))
            a.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:g}".replace("-", "\u2212")))
            a.grid(axis="y", color=GRID, lw=0.7, zorder=0)
            for s_ in ("top", "right", "left"): a.spines[s_].set_visible(False)
            a.spines["bottom"].set_visible(False)
            a.tick_params(length=0)
            a.tick_params(axis="x", pad=7)
            a.set_title(f"{NOMBRES[v]} · {m}  [{d.especificacion.iloc[0]}]", loc="left", color=T1, fontsize=10, fontweight="bold")
            if j == 0:
                a.set_ylabel("% respecto a t−1")
            if i == 4:
                a.set_xlabel("meses respecto al choque (h)" if h_min < 0 else "meses después del choque (h)")
    fig.align_ylabels(ejes[:, 0])
    fig.text(0.012, 0.985, titulo, fontsize=13.5, fontweight="bold", color=T1, va="top")
    fig.text(0.012, 0.962, subtitulo, fontsize=8.8, color=T2, va="top")
    fig.legend(handles=[Line2D([], [], color=AZUL, lw=2, marker="o", ms=3.2, label="respuesta estimada"),
                        Patch(color=AZUL, alpha=0.28, lw=0, label="IC 68%"), Patch(color=AZUL, alpha=0.13, lw=0, label="IC 90%")],
               loc="upper left", bbox_to_anchor=(0.006, 0.935), ncol=3, frameon=False, fontsize=8.5)
    fig.text(0.012, 0.012, "Variaciones mensuales. Controles: producción industrial de EE.UU. (t), tipo de cambio y VIX (t−1), arancel efectivo de la rama, "
             "índice EMV de enfermedades infecciosas y dicótomas\nabr-may-jun 2020 (en t+h). [E0]/[T0]: solo esos controles; [E1]/[T1]: más el rezago propio "
             "de la variable. Choque: sorpresa del TPU con control de COVID. Promedio simple de las ramas.", fontsize=7.8, color=T2)
    fig.savefig(RAIZ / f"outputs/figures/{archivo}", dpi=150)
    plt.close(fig)
    print("Guardado:", archivo)

figura(0, "irf_promedio_mensual_covid.png", "Respuesta a una sorpresa del TPU de 1 desv. est. (promedio de las ramas)",
       "Nivel en t+h respecto al mes previo al choque (t−1). Bandas simétricas alrededor de la estimación; error estándar por permutación.")
figura(-6, "irf_promedio_mensual_covid_placebo.png", "Respuesta a una sorpresa del TPU de 1 desv. est., con placebo (promedio de las ramas)",
       "Nivel en t+h respecto al mes previo al choque (t−1). Zona gris: meses antes del choque, donde la respuesta debe ser cero.\n"
       "h = −1 es la referencia (cero por construcción); con [E1]/[T1], h = −2 también es cero por construcción.")

# Coherencia entre las bandas simétricas y los valores p de permutación
chk = irf[irf.h != -1].assign(fuera90=lambda d: (d.inf90 > 0) | (d.sup90 < 0), p10=lambda d: d.p < 0.10)
print("Horizontes donde la banda del 90% y el valor p de permutación no coinciden:", int((chk.fuera90 != chk.p10).sum()), "de", len(chk))
