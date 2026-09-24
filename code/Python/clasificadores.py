"""Descarga los clasificadores oficiales usados para verificar la correspondencia
SCIAN 2018 (INEGI) = NAICS (Census) a nivel de rama (4 dígitos) y subsector (3 dígitos).

No transforma los archivos. Solo usa la biblioteca estándar.

Salidas (data/raw/clasificadores/):
  inegi_scian_2018_categorias.xlsx           catálogo SCIAN 2018; la marca "T" al final del
                                             título indica categoría trilateral (MX, EE.UU., CAN)
  census_naics_2017_codigos.xlsx             códigos NAICS 2017 de 2 a 6 dígitos
  census_naics_2022_codigos.xlsx             códigos NAICS 2022 de 2 a 6 dígitos
  census_concordancia_naics_2022_2017.xlsx   concordancia NAICS 2022 -> 2017
  census_concordancia_naics_2017_2012.xlsx   concordancia NAICS 2017 -> 2012
"""
from pathlib import Path
from urllib.request import urlopen

OUT = Path(__file__).resolve().parents[2] / "data" / "raw" / "clasificadores"
ARCHIVOS = {
    "inegi_scian_2018_categorias.xlsx":
        "https://www.inegi.org.mx/contenidos/app/scian/scian_2018_categorias_y_productos.xlsx",
    "census_naics_2017_codigos.xlsx":
        "https://www.census.gov/naics/2017NAICS/2-6%20digit_2017_Codes.xlsx",
    "census_naics_2022_codigos.xlsx":
        "https://www.census.gov/naics/2022NAICS/2-6%20digit_2022_Codes.xlsx",
    "census_concordancia_naics_2022_2017.xlsx":
        "https://www.census.gov/naics/concordances/2022_to_2017_NAICS.xlsx",
    "census_concordancia_naics_2017_2012.xlsx":
        "https://www.census.gov/naics/concordances/2017_to_2012_NAICS.xlsx",
}

OUT.mkdir(parents=True, exist_ok=True)
for nombre, url in ARCHIVOS.items():
    with urlopen(url, timeout=120) as r:
        contenido = r.read()
    (OUT / nombre).write_bytes(contenido)
    print(f"{nombre}: {len(contenido):,} bytes")
