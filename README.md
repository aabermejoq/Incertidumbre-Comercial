# Impacto de la incertidumbre comercial sobre la producción industrial de México por rama de actividad económica

## Descripción

El proyecto estudia cómo se relaciona la incertidumbre comercial con la dinámica de la producción industrial de México, desagregada por rama de actividad económica. La pregunta de investigación es si los episodios de mayor incertidumbre sobre la política comercial, en particular la de Estados Unidos, se asocian con cambios en la producción de las ramas industriales mexicanas, y si esa relación difiere entre ramas.

Para ello se combinarán información por rama económica (producción, exportaciones y aranceles), medidas de incertidumbre comercial y de política económica, y variables macroeconómicas de control. El proyecto todavía no tiene resultados: no se ha estimado ningún modelo.

## Objetivo y etapas del proyecto

El trabajo está organizado en seis etapas:

1. **Organización e inventario de las fuentes de información.** *(etapa actual)*
2. Inspección, limpieza y validación individual de las fuentes.
3. Homologación e integración de la base de datos.
4. Análisis exploratorio y revisión de la cobertura.
5. Desarrollo y estimación del modelo econométrico.
6. Evaluación de robustez e interpretación de resultados.

Hasta ahora solo se ha trabajado en la etapa 1. Las etapas 2 a 6 no se han iniciado.

## Fuentes de información

La tabla resume las fuentes que hay en el repositorio. El detalle de cada archivo (hojas, dimensiones, variables, advertencias, relaciones entre fuentes y huella SHA-256) está en [`docs/inventario_fuentes.csv`](docs/inventario_fuentes.csv). Las observaciones que pueden afectar la limpieza están en [`docs/notas_metodologicas.md`](docs/notas_metodologicas.md).

### Producción industrial

| ID | Archivo | Contenido | Fuente | Periodo | Frecuencia | Desagregación |
|---|---|---|---|---|---|---|
| MX_PROD_01 | `data/raw/produccion_mexico/inegi_emim_valores_rama_mensual.xlsx` | EMIM serie 2018: personal ocupado, horas trabajadas, valor de producción y valor de ventas (miles de pesos corrientes) | INEGI | 2018-01 a 2026-07 | Mensual | Manufacturas SCIAN: sector, 21 subsectores, 86 ramas, 206 clases |
| US_PROD_01 | `data/raw/produccion_estados_unidos/ip_naics_sa.csv` | Índices de producción industrial con ajuste estacional (231 series) | Federal Reserve Board, G.17 | 1919-01 a 2026-08 (el inicio varía por serie) | Mensual | NAICS mixto (de 2 a 6 dígitos, rangos y partes de industria) |
| US_PROD_02 | `data/raw/produccion_estados_unidos/ip_naics_series.csv` | Catálogo de las series de US_PROD_01 | Federal Reserve Board, G.17 | — | — | Serie G.17 |

### Comercio exterior

| ID | Archivo | Contenido | Fuente | Periodo | Frecuencia | Desagregación |
|---|---|---|---|---|---|---|
| MX_EXP_01 | `data/raw/exportaciones/exportaciones_mex_scian_mensual.xlsx` | Valor de las exportaciones mexicanas en pesos y dólares; incluye una tabla dinámica y una hoja de trabajo sobre autopartes | Banco de México, cubo de comercio exterior (Comext) | 2019-01 a 2026-07 | Mensual | 279 clases SCIAN (6 dígitos) en 86 ramas |

### Aranceles

| ID | Archivo | Contenido | Fuente | Periodo | Frecuencia | Desagregación |
|---|---|---|---|---|---|---|
| MX_ARAN_01 | `data/raw/aranceles/aranceles_mex_naics4.csv` | Importaciones de EE.UU. desde México: valor importado, valor gravable, aranceles calculados y tasas | U.S. Census Bureau, International Trade API | 2013-01 a 2026-07 | Mensual | 108 ramas NAICS de 4 dígitos |
| MX_ARAN_02 | `data/interim/aranceles/tasa_efectiva_mex_naics4.csv` | Matriz fecha × rama de la tasa arancelaria efectiva (derivada de MX_ARAN_01) | Derivado del Census | 2013-01 a 2026-07 | Mensual | 108 ramas NAICS de 4 dígitos |

### Precios (deflactores)

| ID | Archivo | Contenido | Fuente | Periodo | Frecuencia | Desagregación |
|---|---|---|---|---|---|---|
| PRECIOS_01 | `data/raw/precios/inegi_inpp_origen_scian_mensual.xlsx` | Índice Nacional de Precios Productor, mercancías y servicios finales por origen (base efectiva julio de 2019=100) | INEGI | 1981-01 a 2026-08 (subsectores: desde 1981-01 o 2010-06) | Mensual | Sectores SCIAN y 21 subsectores manufactureros |

### Incertidumbre

| ID | Archivo | Contenido | Fuente | Periodo | Frecuencia | Desagregación |
|---|---|---|---|---|---|---|
| INC_01 | `data/raw/incertidumbre/tpu_caldara_iacoviello.xlsx` | Índice de incertidumbre de política comercial (TPU), construido con prensa de EE.UU. | Caldara, Iacoviello et al. (Federal Reserve Board) | 1960-01 a 2026-08 | Mensual, trimestral y diaria (desde 2015) | Agregado (EE.UU.) |
| INC_02 | `data/raw/incertidumbre/wui_ahir_bloom_furceri_2026_08.xlsx` | World Uncertainty Index (general, comercial y de política) y conteos de palabras | Ahir, Bloom y Furceri | 2008-01 a 2026-08 | Mensual | 71 países (incluye MEX y USA) y promedio mundial |
| INC_03 | `data/raw/incertidumbre/epu_mexico_baker_bloom_davis.xlsx` | Índice de incertidumbre de política económica para México, basado en noticias | Baker, Bloom y Davis (PolicyUncertainty.com) | 1996-01 a 2026-08 | Mensual | Nacional |

### Controles macroeconómicos

| ID | Archivo | Contenido | Fuente | Periodo | Frecuencia | Desagregación |
|---|---|---|---|---|---|---|
| MACRO_01 | `data/raw/controles_macroeconomicos/banxico_tipo_cambio_fix_mensual.xlsx` | Tipo de cambio FIX, pesos por dólar, promedio mensual (SF17908) | Banco de México | 1991-11 a 2026-08 | Mensual | Nacional |
| MACRO_02 | `data/raw/controles_macroeconomicos/fred_vix_diario.csv` | VIX: volatilidad implícita del S&P 500 (incertidumbre financiera global) | CBOE, vía FRED (VIXCLS) | 1990-01-02 a 2026-09-22 | Diaria | Agregado (EE.UU.) |

**Relaciones preliminares entre fuentes (sin verificar su compatibilidad):**
- La EMIM y las exportaciones tienen las mismas 86 ramas SCIAN de 4 dígitos.
- Las ramas manufactureras del Census (NAICS) coinciden en código con las de la EMIM, salvo la 3328.
- El G.17 requerirá una tabla de correspondencia hacia ramas SCIAN.

Hay dos diferencias conceptuales importantes:
- La EMIM reporta valores nominales, no un índice de volumen.
- Las exportaciones mexicanas y las importaciones de EE.UU. desde México son flujos distintos.

Ver las [notas metodológicas](docs/notas_metodologicas.md).

## Estructura del repositorio

```
.
├── README.md
├── data/
│   ├── raw/                              Datos originales, sin modificar
│   │   ├── produccion_mexico/            EMIM (INEGI)
│   │   ├── exportaciones/                Exportaciones por SCIAN
│   │   ├── aranceles/                    Importaciones y aranceles de EE.UU. desde México (Census)
│   │   ├── produccion_estados_unidos/    Producción industrial de EE.UU. (G.17) y su catálogo
│   │   ├── incertidumbre/                TPU, WUI/WTUI/WPUI y EPU México
│   │   ├── precios/                      INPP por origen (deflactores)
│   │   └── controles_macroeconomicos/    Tipo de cambio FIX y VIX
│   ├── interim/                          Datos derivados o transformados
│   │   └── aranceles/                    Tasa efectiva en formato ancho
│   └── processed/                        (reservado) base integrada y validada
├── code/
│   ├── Python/                           Scripts de descarga (Census, G.17 y VIX)
│   └── R/                                01_preparacion_base_integrada.Rmd (limpieza, validación e integración)
├── docs/
│   ├── inventario_fuentes.csv            Inventario completo de archivos
│   ├── correspondencia_rama_inpp.csv     Deflactor INPP asignado a cada rama EMIM
│   └── notas_metodologicas.md            Observaciones de la inspección y preguntas abiertas
└── outputs/                              (reservado) resultados del análisis
    ├── tables/
    ├── figures/
    └── reports/
```

- **`data/raw/`** contiene los archivos tal como se recibieron o descargaron. No deben editarse. Los CSV de `aranceles/` y `produccion_estados_unidos/` los generan los scripts de `code/Python/` a partir de las API de origen.
- **`data/interim/`** guarda versiones transformadas de los datos originales. Por ahora solo contiene `tasa_efectiva_mex_naics4.csv`, que es una reorganización de `MX_ARAN_01`.
- **`data/processed/`**, **`code/R/`** y **`outputs/`** son espacios reservados para etapas posteriores y por ahora solo contienen un archivo `.gitkeep`.
- **`code/Python/`** contiene los scripts de descarga:
  - `aranceles_mex_naics4.py`: descarga del Census; requiere la variable de entorno `CENSUS_API`.
  - `ip_naics.py`: descarga del G.17.
  - `vix.py`: descarga del VIX diario de FRED.

## Decisiones acordadas

Se usará el **valor real de la producción manufacturera** (SCIAN 31-33) de la EMIM por rama. Para obtenerlo, el valor nominal se deflactará con el INPP del subsector al que pertenece cada rama; la asignación está en [`docs/correspondencia_rama_inpp.csv`](docs/correspondencia_rama_inpp.csv).

Las tres medidas de incertidumbre son TPU, WTUI y EPU México, y el VIX se usará como control de incertidumbre financiera global. Los valores confidenciales se tratarán como faltantes y el análisis usará información completa, que empieza en 2019-01.

El detalle está en la sección 0 de las [notas metodológicas](docs/notas_metodologicas.md).

## Estado actual del proyecto

| Actividad | Estado |
|---|---|
| Organización de los archivos | Completada |
| Inventario de fuentes | Completado (15 archivos: 12 de datos y 3 scripts) |
| Inspección de metadatos | Completada para los 12 archivos de datos: todas las hojas, dimensiones, encabezados, cobertura y códigos de clasificación. No se revisaron todas las celdas. |
| Correspondencia rama–deflactor | Completada (86 ramas → 21 subsectores INPP) |
| Limpieza de datos | Código listo: `code/R/01_preparacion_base_integrada.Rmd` (pendiente de ejecutar y revisar) |
| Integración de fuentes | Código listo: genera `data/processed/base_incertidumbre_comercial_mexico.xlsx` y el reporte HTML en `outputs/reports/` |
| Estimación econométrica | Pendiente |

## Próximos pasos

La siguiente etapa será la inspección y limpieza detallada de cada fuente, con énfasis en:
- las diferencias de fechas y cobertura, frecuencias, niveles de desagregación, unidades y definiciones;
- la correspondencia entre clasificaciones SCIAN y NAICS;
- el tratamiento de valores confidenciales, faltantes o preliminares;
- las preguntas abiertas en las notas metodológicas.

Después se buscará construir una base de datos para analizar la producción industrial de México por rama y su relación con las medidas de incertidumbre comercial. En ella se considerarán, según su disponibilidad y pertinencia, las exportaciones, los aranceles, la producción de Estados Unidos y los controles macroeconómicos. La especificación econométrica y el conjunto final de variables aún no están definidos.

## Uso y convenciones

- **Datos originales:** en `data/raw/<categoría>/`. No se modifican; cualquier transformación debe guardarse en `data/interim/` o `data/processed/`.
- **Documentación:** el inventario (`docs/inventario_fuentes.csv`) relaciona el identificador de cada fuente (`id_fuente`) con su nombre original, su ruta anterior y su ruta actual (`nombre_organizado`). También guarda la huella SHA-256 de cada archivo para verificar que no se haya modificado.
- **Nombres de archivo:** minúsculas, sin espacios ni acentos, con palabras separadas por guiones bajos, siguiendo el patrón `<institución o autor>_<contenido>_<frecuencia o versión>`. Los CSV generados por scripts conservan el nombre que les asignan sus scripts.
- **Identificadores de fuente:** `MX_PROD`, `MX_EXP`, `MX_ARAN`, `US_PROD`, `INC`, `MACRO`, `PRECIOS` y `COD`, seguidos de un número consecutivo.
- **Rutas:** todo el código debe usar rutas relativas a la raíz del repositorio (por ejemplo, `data/raw/incertidumbre/...`). Los scripts de Python calculan esa raíz a partir de su propia ubicación. En R se recomienda `here::here()` o un proyecto de RStudio (`.Rproj`) en la raíz.

### Archivos renombrados

| Nombre original | Ubicación actual |
|---|---|
| `EMIM.xlsx` | `data/raw/produccion_mexico/inegi_emim_valores_rama_mensual.xlsx` |
| `Exportaciones SCIAN.xlsx` | `data/raw/exportaciones/exportaciones_mex_scian_mensual.xlsx` |
| `tpu_web_latest.xlsx` | `data/raw/incertidumbre/tpu_caldara_iacoviello.xlsx` |
| `WUI_M_dataset_2026_08.xlsx` | `data/raw/incertidumbre/wui_ahir_bloom_furceri_2026_08.xlsx` |
| `Mexico_Policy_Uncertainty_Data (2).xlsx` | `data/raw/incertidumbre/epu_mexico_baker_bloom_davis.xlsx` |
| `TC.xlsx` | `data/raw/controles_macroeconomicos/banxico_tipo_cambio_fix_mensual.xlsx` |
| `INPP.xlsx` | `data/raw/precios/inegi_inpp_origen_scian_mensual.xlsx` |

Los CSV que estaban en `data/` y los scripts que estaban en `scripts/` se movieron sin cambiarles el nombre (ver el inventario).

## Citas de las fuentes de incertidumbre

- Ahir, H., Bloom, N. y Furceri, D. (2022). *World Uncertainty Index*. NBER Working Paper.
- Baker, S. R., Bloom, N. y Davis, S. J. (2016). Measuring Economic Policy Uncertainty. *Quarterly Journal of Economics*, 131(4).
- Caldara, D., Iacoviello, M., Molligo, P., Prestipino, A. y Raffo, A. (2020). The Economic Effects of Trade Policy Uncertainty. *Journal of Monetary Economics*, 109.
