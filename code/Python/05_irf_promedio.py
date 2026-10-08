"""IRF promedio de las ramas con la especificación elegida (variaciones mensuales, choque y controles de pandemia).

Respuesta del NIVEL respecto al mes previo al choque (t−1), en %: para h ≥ 0, Σ_{j=0..h} β_j; para h < 0, −Σ_{j=h+1..−1} β_j
(tramo placebo). β_j = promedio de las ramas de la respuesta de Δ log y(t+j). Banda: percentiles 5-95 de las mismas
sumas con 1,000 sorpresas permutadas; valor p por horizonte = proporción de permutaciones con |respuesta| ≥ la real.

Uso (desde code/Python):  python 05_irf_promedio.py
Salidas: outputs/tables/irf_promedio_mensual_covid.csv, outputs/figures/irf_promedio_mensual_covid.png
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
elegidas = pd.read_csv(RAIZ / "outputs/tables/especificaciones_resumen_mensual_covid.csv")
elegidas = elegidas[elegidas.elegida]
filas = []
for _, e in elegidas.iterrows():
    ns["estimar"](e.variable, e.especificacion, e.muestra == "sin pandemia", None)
    b = ns["IRF_ULTIMA"]
    for h in range(-6, 13):
        if h >= 0:
            v = np.sum([b[j] for j in range(0, h + 1)], axis=0)
        elif h == -1:
            v = np.zeros_like(b[-1])
        else:
            v = -np.sum([b[j] for j in range(h + 1, 0)], axis=0)
        filas.append(dict(variable=e.variable, muestra=e.muestra, especificacion=e.especificacion, h=h, respuesta=v[0],
                          nulo_p05=np.quantile(v[1:], 0.05), nulo_p95=np.quantile(v[1:], 0.95),
                          p=float(np.mean(np.abs(v[1:]) >= abs(v[0]))) if h != -1 else np.nan))
    print(e.variable, e.muestra, e.especificacion, "listo", flush=True)
irf = pd.DataFrame(filas)
irf.to_csv(RAIZ / "outputs/tables/irf_promedio_mensual_covid.csv", index=False)
print("Guardado: outputs/tables/irf_promedio_mensual_covid.csv")

# ------------------------------------------------------------------ gráfica
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
AZUL, T1, T2, GRID, SUP, BANDA = "#2a78d6", "#0b0b0b", "#52514e", "#e9e8e4", "#fcfcfb", "#8a8984"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": T2,
                     "xtick.color": T2, "ytick.color": T2, "figure.facecolor": SUP, "axes.facecolor": SUP})
NOMBRES = {"produccion": "Producción real", "empleo": "Empleo", "horas": "Horas trabajadas",
           "exportaciones": "Exportaciones (Banxico)", "importaciones_eeuu": "Importaciones de EE.UU. desde México"}
fig, ejes = plt.subplots(5, 2, figsize=(11, 15), sharex=True)
for i, v in enumerate(NOMBRES):
    sub = irf[irf.variable == v]
    lo, hi = min(sub.respuesta.min(), sub.nulo_p05.min()), max(sub.respuesta.max(), sub.nulo_p95.max())
    pad = 0.08 * (hi - lo)
    for j, m in enumerate(["completa", "sin pandemia"]):
        a, d = ejes[i, j], sub[sub.muestra == m].sort_values("h")
        a.fill_between(d.h, d.nulo_p05, d.nulo_p95, color=BANDA, alpha=0.22, lw=0)
        a.axhline(0, color=T2, lw=0.8); a.axvline(-0.5, color=T2, lw=0.8, ls=(0, (3, 3)))
        a.plot(d.h, d.respuesta, color=AZUL, lw=2)
        sig = d.p < 0.10
        a.scatter(d.h[~sig], d.respuesta[~sig], s=22, facecolor="white", edgecolor=AZUL, lw=1.5, zorder=3)
        a.scatter(d.h[sig], d.respuesta[sig], s=22, color=AZUL, zorder=3)
        a.set_ylim(lo - pad, hi + pad)
        a.grid(axis="y", color=GRID, lw=0.8); a.set_axisbelow(True)
        for s_ in ("top", "right", "left"): a.spines[s_].set_visible(False)
        a.tick_params(length=0)
        a.set_title(f"{NOMBRES[v]} · {m} ({d.especificacion.iloc[0]})", loc="left", color=T1, fontsize=10, fontweight="bold")
        if j == 0: a.set_ylabel("% respecto a t−1")
        a.set_xticks([-6, -3, 0, 3, 6, 9, 12])
for a in ejes[-1]: a.set_xlabel("meses respecto al choque (h)")
fig.text(0.01, 0.995, "Respuesta del nivel a una sorpresa del TPU de 1 desv. est. (promedio de las ramas)", fontsize=13, fontweight="bold", color=T1, va="top")
fig.text(0.01, 0.982, "Línea: respuesta estimada. Banda gris: 5-95% con sorpresas permutadas (lo que se vería sin efecto). Punto relleno: p < 0.10.\n"
         "Izquierda de la línea punteada: placebo (antes del choque).", fontsize=8.5, color=T2, va="top")
fig.text(0.01, 0.003, "Variaciones mensuales; controles: IP de EE.UU., tipo de cambio, VIX, arancel de la rama, índice EMV de enfermedades infecciosas\n"
         "y dicótomas abr-jun 2020. Choque: sorpresa del TPU con control de COVID.", fontsize=8, color=T2)
plt.tight_layout(rect=(0, 0.02, 1, 0.97))
fig.savefig(RAIZ / "outputs/figures/irf_promedio_mensual_covid.png", dpi=150)
print("Guardado: outputs/figures/irf_promedio_mensual_covid.png")
