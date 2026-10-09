"""Efecto acumulado a 12 meses por rama, con valor p de permutación y q de Benjamini-Hochberg.

Efecto de la rama = Σ_{h=0..12} β_h (nivel en t+12 respecto a t−1, en %, ante una sorpresa del TPU de 1 desv. est.),
con la especificación elegida (variaciones mensuales, controles de pandemia). Valor p: proporción de las 1,000 sorpresas
permutadas con |efecto| ≥ |efecto real| (prueba del efecto ACUMULADO, no de cada horizonte). q: valor p ajustado por
Benjamini-Hochberg dentro de cada variable y muestra (86 pruebas simultáneas).

Uso (desde code/Python):  python 07_efectos_por_rama.py      Salida: outputs/tables/efecto_12m_por_rama.csv
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

def bh(p):
    p = np.asarray(p, float); n = len(p); orden = np.argsort(p); q = np.empty(n); m = 1.0
    for rango, i in reversed(list(enumerate(orden, start=1))):
        m = min(m, p[i] * n / rango); q[i] = m
    return q

eleg = pd.read_csv(RAIZ / "outputs/tables/especificaciones_resumen_mensual_covid.csv")
eleg = eleg[eleg.elegida]
filas = []
for _, e in eleg.iterrows():
    df, _ = ns["estimar"](e.variable, e.especificacion, e.muestra == "sin pandemia", None)
    N = np.vstack(df.nulos.values)
    df["ee"] = N.std(axis=1)
    df["p"] = [float(np.mean(np.abs(n) >= abs(b))) for n, b in zip(df.nulos, df.sens)]
    df["q_bh"] = bh(df.p)
    filas.append(df[["rama", "sens", "ee", "p", "q_bh"]].rename(columns={"sens": "efecto_12m"})
                 .assign(variable=e.variable, muestra=e.muestra, especificacion=e.especificacion))
    print(e.variable, e.muestra, "| ramas con p < 0.10:", int((df.p < 0.10).sum()), "| con q < 0.10:", int((df.q_bh < 0.10).sum()), flush=True)
out = pd.concat(filas).merge(info, left_on="rama", right_index=True, how="left", validate="many_to_one")
out = out[["variable", "muestra", "especificacion", "rama", "rama_nombre", "coef_exportacion", "efecto_12m", "ee", "p", "q_bh"]]
out.to_csv(RAIZ / "outputs/tables/efecto_12m_por_rama.csv", index=False)
print("Guardado: outputs/tables/efecto_12m_por_rama.csv")
