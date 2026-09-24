# Notas metodológicas iniciales

Este documento reúne observaciones de la inspección inicial de las fuentes (etapa 1: organización e inventario). Aquí se anotan hechos comprobados en los archivos, las decisiones que ya se acordaron (sección 0) y las preguntas abiertas. Todavía no se ha aplicado ninguna transformación a los datos. Los identificadores (`MX_PROD_01`, `INC_02`, etc.) corresponden a [`inventario_fuentes.csv`](inventario_fuentes.csv).

## 0. Decisiones acordadas

Registradas el 2026-09-24, con base en las respuestas del responsable del proyecto.

1. **Exportaciones:** `MX_EXP_01` proviene del cubo de información de comercio exterior (Comext) del Banco de México; `Tipo de operación = 2` corresponde a exportaciones.
2. **Variable de producción:** se usará el **valor real** de la producción de la EMIM, es decir, el valor de producción deflactado con el INPP (`PRECIOS_01`). Como el INPP solo llega a subsector (3 dígitos), cada rama se deflacta con el índice de su subsector. La asignación está en [`correspondencia_rama_inpp.csv`](correspondencia_rama_inpp.csv): 86 ramas, 21 subsectores, todas con correspondencia exacta a 3 dígitos.
3. **Cobertura sectorial:** solo industrias manufactureras (SCIAN 31-33). Los códigos no manufactureros del Census (11xx, 21xx y 9xxx) quedan fuera.
4. **Medidas de incertidumbre:** se usarán las tres: TPU (`INC_01`), WTUI (`INC_02`, hoja T6) y EPU México (`INC_03`).
5. **Datos confidenciales (`ND`) y faltantes:** se tratarán como valores faltantes. El análisis final usará solo información completa.
6. **Periodo:** la información completa empieza en 2019-01 (límite de las exportaciones). Los ceros de 1991 del tipo de cambio quedan fuera de ese periodo y no requieren tratamiento.
7. **Anomalías arancelarias** en las ramas 1119 y 3119: no requieren tratamiento especial (la 1119 queda fuera por no ser manufacturera).
8. **Control de incertidumbre financiera global:** se incorpora el VIX (`MACRO_02`, FRED/CBOE). Otros controles (tipo de cambio real, TIIE) quedan pendientes de instrucciones.

Registradas el 2026-09-24, al revisar el R Markdown de integración (`code/R/01_preparacion_base_integrada.Rmd`):

9. **Periodo del panel:** las filas mes-rama empiezan en 2018-01 (EMIM). Los datos del Census de 2013-2017 no forman filas del panel; quedan documentados en la hoja `cobertura` del Excel.
10. **Correspondencia NAICS = SCIAN:** se verificó con clasificadores oficiales (`data/raw/clasificadores/`, descargados con `code/Python/clasificadores.py`). Las 86 ramas y los 21 subsectores manufactureros del SCIAN 2018 son categorías trilaterales (marca «T»). Sus códigos coinciden con NAICS 2017 y 2022, y ninguna clase manufacturera cambió de rama ni de subsector entre NAICS 2012, 2017 y 2022. El R Markdown repite esta verificación y solo asigna datos del Census y del G.17 a ramas verificadas.
11. **Control agregado de EE.UU.:** se incorporará aparte, porque el G.17 del repositorio no trae el total nacional.
12. **Incertidumbre comercial:** se usan las tres WTUI: México, EE.UU. y el promedio mundial ponderado por PIB.
13. **VIX:** se convierte a mensual con el promedio de los días con dato.
14. **Unidades monetarias:** todas se expresan también en miles de pesos reales de julio de 2019, deflactadas con el INPP del subsector. Los dólares se convierten antes con el FIX promedio del mes. Se conservan las variables nominales originales.

## 1. Cobertura temporal y frecuencia

| Fuente | Frecuencia | Inicio | Fin |
|---|---|---|---|
| MX_PROD_01 – EMIM (INEGI) | Mensual | 2018-01 | 2026-07 |
| MX_EXP_01 – Exportaciones por SCIAN | Mensual | 2019-01 | 2026-07 |
| MX_ARAN_01 / 02 – Aranceles EE.UU. a México (Census) | Mensual | 2013-01 | 2026-07 |
| US_PROD_01 – Producción industrial EE.UU. (Fed G.17) | Mensual | 1919-01 (varía por serie; hasta 2002) | 2026-08 |
| INC_01 – TPU (Caldara et al.) | Mensual / trimestral / diaria | 1960-01 (diaria: 2015-01-01) | 2026-08 (trim.: 2026Q2; diaria: 2026-09-21) |
| INC_02 – WUI / WTUI / WPUI (Ahir, Bloom y Furceri) | Mensual | 2008-01 | 2026-08 |
| INC_03 – EPU México (Baker, Bloom y Davis) | Mensual | 1996-01 | 2026-08 |
| MACRO_01 – Tipo de cambio FIX (Banxico) | Mensual | 1991-11 | 2026-08 |
| MACRO_02 – VIX (CBOE vía FRED) | Diaria | 1990-01-02 | 2026-09-22 |
| PRECIOS_01 – INPP por origen (INEGI) | Mensual | 1981-01 o 2010-06 (subsectores manufactureros) | 2026-08 |

- El periodo común a **todas** las fuentes va de 2019-01 (inicio de las exportaciones) a 2026-07. Este es el periodo con información completa (decisión 6).
- Casi todas las fuentes son mensuales. El TPU trae además versiones trimestral y diaria, y `TARIFFVOL` (volatilidad arancelaria) solo llega a 2018Q4.
- La EMIM tiene cifras preliminares desde agosto de 2025 y revisadas de enero a julio de 2025. Los últimos meses de exportaciones y aranceles también podrían revisarse.

## 2. Clasificaciones y niveles de desagregación

- **SCIAN (México) frente a NAICS (EE.UU.).** La EMIM y las exportaciones usan SCIAN; el Census y el G.17 usan NAICS. Los códigos de 4 dígitos se parecen mucho, pero no se ha verificado que las definiciones coincidan en cada rama.
- **EMIM y exportaciones:** las 86 ramas de 4 dígitos coinciden exactamente. A 6 dígitos, 198 de las 279 clases de exportación aparecen en la EMIM (que tiene 206 clases); las otras 81 clases de exportación no están en la EMIM.
- **EMIM y Census:** las 85 ramas manufactureras (código 3xxx) del Census están en la EMIM; la rama 3328 de la EMIM no aparece en el Census. El Census incluye además 23 códigos no manufactureros: agropecuarios (11xx), mineros (21xx) y códigos especiales 9100–9900 (probablemente mercancías devueltas, desperdicios u otras categorías sin rama industrial; por confirmar).
- **G.17 (EE.UU.):** los códigos NAICS son heterogéneos (de 2 a 6 dígitos, rangos como `3361-3`, listas como `3333,9` y partes de industria marcadas `pt.`). Hará falta una tabla de correspondencia para relacionarlos con ramas SCIAN.
- **Agregados junto con detalle:** la EMIM mezcla en la misma tabla el total manufacturero (31-33), los subsectores, las ramas y las clases. Al agregar hay que evitar contar dos veces.
- En el archivo de exportaciones, la columna llamada `Clase` en realidad contiene la **rama** (4 dígitos), y `SCIAN` contiene la clase (6 dígitos).

## 3. Conceptos que parecen similares pero no son iguales

- **Producción mexicana:** la EMIM trae **valor** de producción y de ventas en miles de pesos corrientes, más personal ocupado y horas trabajadas. No es un índice de volumen físico ni viene desestacionalizada. Se deflactará con el INPP por subsector (decisión 2).
- **Exportaciones mexicanas frente a importaciones de EE.UU. desde México:** `MX_EXP_01` son exportaciones totales de México (el archivo no dice el destino). `MX_ARAN_01` son importaciones de EE.UU. con origen México, en dólares. Miden flujos relacionados pero no idénticos (destinos, registro, valoración, fechas de registro).
- **Tasa arancelaria efectiva:** es aranceles calculados / valor importado. Las cuotas compensatorias podrían no estar incluidas en los aranceles calculados (por confirmar). En las ramas 1119 y 3119 los aranceles llegan a superar el valor gravable, lo que es compatible con aranceles específicos (por kilo) como los del azúcar. Hay un pico aislado de 49% en 1119 en diciembre de 2024.
- **Tres medidas de incertidumbre con alcances distintos:**
  - TPU (`INC_01`): incertidumbre de **política comercial** en prensa **estadounidense**; un solo índice agregado.
  - WTUI (`INC_02`, hoja T6): incertidumbre **comercial** por **país** (incluye MEX y USA), basada en reportes de la EIU. El mismo archivo trae la WUI (general) y la WPUI (política).
  - EPU México (`INC_03`): incertidumbre de **política económica** en general (no solo comercial) para México.

  Sus escalas y metodologías difieren. Se usarán las tres (decisión 4).

## 4. Unidades y monedas

- EMIM: miles de pesos corrientes (producción y ventas), número de personas y miles de horas.
- Exportaciones: pesos y dólares. En la hoja `Datos`, el cociente pesos/dólares da una mediana anual de 17.5 a 21.7, cerca del tipo de cambio de mercado; habría que compararlo con `MACRO_01`. Algunos valores en pesos están redondeados a pocas cifras significativas.
- Aranceles (Census): dólares corrientes.
- G.17: índice (2017=100 según el script de descarga; por confirmar).
- Índices de incertidumbre: cada uno tiene su propia normalización. En la WUI, las hojas F1 a F3 (promedios ponderados) tienen una escala distinta a la de las series por país.

## 5. Particularidades de formato que afectarán la lectura

- **EMIM:** 6 filas de encabezado, encabezado doble (año y mes en texto), las 4 variables apiladas en vertical y notas al pie. Las columnas de agosto a diciembre de 2026 traen `-` (aún no publicadas) y hay 184 celdas `ND` (datos confidenciales) en 326211, 3343, 334310, 335110 y 336991.
- **Exportaciones:** las hojas `TD` (tabla dinámica) y `Autopartes` las elaboró el usuario; no son datos originales. En `Autopartes`, `xparts` no coincide con la suma de la rama 3363 de la hoja `Datos` (ni en pesos ni en dólares), así que su origen está por revisar. `inpp336` vale 100 en julio de 2019 y parece un índice de precios al productor. `xparts_r_ae` parece estar desestacionalizada, con un método no documentado.
- **Tipo de cambio:** 18 filas de metadatos. De enero a octubre de 1991 la serie trae 0, que deben tratarse como faltantes.
- **EPU México:** `Year` es texto y la última fila es una nota de fuente.
- **TPU:** la hoja ReadMe dice que la cobertura es 1985–2020, pero los datos van de 1960 a 2026.
- **WUI:** muchas celdas en 0 en las series por país.

- **INPP:** el título de las series dice «Base Julio 2025=100», pero las 43 series valen exactamente 100 en **julio de 2019** y entre 108 y 176 en julio de 2025. La base efectiva es julio de 2019=100. Esto no afecta la deflactación (solo cambia el nivel), pero conviene confirmarlo y citar la base correcta.
- **INPP, cobertura conceptual:** el archivo contiene el INPP de *mercancías y servicios finales* por origen, que excluye bienes intermedios. El valor de producción de la EMIM incluye bienes que otras industrias usan como insumos, así que la cobertura de precios no coincide exactamente.
- **INPP, ramas que comparten deflactor:** en 312 (bebidas y tabaco), 336 (vehículos, carrocerías, autopartes y otro equipo de transporte) y 311 (nueve ramas alimentarias), ramas con precios muy distintos comparten índice. Las diferencias de precios dentro de cada subsector quedarán en la producción real.

## 6. Fuentes de EE.UU. y posibles usos (sin decidir)

- La producción industrial de EE.UU. (`US_PROD_01`) podría servir como control de demanda externa o como fuente complementaria por rama. Primero hay que construir la correspondencia NAICS–SCIAN.
- La WTUI trae series para MEX y USA, lo que permitiría comparar incertidumbre comercial en México y en EE.UU.

## 7. Preguntas pendientes

1. ¿De dónde vienen y cómo se construyeron las series de la hoja `Autopartes` (`xparts`, `inpp336`, `xparts_r_ae`)?
2. ¿Hay que confirmar con INEGI la base del INPP (julio de 2019 frente a julio de 2025)? ¿Vale la pena conseguir el INPP de *producción total* (que incluye bienes intermedios) como deflactor alternativo?
3. ¿Qué método de ajuste estacional se usará, si se usa alguno?
4. ¿Qué otros controles macroeconómicos se incorporarán, además del tipo de cambio nominal y el VIX? (La regla del VIX ya se acordó: promedio mensual.)
5. ¿Cómo se tratarán las clases de exportación que no están en la EMIM al agregar a nivel rama? Las 86 ramas coinciden, así que agregar por rama las incluye.
