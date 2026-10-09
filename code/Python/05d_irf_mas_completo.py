"""IRF promedio con la especificación MÁS COMPLETA para cada variable (comparación con la elegida por placebo y BIC).

Más completa: E4 para producción, empleo y horas (3 rezagos de producción, empleo, horas y exportaciones a EE.UU.);
T2 para exportaciones e importaciones (3 rezagos propios). Mismo cálculo que 05_irf_promedio.py (variaciones mensuales,
choque y controles de pandemia). La gráfica superpone, en gris punteado, la IRF de la especificación elegida.

Uso (desde code/Python):  python 05d_irf_mas_completo.py
Salidas: outputs/tables/irf_promedio_mensual_covid_mas_completo.csv, outputs/figures/irf_mas_completo_vs_elegida.png
"""
import sys
sys.argv = [sys.argv[0], "1", "covid"]
from pathlib import Path
import numpy as np
import pandas as pd

src = Path(__file__).with_name("04_especificaciones_por_rama.py").read_text(encoding="utf-8")
src = src[:src.index('if __name__ != "__main__":')]
ns = {"__file__": str(Path(__file__).with_name("04_especificaciones_por_rama.py"))}
exec(compile(src, "04_especificaciones_por_rama.py", "exec"), ns)
RAIZ = ns["RAIZ"]
MAS_COMPLETA = {"produccion": "E4", "empleo": "E4", "horas": "E4", "exportaciones": "T2", "importaciones_eeuu": "T2"}
filas = []
for v, spec in MAS_COMPLETA.items():
    for m in ["completa", "sin pandemia"]:
        ns["estimar"](v, spec, m == "sin pandemia", None)
        b = ns["IRF_ULTIMA"]
        for h in range(-6, 13):
            x = np.sum([b[j] for j in range(0, h + 1)], axis=0) if h >= 0 else (np.zeros_like(b[-1]) if h == -1 else -np.sum([b[j] for j in range(h + 1, 0)], axis=0))
            filas.append(dict(variable=v, muestra=m, especificacion=spec, h=h, respuesta=x[0], ee=x[1:].std(),
                              p=float(np.mean(np.abs(x[1:]) >= abs(x[0]))) if h != -1 else np.nan))
        print(v, m, spec, "listo", flush=True)
irf = pd.DataFrame(filas)
irf.to_csv(RAIZ / "outputs/tables/irf_promedio_mensual_covid_mas_completo.csv", index=False)
eleg = pd.read_csv(RAIZ / "outputs/tables/irf_promedio_mensual_covid.csv")

# ------------------------------------------------------------------ gráfica (mismo formato que 05b, con la elegida superpuesta)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
irf["inf90"], irf["sup90"] = irf.respuesta - 1.645 * irf.ee, irf.respuesta + 1.645 * irf.ee
irf["inf68"], irf["sup68"] = irf.respuesta - irf.ee, irf.respuesta + irf.ee
AZUL, T1, T2, GRID, SUP, GRIS, ELEG = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb", "#ecebe7", "#52514e"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": T2,
                     "xtick.color": T2, "ytick.color": T2, "figure.facecolor": SUP, "axes.facecolor": SUP})
NOMBRES = {"produccion": "Producción real", "empleo": "Empleo", "horas": "Horas trabajadas",
           "exportaciones": "Exportaciones (Banxico)", "importaciones_eeuu": "Importaciones de EE.UU. desde México"}
def limites_simetricos(m):
    crudo = m / 3; mag = 10 ** np.floor(np.log10(crudo))
    paso = next(f * mag for f in (1, 2, 2.5, 5, 10) if f * mag >= crudo)
    k = int(np.ceil(m / paso - 1e-9)); return k * paso, np.arange(-k, k + 1) * paso
fmt = matplotlib.ticker.FuncFormatter(lambda x, _: f"{x:g}".replace("-", "−"))
fig, ejes = plt.subplots(5, 2, figsize=(11, 15.5))
fig.subplots_adjust(left=0.075, right=0.985, top=0.89, bottom=0.075, hspace=0.52, wspace=0.14)
for i, v in enumerate(NOMBRES):
    fila, fe = irf[irf.variable == v], eleg[eleg.variable == v]
    lim, marcas = limites_simetricos(1.05 * max(np.abs(fila[["inf90", "sup90"]].values).max(), np.abs(fe.respuesta).max()))
    for j, m in enumerate(["completa", "sin pandemia"]):
        a, d, de = ejes[i, j], fila[fila.muestra == m].sort_values("h"), fe[fe.muestra == m].sort_values("h")
        a.axvspan(-6, 0, color=GRIS, lw=0, zorder=0)
        a.axvline(0, color=T2, lw=0.9, ls=(0, (3, 3)), zorder=1)
        a.axhline(0, color=T2, lw=0.9, zorder=1)
        a.fill_between(d.h, d.inf90, d.sup90, color=AZUL, alpha=0.13, lw=0, zorder=2)
        a.fill_between(d.h, d.inf68, d.sup68, color=AZUL, alpha=0.28, lw=0, zorder=2)
        a.plot(de.h, de.respuesta, color=ELEG, lw=1.4, ls=(0, (2, 2)), zorder=3)
        a.plot(d.h, d.respuesta, color=AZUL, lw=2, zorder=4)
        est = d[d.h != -1]
        a.plot(est.h, est.respuesta, "o", color=AZUL, ms=3.2, zorder=5)
        a.plot([-1], [0], "o", ms=5.5, mfc=SUP, mec=AZUL, mew=1.5, zorder=6)
        a.set_xlim(-6, 12); a.set_xticks(range(-6, 13, 2)); a.xaxis.set_major_formatter(fmt)
        a.set_ylim(-lim, lim); a.set_yticks(marcas); a.yaxis.set_major_formatter(fmt)
        a.grid(axis="y", color=GRID, lw=0.7, zorder=0)
        for s_ in ("top", "right", "left", "bottom"): a.spines[s_].set_visible(False)
        a.tick_params(length=0); a.tick_params(axis="x", pad=7)
        a.set_title(f"{NOMBRES[v]} · {m}", loc="left", color=T1, fontsize=10, fontweight="bold", pad=16)
        a.text(0, 1.015, f"más completa: {d.especificacion.iloc[0]}  ·  elegida: {de.especificacion.iloc[0]}",
               transform=a.transAxes, ha="left", va="bottom", fontsize=8.2, color=T2)
        if j == 0: a.set_ylabel("% respecto a t−1")
        if i == 4: a.set_xlabel("meses respecto al choque (h)")
fig.align_ylabels(ejes[:, 0])
fig.text(0.012, 0.985, "IRF con la especificación más completa vs. la elegida (promedio de las ramas)", fontsize=13.5, fontweight="bold", color=T1, va="top")
fig.text(0.012, 0.962, "Azul (con bandas al 68% y 90%): especificación más completa. Gris punteado: especificación elegida por placebo y BIC (la de las gráficas anteriores).\n"
         "Nivel en t+h respecto a t−1 ante una sorpresa del TPU de 1 desv. est. Zona gris: placebo; h = −1 es la referencia.", fontsize=8.6, color=T2, va="top")
fig.legend(handles=[Line2D([], [], color=AZUL, lw=2, marker="o", ms=3.2, label="más completa"),
                    Patch(color=AZUL, alpha=0.28, lw=0, label="IC 68%"), Patch(color=AZUL, alpha=0.13, lw=0, label="IC 90%"),
                    Line2D([], [], color=ELEG, lw=1.4, ls=(0, (2, 2)), label="elegida")],
           loc="upper left", bbox_to_anchor=(0.006, 0.928), ncol=4, frameon=False, fontsize=8.5)
fig.text(0.012, 0.012, "E4: controles macro y de pandemia + 3 rezagos de producción, empleo, horas y exportaciones a EE.UU.  T2: controles macro y de pandemia + 3 rezagos propios.",
         fontsize=7.8, color=T2)
fig.savefig(RAIZ / "outputs/figures/irf_mas_completo_vs_elegida.png", dpi=150)
print("Guardado: outputs/figures/irf_mas_completo_vs_elegida.png")
chk = irf[irf.h >= 0].merge(eleg[eleg.h >= 0], on=["variable", "muestra", "h"], suffixes=("_mc", "_el"))
print(chk[chk.h.isin([6, 9, 12])].pivot_table(index=["variable", "muestra"], columns="h", values=["respuesta_mc", "respuesta_el", "p_mc"]).round(2).to_string())
