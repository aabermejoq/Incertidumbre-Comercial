"""Descarga la producción industrial de EE.UU. (Fed, G.17) con ajuste estacional
y guarda las series por rama NAICS en CSV.

Salidas:
  data/ip_naics_sa.csv      fecha x serie, índice 2017=100
  data/ip_naics_series.csv  serie, descripción y código NAICS
"""
import re
from pathlib import Path

import pandas as pd
import requests

URL = "https://www.federalreserve.gov/releases/g17/ipdisk/ip_sa.txt"
OUT = Path(__file__).resolve().parent.parent / "data"

HEADER = re.compile(r'^"([^"]+): (.*?)\s+NAICS=(\S+)"')

txt = requests.get(URL, timeout=60).text
meta, rows = {}, []
for line in txt.splitlines():
    if (m := HEADER.match(line)):
        meta[m[1]] = (m[2].strip(), m[3])
    elif line.startswith('"') and ": " not in line:
        p = line.split()
        serie, anio = p[0].strip('"'), int(p[1])
        if serie in meta:
            for mes, v in enumerate(p[2:14], 1):
                rows.append((serie, pd.Timestamp(anio, mes, 1), float(v)))

ip = (pd.DataFrame(rows, columns=["serie", "fecha", "indice"])
        .pivot(index="fecha", columns="serie", values="indice")[list(meta)])
series = pd.DataFrame([(s, d, n) for s, (d, n) in meta.items()],
                      columns=["serie", "descripcion", "naics"])

OUT.mkdir(exist_ok=True)
ip.to_csv(OUT / "ip_naics_sa.csv", date_format="%Y-%m-%d", float_format="%.4f")
series.to_csv(OUT / "ip_naics_series.csv", index=False)
print(f"{ip.shape[1]} series, {ip.index.min():%Y-%m} a {ip.index.max():%Y-%m}")
