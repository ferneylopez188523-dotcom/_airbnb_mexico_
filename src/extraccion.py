import logging
import pandas as pd
from config import ARCHIVOS_CSV, DATA_DIR, MONGO_DB, MONGO_URI, configurar_logs


class Extraccion:
    
    COLECCIONES = ["Listings", "Reviews", "Calendar"]

    def __init__(self, db_name: str = MONGO_DB, uri: str = MONGO_URI):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None
        self.fuente = None
        configurar_logs()

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------
    def obtener_datos(self) -> dict:
        try:
            self.conectar_mongodb()
            datos = self.extraer_datos()
            self.fuente = "MongoDB"
        except Exception as e:
            logging.warning(f"MongoDB no disponible ({e}). Se leerán los CSV de la carpeta data/.")
            datos = self.extraer_desde_csv()
            self.fuente = "CSV"
        logging.info(f"Fuente de datos utilizada: {self.fuente}")
        return datos

    # ------------------------------------------------------------------
    # MongoDB
    # ------------------------------------------------------------------
    def conectar_mongodb(self):
        # Se importa aquí para que el proyecto funcione con CSV aunque pymongo no esté instalado.
        from pymongo import MongoClient

        self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
        self.client.admin.command("ping")
        self.db = self.client[self.db_name]
        logging.info(f"Conexión a MongoDB exitosa. Base de datos: {self.db_name}")

    def extraer_datos(self) -> dict:
        if self.db is None:
            raise RuntimeError("No hay conexión a MongoDB. Ejecute conectar_mongodb() primero.")

        dfs = {}
        for col in self.COLECCIONES:
            logging.info(f"Consultando la colección: {col}")
            df = pd.DataFrame(list(self.db[col].find({}, {"_id": 0})))
            if df.empty:
                raise ValueError(f"La colección '{col}' no existe o está vacía")
            dfs[col] = df
            logging.info(f"[{col}] {len(df):,} registros y {df.shape[1]} columnas extraídos de MongoDB.")
        return dfs

    # ------------------------------------------------------------------
    # CSV (respaldo)
    # ------------------------------------------------------------------
    def extraer_desde_csv(self) -> dict:
        dfs = {}
        for tabla, nombre in ARCHIVOS_CSV.items():
            archivo = next(
                (DATA_DIR / f"{nombre}{ext}" for ext in (".csv", ".csv.gz")
                 if (DATA_DIR / f"{nombre}{ext}").exists()),
                None,
            )
            if archivo is None:
                raise FileNotFoundError(
                    f"No se encontró '{nombre}.csv' ni '{nombre}.csv.gz' en {DATA_DIR}"
                )
            logging.info(f"Leyendo {archivo.name} ...")
            dfs[tabla] = pd.read_csv(archivo, low_memory=False)
            logging.info(f"[{tabla}] {len(dfs[tabla]):,} registros y {dfs[tabla].shape[1]} columnas leídos del CSV.")
        return dfs

    def cerrar_conexion(self):
        if self.client is not None:
            self.client.close()
            logging.info("Conexión a MongoDB cerrada.")