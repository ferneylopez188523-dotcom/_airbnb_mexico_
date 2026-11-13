import logging
import sys

from carga import Carga
from config import configurar_logs
from extraccion import Extraccion
#from modelo_bi import ModeloBI
#from transformacion import Transformacion


def ejecutar_etl() -> bool:
    """Ejecuta Extracción -> Transformación -> Carga -> Modelo BI. Devuelve True si todo salió bien."""
    configurar_logs()
    logging.info("=" * 50)
    logging.info("INICIANDO PIPELINE ETL - AIRBNB CDMX")
    logging.info("=" * 50)

    extractor = Extraccion()
    try:
        # FASE 1: EXTRACCIÓN
        logging.info(">>> FASE 1: EXTRACCIÓN (MongoDB o, si no está disponible, CSV)")
        datos = extractor.obtener_datos()

        # FASE 2: TRANSFORMACIÓN
        #logging.info(">>> FASE 2: TRANSFORMACIÓN")
        #datos_limpios = Transformacion(datos).ejecutar_transformacion()

        # FASE 3: CARGA
       # logging.info(">>> FASE 3: CARGA")
        #resultados = Carga(datos_limpios).ejecutar_carga(exportar=True)

        # FASE 4: MODELO ESTRELLA PARA BI (Power BI)
        #logging.info(">>> FASE 4: MODELO ESTRELLA PARA BI")
        #resultados["modelo_bi"] = ModeloBI(datos_limpios).construir()

    except Exception as e:
        logging.critical(f"EL PIPELINE FALLÓ: {e}")
        return False
    finally:
        extractor.cerrar_conexion()

    """# Revisión final: si alguna tabla falló o no coincidió el conteo, se reporta como fallo.
    errores = [
        f"{fase}/{tabla}"
        for fase, tablas in resultados.items()
        for tabla, res in tablas.items()
        if res["estado"] != "exito" or res.get("verificado") is False
    ]
    if errores:
        logging.error(f"PIPELINE FINALIZADO CON ERRORES en: {', '.join(errores)}")
        return False"""

    logging.info("PIPELINE ETL FINALIZADO CON ÉXITO")
    return True


if __name__ == "__main__":
    # Código de salida 0 = éxito, 1 = fallo (útil si se programa la ejecución).
    sys.exit(0 if ejecutar_etl() else 1)