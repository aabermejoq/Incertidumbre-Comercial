# Pronóstico mensual de la actividad industrial de México

Proyecto independiente para pronosticar con un mes de anticipación la **variación anual** del IMAI en cuatro sectores: manufacturas (`MANUF`), construcción (`CONST`), electricidad (`ELEC`) y minería (`MIN`). Se trabaja exclusivamente en variaciones anuales y con evaluación estrictamente fuera de muestra.

El proyecto es un solo documento RMarkdown que se desarrolla por entregas. Cada entrega se revisa y valida antes de pasar a la siguiente.

| Entrega | Contenido | Estado |
|---|---|---|
| 1 | Configuración, lectura y diagnóstico de datos | Lista para revisión |
| 2 | Construcción de variaciones anuales y transformaciones | Pendiente |
| 3 | Disponibilidad histórica y estrategia de información | Pendiente |
| 4 | Benchmarks y modelos econométricos | Pendiente |
| 5 | Machine learning, factores y combinaciones | Pendiente |
| 6 | Selección y pronósticos finales | Pendiente |

## Estructura

```
pronostico_actividad_industrial/
├── pronostico_actividad_industrial.Rmd   # documento único (código + metodología + resultados)
├── datos/base_imai.xlsx                  # libro de datos original (sin modificar)
└── resultados/01_diagnostico/            # tablas intermedias (CSV) y datos leídos (RDS)
```

## Ejecución

Desde esta carpeta, en R (≥ 4.2):

```r
rmarkdown::render("pronostico_actividad_industrial.Rmd")
```

También se puede ejecutar chunk por chunk en RStudio. Paquetes de la entrega 1: `readxl`, `dplyr`, `tidyr`, `purrr`, `tibble`, `stringr`, `lubridate`, `ggplot2`, `scales`, `patchwork`, `knitr`, `kableExtra`, `zoo`, `tseries`, `strucchange`. El documento no instala paquetes, salvo que se active `INSTALAR_FALTANTES <- TRUE`. La ejecución completa tarda alrededor de un minuto.

El HTML generado no se versiona (se reconstruye con el comando anterior).
