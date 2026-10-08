"""Efecto acumulado a 12 meses por rama vs. coeficiente de exportación (MIP 2018).

Efecto de la rama = Σ_{h=0..12} β_h (nivel en t+12 respecto a t−1, en %), especificación elegida en
especificaciones_resumen_mensual_covid.csv (variaciones mensuales, controles de pandemia).
Pendiente: MCO de las 86 ramas (efecto sobre coeficiente). Error estándar y valor p de la pendiente por permutación:
la misma pendiente calculada con los efectos de cada rama bajo 1,000 sorpresas permutadas (comunes a todas las ramas,
así que se respeta la correlación entre ramas). Barras: ± 1.645 ee de cada rama (también por permutación).

Uso (desde code/Python):  python 06_scatter_exposicion.py
Salidas: outputs/tables/efecto_12m_vs_exportacion.csv, outputs/figures/efecto_12m_vs_exportacion.png
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
RAIZ, base = ns["RAIZ"], ns["base"]
info = base.groupby("rama").agg(rama_nombre=("rama_nombre", "first"), coef_exportacion=("mip_coef_exportacion_2018", "first"))
eleg = pd.read_csv(RAIZ / "outputs/tables/especificaciones_resumen_mensual_covid.csv")
eleg = eleg[eleg.elegida]
filas, pendientes = [], []
for _, e in eleg.iterrows():
    df, _ = ns["estimar"](e.variable, e.especificacion, e.muestra == "sin pandemia", None)
    df = df.merge(info, left_on="rama", right_index=True, how="left", validate="one_to_one")
    N = np.vstack(df.nulos.values)                                # (ramas, permutaciones)
    x = df.coef_exportacion.values - df.coef_exportacion.mean()
    b = x @ (df.sens.values - df.sens.mean()) / (x @ x)
    b_perm = x @ (N - N.mean(axis=0)) / (x @ x)
    pendientes.append(dict(variable=e.variable, muestra=e.muestra, especificacion=e.especificacion, pendiente=b, ee=b_perm.std(),
                           p=float(np.mean(np.abs(b_perm) >= abs(b))), intercepto=df.sens.mean() - b * df.coef_exportacion.mean(),
                           correlacion=np.corrcoef(df.coef_exportacion, df.sens)[0, 1], ramas=len(df)))
    filas.append(df.drop(columns=["nulos", "nulos_pre", "pre"]).assign(ee_rama=N.std(axis=1), variable=e.variable, muestra=e.muestra,
                                                                      especificacion=e.especificacion))
    print(pendientes[-1], flush=True)
pts, pen = pd.concat(filas, ignore_index=True), pd.DataFrame(pendientes)
pts = pts.rename(columns={"sens": "efecto_12m"})
pts.to_csv(RAIZ / "outputs/tables/efecto_12m_vs_exportacion.csv", index=False)
pen.to_csv(RAIZ / "outputs/tables/efecto_12m_vs_exportacion_pendientes.csv", index=False)

# ------------------------------------------------------------------ gráfica
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
AZUL, T1, T2, GRID, SUP = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": T2,
                     "xtick.color": T2, "ytick.color": T2, "figure.facecolor": SUP, "axes.facecolor": SUP})
NOMBRES = {"produccion": "Producción real", "empleo": "Empleo", "horas": "Horas trabajadas",
           "exportaciones": "Exportaciones (Banxico)", "importaciones_eeuu": "Importaciones de EE.UU. desde México"}
def limites_simetricos(m):
    crudo = m / 3; mag = 10 ** np.floor(np.log10(crudo))
    paso = next(f * mag for f in (1, 2, 2.5, 5, 10) if f * mag >= crudo)
    k = int(np.ceil(m / paso - 1e-9)); return k * paso, np.arange(-k, k + 1) * paso
fig, ejes = plt.subplots(5, 2, figsize=(11, 16))
fig.subplots_adjust(left=0.075, right=0.985, top=0.895, bottom=0.07, hspace=0.55, wspace=0.14)
fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace("-", "−"))
for i, v in enumerate(NOMBRES):
    fila = pts[pts.variable == v]
    lim, marcas = limites_simetricos(1.05 * np.abs(fila.efecto_12m).max())
    for j, m in enumerate(["completa", "sin pandemia"]):
        a, d = ejes[i, j], fila[fila.muestra == m]
        p = pen[(pen.variable == v) & (pen.muestra == m)].iloc[0]
        a.axhline(0, color=T2, lw=0.9, zorder=1)
        a.errorbar(d.coef_exportacion, d.efecto_12m, yerr=1.645 * d.ee_rama, fmt="none", ecolor=AZUL, alpha=0.18, lw=0.9, zorder=2)
        a.scatter(d.coef_exportacion, d.efecto_12m, s=18, color=AZUL, edgecolor=SUP, lw=0.6, zorder=3)
        xs = np.array([0, 1])
        a.plot(xs, p.intercepto + p.pendiente * xs, color=T1, lw=1.4, ls=(0, (4, 2)), zorder=4)
        puestas = []                                   # si dos etiquetas quedarían juntas, la segunda va a la izquierda del punto
        for _, r in d.reindex(d.efecto_12m.abs().sort_values(ascending=False).index[:3]).iterrows():
            cerca = any(abs(r.coef_exportacion - x0) < 0.08 and abs(r.efecto_12m - y0) < 0.12 * lim for x0, y0 in puestas)
            a.annotate(r.rama, (r.coef_exportacion, r.efecto_12m), xytext=(-4, 2) if cerca else (4, 2), textcoords="offset points",
                       ha="right" if cerca else "left", fontsize=7, color=T2)
            puestas.append((r.coef_exportacion, r.efecto_12m))
        a.set_xlim(0, 1); a.set_xticks(np.arange(0, 1.01, 0.2))
        a.set_ylim(-lim, lim); a.set_yticks(marcas)
        a.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v_, _: f"{v_:.1f}"))
        a.yaxis.set_major_formatter(fmt)
        a.grid(color=GRID, lw=0.6, zorder=0)
        for s_ in ("top", "right", "left", "bottom"): a.spines[s_].set_visible(False)
        a.tick_params(length=0); a.tick_params(axis="x", pad=6)
        a.set_title(f"{NOMBRES[v]} · {m}  [{p.especificacion}]", loc="left", color=T1, fontsize=10, fontweight="bold", pad=16)
        a.text(0, 1.015, f"pendiente {p.pendiente:+.2f} (ee {p.ee:.2f}, p = {p.p:.2f}); correlación {p.correlacion:+.2f}".replace("-", "\u2212"),
               transform=a.transAxes, ha="left", va="bottom", fontsize=8.2, color=T2)
        if j == 0: a.set_ylabel("efecto a 12 meses (%)")
        if i == 4: a.set_xlabel("coeficiente de exportación (MIP 2018)")
fig.align_ylabels(ejes[:, 0])
fig.text(0.012, 0.985, "Efecto acumulado a 12 meses de una sorpresa del TPU vs. orientación exportadora, por rama", fontsize=13, fontweight="bold", color=T1, va="top")
fig.text(0.012, 0.962, "Cada punto es una rama: nivel en t+12 respecto a t−1 ante una sorpresa de 1 desv. est. Barras: ± 1.645 ee de la rama. "
         "Línea punteada: ajuste MCO entre ramas.\nValor p de la pendiente por permutación de la sorpresa (respeta la correlación entre ramas). "
         "Se etiquetan las 3 ramas con mayor efecto absoluto.", fontsize=8.6, color=T2, va="top")
fig.text(0.012, 0.012, "Variaciones mensuales; controles: IP de EE.UU., tipo de cambio, VIX, arancel de la rama, EMV de enfermedades infecciosas y dicótomas abr-jun 2020; "
         "especificación elegida por placebo y BIC.", fontsize=7.8, color=T2)
fig.savefig(RAIZ / "outputs/figures/efecto_12m_vs_exportacion.png", dpi=150)
print("Guardado: outputs/figures/efecto_12m_vs_exportacion.png")
