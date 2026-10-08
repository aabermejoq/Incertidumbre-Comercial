"""IRF promedio de las ramas con la especificación elegida (variaciones mensuales, choque y controles de pandemia).

Respuesta del NIVEL respecto al mes previo al choque (t−1), en %: para h ≥ 0, Σ_{j=0..h} β_j; para h < 0, −Σ_{j=h+1..−1} β_j
(placebo, solo en la tabla). β_j = promedio de las ramas de la respuesta de Δ log y(t+j).
Error estándar = desviación estándar de la misma respuesta con 1,000 sorpresas permutadas. Gráfica: h = 0..12, bandas
simétricas al 68% (± 1 ee) y al 90% (± 1.645 ee) alrededor de la estimación. Valor p por permutación.

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
                          ee=v[1:].std(), nulo_p05=np.quantile(v[1:], 0.05), nulo_p95=np.quantile(v[1:], 0.95),
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
    sub = irf[(irf.variable == v) & (irf.h >= 0)].copy()
    sub["inf90"], sub["sup90"] = sub.respuesta - 1.645 * sub.ee, sub.respuesta + 1.645 * sub.ee
    sub["inf68"], sub["sup68"] = sub.respuesta - sub.ee, sub.respuesta + sub.ee
    lim = 1.1 * np.abs(sub[["inf90", "sup90"]].values).max()                 # eje simétrico: el cero al centro
    for j, m in enumerate(["completa", "sin pandemia"]):
        a, d = ejes[i, j], sub[sub.muestra == m].sort_values("h")
        a.fill_between(d.h, d.inf90, d.sup90, color=AZUL, alpha=0.12, lw=0, label="IC 90%")
        a.fill_between(d.h, d.inf68, d.sup68, color=AZUL, alpha=0.25, lw=0, label="IC 68%")
        a.axhline(0, color=T2, lw=0.9)
        a.plot(d.h, d.respuesta, color=AZUL, lw=2)
        a.set_ylim(-lim, lim); a.set_xlim(0, 12)
        a.grid(axis="y", color=GRID, lw=0.8); a.set_axisbelow(True)
        for s_ in ("top", "right", "left"): a.spines[s_].set_visible(False)
        a.tick_params(length=0)
        a.set_title(f"{NOMBRES[v]} · {m}", loc="left", color=T1, fontsize=10, fontweight="bold")
        if j == 0: a.set_ylabel("% respecto a t−1")
        a.set_xticks(range(0, 13, 2))
ejes[0, 0].legend(loc="lower left", frameon=False, fontsize=8)
for a in ejes[-1]: a.set_xlabel("meses después del choque (h)")
fig.text(0.01, 0.995, "Respuesta a una sorpresa del TPU de 1 desv. est. (promedio de las ramas)", fontsize=13, fontweight="bold", color=T1, va="top")
fig.text(0.01, 0.982, "Nivel respecto al mes previo al choque. Bandas: intervalos de confianza al 68% y 90% (error estándar por permutación).",
         fontsize=8.5, color=T2, va="top")
fig.text(0.01, 0.003, "Variaciones mensuales; controles: IP de EE.UU., tipo de cambio, VIX, arancel de la rama, índice EMV de enfermedades infecciosas\n"
         "y dicótomas abr-jun 2020; especificación elegida por placebo y BIC. Choque: sorpresa del TPU con control de COVID.", fontsize=8, color=T2)
plt.tight_layout(rect=(0, 0.02, 1, 0.975))
fig.savefig(RAIZ / "outputs/figures/irf_promedio_mensual_covid.png", dpi=150)
print("Guardado: outputs/figures/irf_promedio_mensual_covid.png")
