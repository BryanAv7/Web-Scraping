"""
ORQUESTADOR - MODO PROCESOS
FASE 1: Scraping paralelo
FASE 2: Preprocesamiento secuencial
FASE 3: Análisis LLM (main2)
"""

from concurrent.futures import ProcessPoolExecutor, TimeoutError
import logging
from datetime import datetime
import importlib.util
import os
import asyncio
import subprocess
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURACIÓN PRINCIPAL
# ==========================================

POSTS_POR_TEMA = 20

TEMAS_BUSCAR = [
    "nicolas maduro capturado",
]

# ==========================================
# EXTRACTORES
# ==========================================

EXTRACTORES = [
    {"nombre": "LinkedIn", "archivo": "webscraping_extractores/extraerLinkedln.py", "activo": True},
    {"nombre": "Twitter/X", "archivo": "webscraping_extractores/extraerX.py", "activo": True},
    {"nombre": "Facebook", "archivo": "webscraping_extractores/extraerFb.py", "activo": True},
    {"nombre": "Reddit", "archivo": "webscraping_extractores/extraerReddit.py", "activo": True},
]

MAX_WORKERS = 4
TIMEOUT = 600

SCRIPT_PREPROCESAMIENTO = "pipeline/preprocesamiento.py"
RUTA_MAIN2 = "main2.py" 

# ==========================================
# EJECUTAR UN EXTRACTOR EN PROCESO
# ==========================================

def _ejecutar_extractor_proceso(nombre, archivo, config):
    try:
        logger.info(f"Iniciando en proceso: {nombre}")
        logger.info(f"  - Posts por tema: {config.get('posts_por_tema')}")
        logger.info(f"  - Temas a buscar: {len(config.get('temas_buscar', []))}")

        if not os.path.exists(archivo):
            raise FileNotFoundError(f"Archivo no encontrado: {archivo}")

        spec = importlib.util.spec_from_file_location("modulo_extractor", archivo)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)

        if hasattr(modulo, "main"):
            asyncio.run(modulo.main(
                posts_por_tema=config.get("posts_por_tema"),
                temas_buscar=config.get("temas_buscar")
            ))
        else:
            raise RuntimeError(f"{nombre} no tiene función main()")

        logger.info(f"{nombre}: Completado exitosamente")
        return {"nombre": nombre, "estado": "exitoso"}

    except Exception as e:
        logger.error(f"{nombre}: Error - {str(e)}")
        return {"nombre": nombre, "estado": "error", "error": str(e)}

# ==========================================
# PREPROCESAMIENTO
# ==========================================

def _ejecutar_preprocesamiento():
    try:
        logger.info("=" * 70)
        logger.info("Iniciando FASE 2: Preprocesamiento")
        logger.info("=" * 70)

        if not os.path.exists(SCRIPT_PREPROCESAMIENTO):
            raise FileNotFoundError(f"No existe {SCRIPT_PREPROCESAMIENTO}")

        resultado = subprocess.run(
            [sys.executable, SCRIPT_PREPROCESAMIENTO],
            capture_output=True,
            text=True
        )

        if resultado.returncode != 0:
            raise RuntimeError(resultado.stderr)

        logger.info("Preprocesamiento completado exitosamente")
        logger.info(resultado.stdout)

        return {"nombre": "Preprocesamiento", "estado": "exitoso"}

    except Exception as e:
        logger.error(f"Preprocesamiento: Error - {str(e)}")
        return {"nombre": "Preprocesamiento", "estado": "error", "error": str(e)}

# ==========================================
# ORQUESTADOR
# ==========================================

class OrquestadorExtractores:

    def __init__(self, config, max_workers=2):
        self.config = config
        self.max_workers = max_workers
        self.resultados = {}
        self.errores = {}
        self.inicio = None
        self.fin = None

    def ejecutar(self):
        logger.info("=" * 70)
        logger.info("Orquestador - Modo Procesos")
        logger.info("=" * 70)
        logger.info(f"Temas a buscar: {len(self.config.get('temas_buscar', []))}")
        logger.info("=" * 70)

        self.inicio = datetime.now()

        # ==========================
        # FASE 1 - SCRAPING
        # ==========================
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}

            for ext in EXTRACTORES:
                if ext["activo"]:
                    future = executor.submit(
                        _ejecutar_extractor_proceso,
                        ext["nombre"],
                        ext["archivo"],
                        self.config
                    )
                    futures[future] = ext["nombre"]

            for future in futures:
                nombre = futures[future]
                try:
                    resultado = future.result(timeout=TIMEOUT)
                    if resultado["estado"] == "exitoso":
                        self.resultados[nombre] = resultado
                    else:
                        self.errores[nombre] = resultado.get("error")
                except TimeoutError:
                    self.errores[nombre] = f"Timeout después de {TIMEOUT} segundos"
                except Exception as e:
                    self.errores[nombre] = str(e)

        logger.info("=" * 70)
        logger.info("FASE 1 COMPLETADA")
        logger.info("Iniciando FASE 2")
        logger.info("=" * 70)

        # ==========================
        # FASE 2 - PREPROCESAMIENTO
        # ==========================
        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_ejecutar_preprocesamiento)
            try:
                resultado = future.result(timeout=TIMEOUT)
                if resultado["estado"] == "exitoso":
                    self.resultados["Preprocesamiento"] = resultado
                else:
                    self.errores["Preprocesamiento"] = resultado.get("error")
            except TimeoutError:
                self.errores["Preprocesamiento"] = f"Timeout después de {TIMEOUT} segundos"
            except Exception as e:
                self.errores["Preprocesamiento"] = str(e)

        self.fin = datetime.now()
        self._imprimir_resumen()

        # ==========================
        # FASE 3 - ANÁLISIS LLM (MAIN2)
        # ==========================
        if not self.errores:
            self._ejecutar_main2()
        else:
            logger.warning("Se detectaron errores en fases anteriores. Se omite MAIN2.")

    def _imprimir_resumen(self):
        tiempo_total = (self.fin - self.inicio).total_seconds()

        logger.info("=" * 70)
        logger.info("RESUMEN FINAL DEL PIPELINE")
        logger.info("=" * 70)
        logger.info(f"Procesos exitosos: {len(self.resultados)}")
        logger.info(f"Procesos con error: {len(self.errores)}")
        logger.info(f"Tiempo total: {tiempo_total:.2f} segundos")

        if self.errores:
            logger.info("Errores:")
            for nombre, error in self.errores.items():
                logger.error(f"  {nombre}: {error}")

        logger.info("=" * 70)

    def _ejecutar_main2(self):
        try:
            if not os.path.exists(RUTA_MAIN2):
                raise FileNotFoundError(f"No se encontró main2: {RUTA_MAIN2}")

            spec = importlib.util.spec_from_file_location("main2_module", RUTA_MAIN2)
            main2_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main2_module)

            logger.info("="*70)
            logger.info("Iniciando FASE 3: ANÁLISIS LLM (MAIN2)")
            logger.info("="*70)

            main2_module.main()

        except Exception as e:
            logger.error(f"No se pudo ejecutar MAIN2: {str(e)}")

# ==========================================
# MAIN
# ==========================================

def main():
    logger.info("=" * 70)
    logger.info("Pipeline completo: SCRAPING + PREPROCESAMIENTO + ANALISIS LLM")
    logger.info("=" * 70)

    config = {
        "posts_por_tema": POSTS_POR_TEMA,
        "temas_buscar": TEMAS_BUSCAR
    }

    orquestador = OrquestadorExtractores(
        config=config,
        max_workers=MAX_WORKERS
    )

    orquestador.ejecutar()


if __name__ == "__main__":
    main()
