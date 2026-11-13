import logging
import sqlite3
from contextlib import closing
from pathlib import Path
import pandas as pd
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from config import DB_PATH, EXPORTS_DIR, configurar_logs


TIPOS_SQL = {
    "id": "INTEGER PRIMARY KEY",
    "listing_id": "INTEGER",
    "host_id": "INTEGER",
    "date": "TEXT",
    "price": "REAL",
    "adjusted_price": "REAL",
    "available": "INTEGER",
    "anio": "INTEGER",
    "mes": "INTEGER",
    "dia": "INTEGER",
    "trimestre": "INTEGER",
}

LIMITE_FILAS_XLSX = 500_000  # Tablas más grandes se exportan a CSV.
LIMITE_CELDA_XLSX = 32_767  # Máximo de caracteres por celda en Excel.


class Carga:
    """
    Clase encargada de cargar los DataFrames transformados a SQLite 
    y exportar a XLSX/CSV.
    """

    def __init__(self, dicc_dataframes: dict, db_path: Path = DB_PATH):
        self.dfs = dicc_dataframes
        self.db_path = Path(db_path)
        configurar_logs()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # SQLite
    # ------------------------------------------------------------------
    def _crear_tabla(self, conn: sqlite3.Connection, nombre: str, df: pd.DataFrame):
        columnas = []
        for col in df.columns:
            if col in TIPOS_SQL:
                tipo = TIPOS_SQL[col]
            elif pd.api.types.is_integer_dtype(df[col]) or pd.api.types.is_bool_dtype(df[col]):
                tipo = "INTEGER"
            elif pd.api.types.is_float_dtype(df[col]):
                tipo = "REAL"
            else:
                tipo = "TEXT"
            columnas.append(f'"{col}" {tipo}')

        conn.execute(f'DROP TABLE IF EXISTS "{nombre}"')
        conn.execute(f'CREATE TABLE "{nombre}" ({", ".join(columnas)})')

    def cargar_sqlite(self) -> dict:
        logging.info(f"--- INICIANDO CARGA A SQLite ({self.db_path}) ---")
        resultados = {}

        with closing(sqlite3.connect(self.db_path)) as conn:
            for nombre, df in self.dfs.items():
                try:
                    self._crear_tabla(conn, nombre, df)
                    # 'append' respeta el esquema que acabamos de crear.
                    df.to_sql(nombre, conn, if_exists="append", index=False, chunksize=10_000)
                    conn.commit()
                    resultados[nombre] = {"estado": "exito", "registros": len(df)}
                    logging.info(f"[{nombre}] {len(df):,} registros insertados en SQLite.")
                except Exception as e:
                    conn.rollback()
                    resultados[nombre] = {"estado": "error", "mensaje": str(e)}
                    logging.error(f"[{nombre}] Error al insertar en SQLite: {e}")

        return resultados

    def verificar_carga(self, tabla: str, esperados: int) -> bool:
        with closing(sqlite3.connect(self.db_path)) as conn:
            en_bd = conn.execute(f'SELECT COUNT(*) FROM "{tabla}"').fetchone()[0]
        ok = en_bd == esperados
        nivel = logging.INFO if ok else logging.ERROR
        logging.log(nivel, f"[{tabla}] Verificación: {en_bd:,} en BD vs {esperados:,} esperados -> "
                           f"{'OK' if ok else 'NO COINCIDE'}")
        return ok

    # ------------------------------------------------------------------
    # Exportación
    # ------------------------------------------------------------------
    @staticmethod
    def _limpiar_para_excel(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].map(
                lambda v: ILLEGAL_CHARACTERS_RE.sub("", v)[:LIMITE_CELDA_XLSX] if isinstance(v, str) else v
            )
        return df

    def exportar_archivos(self, ruta: Path = EXPORTS_DIR) -> dict:
        logging.info("--- INICIANDO EXPORTACIÓN ---")
        ruta = Path(ruta)
        ruta.mkdir(parents=True, exist_ok=True)
        resultados = {}

        for nombre, df in self.dfs.items():
            try:
                if len(df) > LIMITE_FILAS_XLSX:
                    salida = ruta / f"{nombre}.csv"
                    df.to_csv(salida, index=False, encoding="utf-8-sig")
                else:
                    salida = ruta / f"{nombre}.xlsx"
                    self._limpiar_para_excel(df).to_excel(salida, sheet_name=nombre[:31], index=False)
                resultados[nombre] = {"estado": "exito", "ruta": str(salida), "filas": len(df)}
                logging.info(f"[{nombre}] Exportado a {salida}")
            except Exception as e:
                resultados[nombre] = {"estado": "error", "mensaje": str(e)}
                logging.error(f"[{nombre}] Error al exportar: {e}")

        return resultados

    # ------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------
    def ejecutar_carga(self, exportar: bool = True) -> dict:
        resultados_sqlite = self.cargar_sqlite()

        for nombre, res in resultados_sqlite.items():
            if res["estado"] == "exito":
                res["verificado"] = self.verificar_carga(nombre, len(self.dfs[nombre]))

        resultados_export = self.exportar_archivos() if exportar else {}
        return {"sqlite": resultados_sqlite, "exportacion": resultados_export}
