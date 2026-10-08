"""Verificación independiente de la IRF de producción (muestra completa): MCO con statsmodels rama por rama, sin el estimador de 04.
Debe coincidir con outputs/tables/irf_promedio_mensual_covid.csv (diferencia ~1e-15). Uso (desde code/Python): python 05c_verifica_irf.py"""
import sys
sys.argv = ["x", "1", "covid"]
from pathlib import Path
import numpy as np, pandas as pd, statsmodels.api as sm
src = Path("04_especificaciones_por_rama.py").read_text(encoding="utf-8")
src = src[:src.index('if __name__ != "__main__":')]
ns = {"__file__": str(Path("04_especificaciones_por_rama.py").resolve())}
exec(compile(src, "04", "exec"), ns)
P, choque, ramas = ns["P"].copy(), ns["choque"], ns["ramas"]
# El panel es una malla completa rama × mes: los desplazamientos por posición equivalen a desplazamientos por fecha.
assert P.groupby("rama").size().nunique() == 1 and (P.groupby("rama").mes.diff().dropna().dt.days.between(28, 31)).all()
P["s0"] = P.mes.map(choque); P["s1"] = (P.mes - pd.DateOffset(months=1)).map(choque)
H = list(range(-6, 13))
beta = {h: [] for h in H}
for r in ramas:
    d = P[P.rama == r].sort_values("mes").reset_index(drop=True)
    bs = {}
    for h in H:
        X = pd.DataFrame({"s0": d.s0, "s1": d.s1, "ip": d.d1_lip, "tc_l1": d.d1_ltc.shift(1), "vix_l1": d.d1_lvix.shift(1),
                          "y_l1": d.d1_l_produccion.shift(1), "ar": d.d1_arancel.shift(-h), "cov": d.d1_lcovid.shift(-h),
                          "d4": d["dum_2020-04"].shift(-h), "d5": d["dum_2020-05"].shift(-h), "d6": d["dum_2020-06"].shift(-h)})
        X = X.loc[:, X.notna().any()]                              # rama sin arancel (3328): se omite la columna
        y = d.d1_l_produccion.shift(-h)
        m = X.notna().all(axis=1) & y.notna()
        Xm = X[m].loc[:, X[m].nunique() > 1]
        if m.sum() < 30:
            bs = None; break
        bs[h] = sm.OLS(y[m], sm.add_constant(Xm)).fit().params["s0"]
    if bs is None:
        continue
    for h in H:
        beta[h].append(bs[h])
bm = {h: 100 * np.mean(v) for h, v in beta.items()}
cum = {h: (sum(bm[j] for j in range(0, h + 1)) if h >= 0 else (0.0 if h == -1 else -sum(bm[j] for j in range(h + 1, 0)))) for h in H}
irf = pd.read_csv("../../outputs/tables/irf_promedio_mensual_covid.csv")
ref = irf[(irf.variable == "produccion") & (irf.muestra == "completa")].set_index("h").respuesta
comp = pd.DataFrame({"verificacion_statsmodels": pd.Series(cum), "tabla_irf": ref})
comp["diferencia"] = comp.verificacion_statsmodels - comp.tabla_irf
print(f"ramas usadas: {len(beta[0])}")
print(comp.round(6).to_string())
print("Diferencia absoluta máxima:", comp.diferencia.abs().max())
print("β de h = −1 (con el rezago propio como control), promedio:", round(bm[-1], 10))
