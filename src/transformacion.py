import ast
import logging
import pandas as pd
from config import configurar_logs

# Detección de duplicados por llave.
CLAVES_DUPLICADOS = {
    "Listings": ["id"],
    "Reviews": ["id"],
    "Calendar": ["listing_id", "date"],
}

FECHAS_LISTINGS = ["last_scraped", "host_since", "first_review", "last_review", "calendar_last_scraped"]
PORCENTAJES_LISTINGS = ["host_response_rate", "host_acceptance_rate"]
ETIQUETAS_PRECIO = ["Económico", "Estándar", "Alto", "Premium"]


class Transformacion:
    """
    Clase encargada de transformar y limpiar los DataFrames extraídos.
    Implementa normalización de tipos de datos, limpieza de nulos/duplicados,
    derivación de variables temporales, tratamiento de texto.
    """

    def __init__(self, dicc_dataframes: dict):
        self.dfs = dicc_dataframes
        self.dfs_limpios = {}
        configurar_logs()

    # ------------------------------------------------------------------
    # Limpieza general
    # ------------------------------------------------------------------
    def _limpiar_basicos(self, df: pd.DataFrame, nombre_df: str, claves: list) -> pd.DataFrame:
        antes = len(df)
        claves = [c for c in claves if c in df.columns]
        if claves:
            df = df.dropna(subset=claves).drop_duplicates(subset=claves)
        else:
            df = df.drop_duplicates()

        df = df.replace(r"^\s*$", pd.NA, regex=True)

        logging.info(f"[{nombre_df}] Limpieza básica: {antes:,} -> {len(df):,} registros "
                     f"({antes - len(df):,} eliminados).")
        return df

    def _convertir_booleanos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convierte columnas con valores 't'/'f' (formato de Airbnb) a 1/0."""
        for col in df.columns:
            if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
                valores = {v for v in df[col].dropna() if isinstance(v, str)}
                if valores and valores <= {"t", "f"} and df[col].dropna().map(type).eq(str).all():
                    df[col] = df[col].map({"t": 1, "f": 0}).astype("Int64")
        return df

    def _normalizar_precio(self, df: pd.DataFrame, columna: str) -> pd.DataFrame:
        """Convierte '$1,234.00' a 1234.0. Los precios <= 0 se dejan como nulo."""
        if columna in df.columns:
            texto = df[columna].astype("string").str.replace(r"[$,]", "", regex=True)
            df[columna] = pd.to_numeric(texto, errors="coerce")
            df.loc[df[columna] <= 0, columna] = pd.NA
            logging.info(f"Columna '{columna}' normalizada a número.")
        return df

    def _normalizar_porcentaje(self, df: pd.DataFrame, columna: str) -> pd.DataFrame:
        """Convierte '95%' a 95.0."""
        if columna in df.columns:
            texto = df[columna].astype("string").str.replace("%", "", regex=False)
            df[columna] = pd.to_numeric(texto, errors="coerce")
        return df

    def _formatear_fecha(self, df: pd.DataFrame, columna: str) -> pd.DataFrame:
        """Estandariza una columna de fecha a texto YYYY-MM-DD."""
        if columna in df.columns:
            df[columna] = pd.to_datetime(df[columna], errors="coerce").dt.strftime("%Y-%m-%d")
        return df

    def _procesar_fechas(self, df: pd.DataFrame, columna: str) -> pd.DataFrame:
        """Estandariza la fecha a YYYY-MM-DD y deriva año, mes, día y trimestre."""
        if columna in df.columns:
            fechas = pd.to_datetime(df[columna], errors="coerce")
            df["anio"] = fechas.dt.year.astype("Int64")
            df["mes"] = fechas.dt.month.astype("Int64")
            df["dia"] = fechas.dt.day.astype("Int64")
            df["trimestre"] = fechas.dt.quarter.astype("Int64")
            df[columna] = fechas.dt.strftime("%Y-%m-%d")
            logging.info(f"Fecha '{columna}' estandarizada y variables anio/mes/dia/trimestre creadas.")
        return df

    def _categorizar_precios(self, df: pd.DataFrame, columna: str = "price") -> pd.DataFrame:
        """
        Clasifica el precio en Económico / Estándar / Alto / Premium usando los
        cuartiles de TODO el mercado (así un 'Premium' significa lo mismo en
        cualquier tipo de alojamiento y la comparación entre room_type tiene sentido).
        """
        if columna not in df.columns:
            return df
        df[f"{columna}_rango"] = pd.qcut(
            df[columna].rank(method="first"), q=4, labels=ETIQUETAS_PRECIO
        )
        logging.info(f"Precios categorizados en '{columna}_rango' por cuartiles del mercado.")
        return df

    def _desanidar_lista(self, df: pd.DataFrame, columna: str) -> pd.DataFrame:
        """Convierte campos tipo lista (ej. amenities) en texto limpio separado por comas:
        ["Wifi", "TV"]  ->  Wifi, TV. """
        if columna not in df.columns:
            return df

        def a_texto(valor):
            if isinstance(valor, str):
                try:
                    valor = ast.literal_eval(valor)  # "['Wifi', 'TV']" -> ['Wifi', 'TV']
                except (ValueError, SyntaxError):
                    return valor.strip("[]{}").replace('"', "").replace("'", "")
            if isinstance(valor, (list, tuple, set)):
                return ", ".join(str(v).strip() for v in valor)
            return pd.NA  # nulos se quedan como nulo (no como el texto "nan")

        df[columna] = df[columna].apply(a_texto)
        logging.info(f"Campo '{columna}' desanidado a texto separado por comas.")
        return df

    # ------------------------------------------------------------------
    # Reporte de calidad
    # ------------------------------------------------------------------
    def _reporte_calidad(self, df: pd.DataFrame, nombre: str) -> None:
        """Registra en el log las columnas con más nulos."""
        nulos = (df.isna().mean() * 100).round(1)
        nulos = nulos[nulos > 0].sort_values(ascending=False).head(10)
        if nulos.empty:
            logging.info(f"[{nombre}] Calidad: sin valores nulos.")
        else:
            detalle = ", ".join(f"{c}={p}%" for c, p in nulos.items())
            logging.info(f"[{nombre}] Calidad - columnas con más nulos: {detalle}")

    # ------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------
    def ejecutar_transformacion(self) -> dict:
        """Aplica las transformaciones a cada tabla y devuelve el diccionario limpio."""
        logging.info("--- INICIANDO TRANSFORMACIÓN ---")

        for nombre, df in self.dfs.items():
            if df.empty:
                logging.warning(f"El DataFrame '{nombre}' está vacío, se omite.")
                continue

            logging.info(f"Transformando tabla: {nombre}")
            df_t = df.copy()

            # 1. Limpieza general (aplica a todas las tablas).
            df_t = self._limpiar_basicos(df_t, nombre, CLAVES_DUPLICADOS.get(nombre, []))
            df_t = self._convertir_booleanos(df_t)

            # 2. Transformaciones específicas por tabla.
            if nombre == "Listings":
                df_t = self._normalizar_precio(df_t, "price")
                df_t = self._categorizar_precios(df_t, "price")
                for col in PORCENTAJES_LISTINGS:
                    df_t = self._normalizar_porcentaje(df_t, col)
                for col in FECHAS_LISTINGS:
                    df_t = self._formatear_fecha(df_t, col)
                df_t = self._desanidar_lista(df_t, "amenities")
                df_t = self._desanidar_lista(df_t, "host_verifications")

            elif nombre == "Calendar":
                df_t = self._normalizar_precio(df_t, "price")
                df_t = self._normalizar_precio(df_t, "adjusted_price")
                df_t = self._procesar_fechas(df_t, "date")

            elif nombre == "Reviews":
                df_t = self._procesar_fechas(df_t, "date")

            # 3. Validación de calidad.
            self._reporte_calidad(df_t, nombre)

            self.dfs_limpios[nombre] = df_t
            logging.info(f"Transformación de '{nombre}' finalizada.")

        logging.info("--- TRANSFORMACIÓN COMPLETADA ---")
        return self.dfs_limpios
