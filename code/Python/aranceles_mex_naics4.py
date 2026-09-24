"""Descarga del Census (International Trade API) las importaciones de EE.UU.
desde México por NAICS a 4 dígitos y calcula la tasa arancelaria efectiva mensual.

Requiere la variable de entorno CENSUS_API.

Salidas:
  data/raw/aranceles/aranceles_mex_naics4.csv          formato largo: fecha, naics, valores y tasas
  data/interim/aranceles/tasa_efectiva_mex_naics4.csv  fecha x naics, aranceles / valor importado
"""
import os
from datetime import date
from pathlib import Path

import pandas as pd
import requests

URL = "https://api.census.gov/data/timeseries/intltrade/imports/naics"
MEXICO = "2010"
INICIO = 2013
DATA = Path(__file__).resolve().parents[2] / "data"
RAW = DATA / "raw" / "aranceles"
INTERIM = DATA / "interim" / "aranceles"

key = os.environ.get("CENSUS_API")
if not key:
    raise SystemExit("Falta la variable de entorno CENSUS_API")


def anio(a):
    params = {
        "get": "NAICS,NAICS_SDESC,CON_VAL_MO,DUT_VAL_MO,CAL_DUT_MO",
        "CTY_CODE": MEXICO,
        "COMM_LVL": "NA4",
        "time": str(a),
        "key": key,
    }
    r = requests.get(URL, params=params, timeout=120)
    if r.status_code == 204:  # año sin datos publicados
        return None
    r.raise_for_status()
    if "json" not in r.headers.get("Content-Type", ""):
        raise SystemExit(f"Respuesta inesperada del Census ({r.url.split('&key=')[0]}):\n{r.text[:300]}")
    filas = r.json()
    return pd.DataFrame(filas[1:], columns=filas[0])


df = pd.concat([d for a in range(INICIO, date.today().year + 1)
                if (d := anio(a)) is not None], ignore_index=True)

df = pd.DataFrame({
    "fecha": pd.to_datetime(df["time"]),
    "naics": df["NAICS"],
    "descripcion": df["NAICS_SDESC"],
    "valor_importado": pd.to_numeric(df["CON_VAL_MO"]),
    "valor_gravable": pd.to_numeric(df["DUT_VAL_MO"]),
    "aranceles": pd.to_numeric(df["CAL_DUT_MO"]),
})
df["tasa_efectiva"] = df["aranceles"] / df["valor_importado"].where(df["valor_importado"] > 0)
df["tasa_gravable"] = df["aranceles"] / df["valor_gravable"].where(df["valor_gravable"] > 0)
df = df.sort_values(["naics", "fecha"])

RAW.mkdir(parents=True, exist_ok=True)
INTERIM.mkdir(parents=True, exist_ok=True)
df.to_csv(RAW / "aranceles_mex_naics4.csv", index=False, date_format="%Y-%m-%d")
(df.pivot(index="fecha", columns="naics", values="tasa_efectiva")
   .to_csv(INTERIM / "tasa_efectiva_mex_naics4.csv", date_format="%Y-%m-%d", float_format="%.6f"))
print(f"{df['naics'].nunique()} ramas, {df['fecha'].min():%Y-%m} a {df['fecha'].max():%Y-%m}")
