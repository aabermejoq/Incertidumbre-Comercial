"""Descarga de FRED la producción industrial total de EE.UU. (INDPRO) y la de
manufactura (IPMAN), mensuales con ajuste estacional, índice 2017=100, tal como
las publica la fuente (Federal Reserve Board, G.17), sin transformarlas.

Salidas:
  data/raw/produccion_estados_unidos/fred_indpro_mensual.csv  observation_date, INDPRO
  data/raw/produccion_estados_unidos/fred_ipman_mensual.csv   observation_date, IPMAN
"""
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / "data" / "raw" / "produccion_estados_unidos"
SERIES = {"INDPRO": "fred_indpro_mensual.csv", "IPMAN": "fred_ipman_mensual.csv"}

OUT.mkdir(parents=True, exist_ok=True)
for serie, archivo in SERIES.items():
    r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={serie}", timeout=60)
    r.raise_for_status()
    (OUT / archivo).write_bytes(r.content)
    lineas = r.text.strip().splitlines()
    print(f"{serie}: {len(lineas) - 1} observaciones, {lineas[1].split(',')[0]} a {lineas[-1].split(',')[0]}")
