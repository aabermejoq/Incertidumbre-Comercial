"""Local projections rama por rama: efecto de la sorpresa del TPU sobre la producción real de cada rama.

Complementa 02_local_projections.ipynb (especificación A estima una sola pendiente común; aquí se estima un efecto por rama).
Para cada rama i y horizonte h = 0..12, con datos mensuales de la propia rama:

  log y(t+h) − log y(t−1) = c + mes del calendario + β_h s_t + θ s_{t−1} + ρ1 Δlog y(t−1) + ρ2 Δlog y(t−2)
                            + κ Δ12 IP_EEUU_t + φ Δ12 TC_{t−1} + ψ Δ12 VIX_{t−1} + γ Δ12 arancel_t + δ Δlog días hábiles + e

Controles más austeros que en el panel porque cada rama tiene solo 70-88 meses. El efecto de cada rama incluye los canales
macroeconómicos comunes (no hay efectos fijos de mes). Inferencia: permutación de la sorpresa (las mismas 1,000 en todas las
ramas y horizontes); el estadístico es el efecto medio en los horizontes indicados. Corrección por comparaciones múltiples:
Benjamini-Hochberg (q).

Uso (desde code/Python):  python lp_produccion_por_rama.py
Salida: outputs/tables/lp_produccion_por_rama.csv
"""
import re
from pathlib import Path
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]

# Reutiliza las secciones 1-2 y las definiciones de la sección 3 del notebook 02 (base, sorpresa, días hábiles, permutaciones)
import nbformat
nb = nbformat.read(AQUI / "02_local_projections.ipynb", as_version=4)
ns = {"display": lambda *a, **k: None}
codigo = []
for c in nb.cells:
    if c.cell_type == "markdown" and "### Gráficas" in c.source:
        break
    if c.cell_type == "code":
        codigo.append(c.source.replace("from IPython.display import HTML, Markdown, display", "from IPython.display import HTML, Markdown"))
fuente = "\n".join(codigo)
fuente = fuente[:fuente.index("# Verificación: el estimador")]   # sin la verificación (no hace falta aquí)
import os
os.chdir(AQUI)
exec(compile(fuente, "02_local_projections", "exec"), ns)
base, PERM, MESES_S, POS_MES, PANDEMIA = ns["base"], ns["PERM"], ns["MESES_S"], ns["POS_MES"], ns["PANDEMIA"]
en_fecha, DIAS_HABILES, s = ns["en_fecha"], ns["DIAS_HABILES"], ns["serie_choque"]("sorpresa_tpu_std")
H = list(range(0, 13))
VENTANAS = {"h0_12": H, "h1_6": list(range(1, 7)), "h7_12": list(range(7, 13))}

base["_pos0"] = base.mes.map(POS_MES).fillna(-1).astype(int)
base["_pos1"] = (base.mes - pd.DateOffset(months=1)).map(POS_MES).fillna(-1).astype(int)
W_comun = pd.DataFrame({
    "dl1_l1": en_fecha("dl1_produccion", -1), "dl1_l2": en_fecha("dl1_produccion", -2),
    "ip": base.d12_ip_eeuu.values, "tc_l1": en_fecha("d12_tc", -1), "vix_l1": en_fecha("d12_vix", -1), "arancel": base.d12_arancel.values,
})
for k in range(2, 13):
    W_comun[f"mes_{k}"] = (base.mes.dt.month == k).astype(float).values

def una_rama(rama, excluir_pandemia):
    sel = (base.rama == rama).values
    betas, perms, ns_ = {}, {}, {}
    for h in H:
        W = W_comun.copy()
        W["dias"] = ((base.mes + pd.DateOffset(months=h)).map(np.log(DIAS_HABILES)) - (base.mes - pd.DateOffset(months=1)).map(np.log(DIAS_HABILES))).values
        y = en_fecha("l_produccion", h) - en_fecha("l_produccion", -1)
        ok = sel & ~np.isnan(y) & W.notna().all(axis=1).values & (base._pos1.values >= 0)
        if excluir_pandemia:
            ini, fin = base.mes - pd.DateOffset(months=1), base.mes + pd.DateOffset(months=h)
            ok &= ~((ini <= PANDEMIA[1]) & (fin >= PANDEMIA[0])).values
        idx = np.flatnonzero(ok)
        if len(idx) < 40:
            return None
        Wm = np.column_stack([np.ones(len(idx)), W.values[idx]])
        Q, _ = np.linalg.qr(Wm)
        res = lambda A: A - Q @ (Q.T @ A)
        yt = res(y[idx])
        p0, p1 = base._pos0.values[idx], base._pos1.values[idx]
        # columnas del choque (s_t, s_{t-1}) para la serie real y las permutadas
        S = np.vstack([s, s[PERM]])                       # (1 + N_PERM, T)
        X0, X1 = res(S[:, p0].T), res(S[:, p1].T)        # (n, 1 + N_PERM)
        a, b, c = (X0 * X0).sum(0), (X0 * X1).sum(0), (X1 * X1).sum(0)
        d0, d1 = (X0 * yt[:, None]).sum(0), (X1 * yt[:, None]).sum(0)
        beta = (c * d0 - b * d1) / (a * c - b * b)       # coeficiente de s_t con s_{t-1} como control
        betas[h], perms[h], ns_[h] = beta[0], beta[1:], len(idx)
    fila = {}
    for nombre, hs in VENTANAS.items():
        real = np.mean([betas[h] for h in hs]) * 100
        falsos = np.mean([perms[h] for h in hs], axis=0) * 100
        fila[f"efecto_{nombre}"] = real
        fila[f"p_{nombre}"] = float(np.mean(np.abs(falsos) >= abs(real)))
    fila.update({f"efecto_h{h}": betas[h] * 100 for h in H})
    fila["meses_h0"], fila["meses_h12"] = ns_[0], ns_[12]
    return fila

def bh(p):
    p = np.asarray(p, float); orden = np.argsort(p); n = len(p)
    q = np.empty(n); acumulado = 1.0
    for rango, i in reversed(list(enumerate(orden, start=1))):
        acumulado = min(acumulado, p[i] * n / rango); q[i] = acumulado
    return q

filas = []
info = base.groupby("rama").agg(rama_nombre=("rama_nombre", "first"), coef_exportacion=("mip_coef_exportacion_2018", "first"))
for excl, etiqueta in [(True, "sin pandemia"), (False, "completa")]:
    for rama in sorted(base.rama.unique()):
        f = una_rama(rama, excl)
        if f is not None:
            filas.append(dict(rama=rama, muestra=etiqueta, **f))
out = pd.DataFrame(filas).merge(info, left_on="rama", right_index=True, how="left", validate="many_to_one")
for v in VENTANAS:
    out[f"q_{v}"] = out.groupby("muestra")[f"p_{v}"].transform(bh)
cols = ["muestra", "rama", "rama_nombre", "coef_exportacion", *[f"{k}_{v}" for v in VENTANAS for k in ("efecto", "p", "q")], "meses_h0", "meses_h12", *[f"efecto_h{h}" for h in H]]
out = out[cols].sort_values(["muestra", "efecto_h0_12"], ascending=[False, True])
out.to_csv(RAIZ / "outputs/tables/lp_produccion_por_rama.csv", index=False)
print("Guardado:", RAIZ / "outputs/tables/lp_produccion_por_rama.csv", out.shape)
