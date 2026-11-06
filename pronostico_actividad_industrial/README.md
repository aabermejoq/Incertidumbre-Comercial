# Pronóstico mensual de la actividad industrial de México

Proyecto independiente para pronosticar con un mes de anticipación la **variación anual** del IMAI en cuatro sectores: manufacturas (`MANUF`), construcción (`CONST`), electricidad (`ELEC`) y minería (`MIN`). Se trabaja exclusivamente en variaciones anuales y con evaluación estrictamente fuera de muestra.

El proyecto es un solo documento RMarkdown que se desarrolla por entregas. Cada entrega se revisa y valida antes de pasar a la siguiente.

| Entrega | Contenido | Estado |
|---|---|---|
| 1 | Configuración, lectura y diagnóstico de datos | Validada |
| 2 | Construcción de variaciones anuales y transformaciones; prueba de la EMAER histórica | Validada |
| 3 | Disponibilidad histórica, benchmark auto.arima, contribución marginal y estrategia de información | Validada |
| 4 | Modelos econométricos frente a auto.arima (factores, ADL, selección en tiempo real, LASSO, Elastic Net, Ridge) | Lista para revisión |
| 5 | Machine learning, factores y combinaciones | Pendiente |
| 6 | Selección y pronósticos finales | Pendiente |

## Estructura

```
pronostico_actividad_industrial/
├── pronostico_actividad_industrial.Rmd       # documento único (código + metodología + resultados)
├── datos/
│   ├── base_imai.xlsx                        # libro original (sin modificar; sólo referencia)
│   └── base_imai_corregida.xlsx              # libro con las correcciones aprobadas (base del análisis)
├── herramientas/corregir_excel.py            # genera el libro corregido desde el original
└── resultados/
    ├── resultados_pronostico_imai.xlsx       # libro con todas las tablas de resultados
    ├── 01_diagnostico/                       # tablas del diagnóstico (CSV) y datos leídos (RDS)
    ├── 02_variables/                         # variables construidas, paneles por sector y prueba EMAER
    ├── 03_informacion/                       # benchmark, contribución marginal, estrategias y reconstrucción
    ├── 04_modelos/                           # pronósticos y métricas de los modelos econométricos
    └── cache/                                # cálculos costosos guardados (se reutilizan al ejecutar el Rmd)
```

## Libro corregido

`base_imai_corregida.xlsx` aplica las dos correcciones aprobadas en la entrega 1:

1. `CONST!SHCP1` desde 2011-07 apunta al total correcto (`'SHCP REAL'!B`); en el original copiaba otra serie con un desfase de 216 meses.
2. `ELEC` empieza en 1993-01 (antes, 1997-07), con fórmulas a las mismas hojas fuente; las series IMSS y ENOE conservan su inicio real.

Se generó editando directamente el XML del libro, para conservar sus conexiones de datos y vínculos externos:

```bash
python3 herramientas/corregir_excel.py datos/base_imai.xlsx datos/base_imai_corregida.xlsx
```

El Rmd verifica que no cambie nada más que esas celdas.

## Ejecución

Desde esta carpeta, en R (≥ 4.2):

```r
rmarkdown::render("pronostico_actividad_industrial.Rmd")
```

También se puede ejecutar chunk por chunk en RStudio. Paquetes: `readxl`, `dplyr`, `tidyr`, `purrr`, `tibble`, `stringr`, `lubridate`, `ggplot2`, `scales`, `patchwork`, `knitr`, `kableExtra`, `zoo`, `tseries`, `strucchange`, `writexl`, `forecast` y `glmnet`. El documento no instala paquetes, salvo que se active `INSTALAR_FALTANTES <- TRUE`. Con la caché de `resultados/cache` la ejecución completa tarda ≈1–2 minutos; sin ella (`USAR_CACHE <- FALSE`), ≈15 minutos con 3 núcleos y bastante más en Windows, donde no se paraleliza. El HTML generado no se versiona: se reconstruye con el comando anterior.
