# Notas metodológicas iniciales

Este documento reúne observaciones de la inspección inicial de las fuentes (etapa 1: organización e inventario). Aquí solo se anotan hechos comprobados en los archivos y preguntas abiertas. Todavía no se ha tomado **ninguna** decisión de limpieza, homologación ni modelación. Los identificadores (`MX_PROD_01`, `INC_02`, etc.) corresponden a [`inventario_fuentes.csv`](inventario_fuentes.csv).

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

- El periodo común a **todas** las fuentes está limitado por las exportaciones, que empiezan en 2019-01, y termina en 2026-07. Si solo se usan producción y aranceles, el periodo común empieza en 2018-01. Qué periodo usar se decidirá más adelante.
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

- **Producción mexicana:** la EMIM trae **valor** de producción y de ventas en miles de pesos corrientes, más personal ocupado y horas trabajadas. No es un índice de volumen físico ni viene desestacionalizada. Si se necesita producción real habrá que decidir cómo deflactar u obtener otra serie (por ejemplo, el índice de volumen físico de la actividad industrial de INEGI), que no está en el repositorio.
- **Exportaciones mexicanas frente a importaciones de EE.UU. desde México:** `MX_EXP_01` son exportaciones totales de México (el archivo no dice el destino). `MX_ARAN_01` son importaciones de EE.UU. con origen México, en dólares. Miden flujos relacionados pero no idénticos (destinos, registro, valoración, fechas de registro).
- **Tasa arancelaria efectiva:** es aranceles calculados / valor importado. Las cuotas compensatorias podrían no estar incluidas en los aranceles calculados (por confirmar). En las ramas 1119 y 3119 los aranceles llegan a superar el valor gravable, lo que es compatible con aranceles específicos (por kilo) como los del azúcar. Hay un pico aislado de 49% en 1119 en diciembre de 2024.
- **Tres medidas de incertidumbre con alcances distintos:**
  - TPU (`INC_01`): incertidumbre de **política comercial** en prensa **estadounidense**; un solo índice agregado.
  - WTUI (`INC_02`, hoja T6): incertidumbre **comercial** por **país** (incluye MEX y USA), basada en reportes de la EIU. El mismo archivo trae la WUI (general) y la WPUI (política).
  - EPU México (`INC_03`): incertidumbre de **política económica** en general (no solo comercial) para México.

  Sus escalas y metodologías difieren. No se ha comprobado cuál o cuáles se usarán.

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

## 6. Fuentes de EE.UU. y posibles usos (sin decidir)

- La producción industrial de EE.UU. (`US_PROD_01`) podría servir como control de demanda externa o como fuente complementaria por rama. Primero hay que construir la correspondencia NAICS–SCIAN.
- La WTUI trae series para MEX y USA, lo que permitiría comparar incertidumbre comercial en México y en EE.UU.

## 7. Preguntas pendientes

1. ¿Cuál es la fuente exacta del archivo de exportaciones (sistema de consulta, destino de las exportaciones y significado del código `Tipo de operación = 2`)?
2. ¿De dónde vienen y cómo se construyeron las series de la hoja `Autopartes` (`xparts`, `inpp336`, `xparts_r_ae`)?
3. ¿La variable de producción será el valor de producción de la EMIM (nominal) o un índice de volumen de otra fuente todavía no incluida?
4. ¿Se usarán solo las ramas manufactureras (31-33) o también otras actividades industriales (minería, electricidad, construcción)? Las fuentes actuales de producción mexicana solo cubren manufacturas.
5. ¿Cuáles son las «tres medidas de incertidumbre comercial» del proyecto: TPU, WTUI y EPU México? La EPU no es específicamente comercial.
6. ¿Cómo tratar las ramas con datos confidenciales (`ND`) y las clases de exportación que no están en la EMIM?
7. ¿Qué deflactores y qué método de ajuste estacional se usarán, en su caso?
8. ¿Se incorporarán otros controles macroeconómicos (actividad, tasas de interés, precios) que hoy no están en el repositorio?
