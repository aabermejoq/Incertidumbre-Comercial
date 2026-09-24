"""Descarga de FRED el índice de volatilidad CBOE (VIX, serie VIXCLS), diario,
tal como lo publica la fuente (sin agregar ni transformar).

Salida:
  data/raw/controles_macroeconomicos/fred_vix_diario.csv  observation_date, VIXCLS
"""
from pathlib import Path

import requests

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"
OUT = Path(__file__).resolve().parents[2] / "data" / "raw" / "controles_macroeconomicos"

r = requests.get(URL, timeout=60)
r.raise_for_status()
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "fred_vix_diario.csv").write_bytes(r.content)
lineas = r.text.strip().splitlines()
print(f"{len(lineas) - 1} observaciones, {lineas[1].split(',')[0]} a {lineas[-1].split(',')[0]}")
