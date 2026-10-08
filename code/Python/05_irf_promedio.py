"""IRF promedio de las ramas con la especificación elegida (variaciones mensuales, choque y controles de pandemia).

Respuesta del NIVEL respecto al mes previo al choque (t−1), en %: para h ≥ 0, Σ_{j=0..h} β_j; para h < 0, −Σ_{j=h+1..−1} β_j
(placebo, solo en la tabla). β_j = promedio de las ramas de la respuesta de Δ log y(t+j).
Error estándar = desviación estándar de la misma respuesta con 1,000 sorpresas permutadas. Gráfica: h = 0..12, bandas
simétricas al 68% (± 1 ee) y al 90% (± 1.645 ee) alrededor de la estimación. Valor p por permutación.

Uso (desde code/Python):  python 05_irf_promedio.py     (después: python 05b_graficas_irf.py)
Salida: outputs/tables/irf_promedio_mensual_covid.csv
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

