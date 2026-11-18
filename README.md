## Integrantes

| Integrante | Responsabilidad |
| --- | --- |
| Santiago Varela | Extracción y Transformación de datos |
| Ferney López Copete | Análisis EDA y modelo |
| Leidy Melissa Trejos Pamplona | Documentación y tablero BI |
| José Ricardo Quirós | Modelado Predictivo con Aprendizaje Computacional |

## Licencia

Proyecto académico — Inteligencia de Negocios


# ETL Airbnb Ciudad de México

Proceso ETL (Extracción, Transformación, Carga) automatizado para los datasets de Airbnb de **Ciudad de México** (fuente: [Inside Airbnb](https://insideairbnb.com/get-the-data/)), desarrollado en Python.

Los datos se leen desde **MongoDB** o, si no está disponible, desde **archivos CSV**; se limpian con pandas, se cargan en **SQLite**.

```
 MongoDB ──┐                                        
           ├─> Extracción ─> Transformación ─> Carga ─> Exportación Excel/CSV
 CSV ──────┘               (limpieza+calidad)      
```

## Estructura del Proyecto

```
ETLCode-main/
├── data/                  # CSV de entrada + salidas del ETL
│   ├── listings.csv(.gz)  #   ┐
│   ├── reviews.csv(.gz)   #   ├ entrada (respaldo si no hay MongoDB)
│   ├── calendar.csv(.gz)  #   ┘
│   ├── airbnb.db          #   salida: base SQLite
│   ├── exports/           #   salida: tablas limpias en Excel/CSV
│   
├── src/
│   ├── config.py          # Rutas del proyecto y configuración única de logs
│   ├── extraccion.py      # Clase Extraccion (MongoDB, con respaldo en CSV)
│   ├── transformacion.py  # Clase Transformacion (limpieza, tipos, fechas, calidad)
│   ├── carga.py           # Clase Carga (SQLite + exportación + verificación)
│   ├── modelo_bi.py       # Clase ModeloBI (dimensiones y hechos para Power BI)
│   └── orquestador.py     # Ejecuta el pipeline completo
├── logs/                  # (se crea al ejecutar) un log por ejecución
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.10 o superior.
- **Una** de estas dos fuentes de datos:
  - **Opción A — CSV (la más simple):** copiar `listings`, `reviews` y `calendar` (`.csv` o `.csv.gz`) en la carpeta `data/`.
  - **Opción B — MongoDB:** base `airbnb_mx` con las colecciones `Listings`, `Reviews` y `Calendar`.

## Instalación

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```

La URI de MongoDB y el nombre de la base se cambian en `src/config.py`.

## Uso

### 1. Ejecutar el pipeline

Desde la raíz del proyecto (también funciona desde `src/`):

```bash
python src/orquestador.py
```

El orquestador ejecuta 4 fases:

| Fase | Qué hace |
|---|---|
| 1. Extracción | Intenta conectarse a MongoDB. Si no hay conexión o faltan colecciones, lee los CSV de `data/`. El log indica la fuente usada. |
| 2. Transformación | Limpieza, tipos de datos, fechas, rangos de precio y reporte de calidad. |
| 3. Carga | Tablas en `data/airbnb.db`, verificación de conteos y exportación a `data/exports/`. |
 

> Nota: el `calendar.csv.gz` completo de CDMX tiene millones de filas (un año por alojamiento); la ejecución puede tardar varios minutos.

### 2. Ejecutar el modelo predictivo

Abrir y ejecutar en orden `notebooks/02_modelado_predictivo_precio.ipynb`. El notebook
busca primero `data/airbnb.db`, después `data/listings.csv.gz` y, si ninguno existe,
descarga el corte oficial de Inside Airbnb usado en el proyecto. El entorno exacto con el
que se generaron los resultados se documenta en `requirements-model.txt`.

```bash
pip install -r requirements-model.txt
jupyter notebook notebooks/02_modelado_predictivo_precio.ipynb
```

Al finalizar se actualizan el modelo en `artifacts/` y las evidencias en `resultados/`.


## Componentes

**Extraccion**
- MongoDB con timeout de 5 segundos; si falla, lectura automática de CSV desde `data/`.
- Se detiene si una tabla no existe o está vacía (no se procesan datos incompletos).

**Transformacion**
- Eliminación de duplicados y de filas sin llave; textos vacíos → nulos.
- Booleanos `t/f` → `1/0`; porcentajes `"95%"` → `95.0`.
- Precios `"$1,234.00"` → `1234.0` (precios ≤ 0 → nulo).
- Fechas en `YYYY-MM-DD`; en Reviews y Calendar se derivan `anio`, `mes`, `dia`, `trimestre`.
- `price_rango`: Económico / Estándar / Alto / Premium por cuartiles del mercado.
- Listas (`amenities`, `host_verifications`) → texto separado por comas.
- Reporte de calidad (% de nulos por columna) en el log.

**Carga**
- Tablas en SQLite con tipos definidos y llave primaria.
- Verificación de conteos (registros en BD vs. registros transformados).
- Exportación a XLSX (o CSV si la tabla supera 500.000 filas).

## Logs

Un archivo por ejecución en `logs/etl_YYYYMMDD_HHMM.txt` (en la raíz del proyecto), con la fuente de datos usada, conteos por fase, reporte de calidad y errores.


## 5. Conclusiones y Recomendaciones

### 5.1. Conclusiones del análisis de datos e Inteligencia de Negocios

El proyecto permitió desarrollar una solución de análisis de datos e Inteligencia de Negocios para estudiar el comportamiento del mercado de alojamientos Airbnb en Ciudad de México. A través del proceso ETL, el análisis exploratorio y la implementación de dashboards interactivos en Power BI, se logró organizar y visualizar información relacionada con la oferta, los precios, la disponibilidad y las reseñas de los alojamientos.

A partir de los resultados obtenidos, se identificaron los siguientes hallazgos:

**1. Distribución de la oferta de alojamientos**

Se analizaron 30.468 alojamientos, de los cuales 20.348 corresponden a alojamientos completos y 9.770 a habitaciones privadas. Estos dos segmentos concentran la mayor parte de la oferta registrada, lo que evidencia su importancia dentro del mercado de Airbnb en Ciudad de México.

**2. Comportamiento de los precios**

El precio promedio registrado fue de 2.339,92, mientras que la mediana se ubicó aproximadamente en 1.500. Esta diferencia indica una distribución asimétrica de los precios, posiblemente influenciada por valores atípicos.

Adicionalmente, se identificaron diferencias entre los tipos de alojamiento. Las habitaciones de hotel registraron los precios promedio más elevados, mientras que las habitaciones compartidas presentaron los menores valores. Esto demuestra la importancia de analizar los precios según las características de cada segmento.

**3. Disponibilidad de los alojamientos**

El análisis de los datos del calendario permitió identificar un porcentaje general de disponibilidad del 67,92 %.

También se observaron variaciones entre los tipos de alojamiento y los períodos analizados. Las habitaciones de hotel presentaron una disponibilidad del 70,22 %, mientras que los alojamientos completos registraron un 59,35 %.

Estos resultados permiten estudiar patrones de disponibilidad publicada. Sin embargo, las fechas no disponibles no necesariamente representan reservas confirmadas, por lo que estos indicadores no deben interpretarse como tasas de ocupación real.

**4. Actividad de reseñas**

El análisis de reseñas permitió identificar diferencias en la actividad registrada según el tipo de alojamiento y la ubicación geográfica.

Los alojamientos completos concentraron una cantidad importante de las reseñas asociadas a los anuncios analizados. No obstante, el número de reseñas no representa directamente la satisfacción de los huéspedes ni permite determinar por sí solo la calidad del servicio.

**5. Inteligencia de Negocios**

La implementación de Power BI permitió desarrollar cuatro dashboards interactivos:

- Resumen ejecutivo.
- Análisis comercial.
- Análisis de disponibilidad.
- Análisis de reseñas.

Estas visualizaciones integran indicadores clave de desempeño (KPI), comparaciones, filtros y representaciones geográficas que facilitan la interpretación de los datos.

La solución permite apoyar decisiones de distintos actores organizacionales:

- **Directivos:** evaluación de la oferta y las características generales del mercado.
- **Área comercial:** comparación de precios, tipos de alojamiento y segmentos.
- **Área operativa:** monitoreo de disponibilidad y comportamiento temporal.
- **Análisis de mercado:** identificación de patrones de actividad de reseñas y distribución geográfica.

De esta manera, la Inteligencia de Negocios transforma los datos procesados en información útil para apoyar decisiones estratégicas y operativas.

### 5.2. Recomendaciones

A partir de los resultados del análisis, se proponen las siguientes recomendaciones:

**1. Fortalecer las estrategias de segmentación comercial**

Analizar los alojamientos según su ubicación, tipo, capacidad y categoría de precio para identificar oportunidades de diferenciación y orientar decisiones comerciales basadas en las características de cada segmento.

**2. Utilizar indicadores complementarios para evaluar los precios**

Considerar tanto el precio promedio como la mediana, debido a la presencia de valores extremos que pueden afectar la interpretación del mercado. También se recomienda revisar los registros con precios excepcionalmente altos para determinar su validez.

**3. Implementar un monitoreo periódico de disponibilidad**

Se puede aprovechar las visualizaciones temporales para identificar variaciones en la disponibilidad publicada y comparar su comportamiento por zona y tipo de alojamiento.

Lo cual puede contribuir a la planificación comercial y operativa, sin asumir que las fechas no disponibles corresponden necesariamente a reservas realizadas.

**4. Mejorar la calidad y consistencia de los datos**

Fortalecer los procesos de validación y limpieza, especialmente en registros con información faltante de ubicación, clasificación de precios y otras variables necesarias para el análisis.

**5. Complementar el análisis de reseñas**

Incorporar indicadores adicionales de valoración y satisfacción cuando los datos estén disponibles, con el propósito de complementar el análisis basado en la cantidad de reseñas.

**6. Mantener y actualizar la solución de BI**

Establecer procedimientos de actualización de datos, validación de indicadores y revisión de dashboards para conservar la utilidad de la solución en futuros análisis del mercado.

### 5.3. Conclusiones del modelo predictivo

Se desarrolló un modelo de regresión para estimar el precio publicado por noche de un
alojamiento. Se trabajó con 28.076 anuncios con precio positivo hasta el percentil 99
($13.476,25 MXN) y 18 variables físicas, geográficas, categóricas y operativas.

La evaluación se diseñó para evitar fuga de información: entrenamiento y prueba se
separaron por `host_id`, sin anfitriones compartidos, y la selección se realizó con
`GroupKFold` de cinco pliegues. Se compararon una línea base, Ridge, Random Forest e
HistGradientBoosting. Este último obtuvo el menor MAE y se ajustó mediante búsqueda
aleatoria de 12 configuraciones.

En 5.869 anuncios de prueba pertenecientes a anfitriones no vistos, el modelo final logró:

- MAE: **$646,87 MXN** (IC 95 %: $620,13–$677,97).
- RMSE: **$1.269,43 MXN**.
- R²: **0,491**.
- Error absoluto mediano: **$312,62 MXN**.
- MAPE: **31,30 %**.
- Reducción del MAE frente a la línea base: **40,0 %**.

Las variables con mayor importancia predictiva fueron el tipo de propiedad, el número de
baños, la capacidad, la ubicación y el número de habitaciones. El análisis por segmentos
mostró que el error aumenta de $245,00 en el cuartil económico a $1.621,80 en el cuartil
alto. El modelo no es confiable para habitaciones de hotel, ya que solo hubo 24 casos de
prueba y el MAE fue elevado.

El modelo debe utilizarse como referencia de mercado y no como precio automático. No
predice demanda, reservas, ocupación, ingresos ni causalidad. Los detalles completos se
encuentran en `notebooks/02_modelado_predictivo_precio.ipynb` y en
`docs/04_05_modelado_conclusiones.md`.

### 5.4. Conclusión general

Los resultados obtenidos hasta esta etapa demuestran la utilidad de integrar procesos de extracción, transformación, análisis y visualización de datos para comprender el mercado de alojamientos Airbnb en Ciudad de México.

La solución de Inteligencia de Negocios desarrollada permite identificar patrones de oferta, diferencias de precios, variaciones de disponibilidad y actividad de reseñas, proporcionando información relevante para apoyar la toma de decisiones de diferentes actores organizacionales.

La integración del análisis descriptivo, los dashboards y el modelo predictivo permite
pasar de comprender el mercado a estimar un precio de referencia para anuncios dentro del
rango habitual. La mejora del 40,0 % frente a la línea base demuestra utilidad, aunque el
error por segmentos exige revisión humana en alojamientos caros o poco frecuentes.

Como recomendación general, se propone incorporar la diferencia entre precio publicado y
precio estimado al dashboard, actualizar el modelo con cada corte trimestral y validar su
desempeño sobre un período futuro antes de cualquier uso operativo.


