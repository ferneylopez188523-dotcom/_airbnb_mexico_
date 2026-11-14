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


## Integrantes

| Integrante | Responsabilidad |
| --- | --- |
| (nombre) | Extracción y conexión MongoDB |
| (nombre) | Transformación de datos |
| Ferney López Copete | Análisis EDA y modelo |
| (nombre) | Documentación y tablero BI |

## Licencia

Proyecto académico — Inteligencia de Negocios
