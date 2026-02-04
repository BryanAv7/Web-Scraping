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

PRUEBA_RÁPIDA = False  
POSTS_POR_TEMA_DEFAULT = 20
TEMAS_BUSCAR_DEFAULT = [
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
# FUNCIONES PARA INGRESO DE DATOS
# ==========================================

def preguntar_config_usuario():
    # POSTS_POR_TEMA
    try:
        posts_input = input(f"Ingrese número de posts/comentarios por tema [{POSTS_POR_TEMA_DEFAULT}]: ").strip()
        posts_por_tema = int(posts_input) if posts_input else POSTS_POR_TEMA_DEFAULT
    except ValueError:
        logger.warning(f"Valor inválido, se usará {POSTS_POR_TEMA_DEFAULT}")
        posts_por_tema = POSTS_POR_TEMA_DEFAULT

    # TEMAS_BUSCAR
    temas_input = input(f"Ingrese temas a buscar, separados por coma [{', '.join(TEMAS_BUSCAR_DEFAULT)}]: ").strip()
    if temas_input:
        temas_buscar = [t.strip() for t in temas_input.split(",") if t.strip()]
    else:
        temas_buscar = TEMAS_BUSCAR_DEFAULT

    return posts_por_tema, temas_buscar

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
            text=True,
            timeout=300  # 5 minutos timeout
        )

        if resultado.returncode != 0:
            raise RuntimeError(resultado.stderr)

        logger.info("Preprocesamiento completado exitosamente")
        if resultado.stdout:
            logger.info(resultado.stdout)

        return {"nombre": "Preprocesamiento", "estado": "exitoso"}

    except subprocess.TimeoutExpired:
        logger.error("Preprocesamiento: Timeout excedido")
        return {"nombre": "Preprocesamiento", "estado": "error", "error": "Timeout"}
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
        self.tema_a_analizar = None

    def ejecutar(self):
        logger.info("=" * 70)
        logger.info("🚀 ORQUESTADOR - MODO PROCESOS")
        logger.info("=" * 70)
        logger.info(f"Temas a buscar: {self.config.get('temas_buscar')}")
        logger.info(f"Posts por tema: {self.config.get('posts_por_tema')}")
        logger.info(f"Max workers: {self.max_workers}")
        logger.info("=" * 70)

        self.inicio = datetime.now()

        # ==========================
        # FASE 1 - SCRAPING PARALELO
        # ==========================
        logger.info("📊 FASE 1: SCRAPING")
        
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
                        logger.info(f"✓ {nombre} completado")
                    else:
                        self.errores[nombre] = resultado.get("error")
                        logger.error(f"✗ {nombre} falló: {resultado.get('error')}")
                except TimeoutError:
                    self.errores[nombre] = f"Timeout después de {TIMEOUT} segundos"
                    logger.error(f"✗ {nombre} timeout")
                except Exception as e:
                    self.errores[nombre] = str(e)
                    logger.error(f"✗ {nombre} error: {str(e)}")

        logger.info("=" * 70)
        logger.info(f"FASE 1 COMPLETADA: {len(self.resultados)} exitosos, {len(self.errores)} fallidos")
        logger.info("=" * 70)

        # ==========================
        # FASE 2 - PREPROCESAMIENTO
        # ==========================
        logger.info("🔧 FASE 2: PREPROCESAMIENTO")
        
        resultado_prep = _ejecutar_preprocesamiento()
        
        if resultado_prep["estado"] == "exitoso":
            self.resultados["Preprocesamiento"] = resultado_prep
            logger.info("✓ Preprocesamiento completado")
        else:
            self.errores["Preprocesamiento"] = resultado_prep.get("error")
            logger.error(f"✗ Preprocesamiento falló: {resultado_prep.get('error')}")

        # ==========================
        # Tema para análisis
        # ==========================
        if self.config.get("temas_buscar"):
            self.tema_a_analizar = self.config.get("temas_buscar")[0]
            logger.info(f"📝 Tema principal: {self.tema_a_analizar}")

        self.fin = datetime.now()
        self._imprimir_resumen()

        # ==========================
        # FASE 3 - ANÁLISIS LLM (MAIN2)
        # ==========================
        if self.tema_a_analizar and "Preprocesamiento" in self.resultados:
            logger.info("🤖 FASE 3: ANÁLISIS LLM")
            self._ejecutar_main2()
        else:
            logger.warning("⚠️  Se omite FASE 3 por errores en fases anteriores")

    def _imprimir_resumen(self):
        tiempo_total = (self.fin - self.inicio).total_seconds()

        logger.info("=" * 70)
        logger.info("📊 RESUMEN FINAL DEL PIPELINE")
        logger.info("=" * 70)
        logger.info(f"✓ Procesos exitosos: {len(self.resultados)}")
        logger.info(f"✗ Procesos con error: {len(self.errores)}")
        logger.info(f"⏱️  Tiempo total: {tiempo_total:.2f} segundos ({tiempo_total/60:.2f} minutos)")

        if self.resultados:
            logger.info("\n✓ Exitosos:")
            for nombre in self.resultados:
                logger.info(f"  - {nombre}")

        if self.errores:
            logger.info("\n✗ Errores:")
            for nombre, error in self.errores.items():
                logger.error(f"  - {nombre}: {error}")

        logger.info("=" * 70)

    def _ejecutar_main2(self):
        try:
            if not os.path.exists(RUTA_MAIN2):
                raise FileNotFoundError(f"No se encontró main2: {RUTA_MAIN2}")

            spec = importlib.util.spec_from_file_location("main2_module", RUTA_MAIN2)
            main2_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main2_module)

            logger.info("Ejecutando análisis LLM...")
            main2_module.main(self.tema_a_analizar)
            logger.info("✓ Análisis LLM completado")

        except Exception as e:
            logger.error(f"✗ Error en MAIN2: {str(e)}")

# ==========================================
# MAIN
# ==========================================

def main():
    logger.info("=" * 70)
    logger.info("🚀 PIPELINE COMPLETO: SCRAPING + PREPROCESAMIENTO + ANÁLISIS")
    logger.info("=" * 70)

    # ----------------------------------
    # MODO SERVIDOR (Flask) - SIN NÚMERO DE FASE
    # python main.py <tema>
    # ----------------------------------
    if len(sys.argv) >= 2 and len(sys.argv) < 3:
        tema = sys.argv[1]

        logger.info(f"🌐 Ejecutado desde servidor Flask")
        logger.info(f"📝 Tema: {tema}")

        config = {
            "posts_por_tema": POSTS_POR_TEMA_DEFAULT,
            "temas_buscar": [tema]
        }

    # ----------------------------------
    # COMPATIBILIDAD CON VERSIÓN ANTIGUA (3 args)
    # python main.py <fase> <tema>
    # ----------------------------------
    elif len(sys.argv) >= 3:
        fase = int(sys.argv[1])  # Ignoramos este parámetro
        tema = sys.argv[2]

        logger.warning(f"⚠️  Usando formato antiguo con número de fase (ignorado)")
        logger.info(f"📝 Tema: {tema}")

        config = {
            "posts_por_tema": POSTS_POR_TEMA_DEFAULT,
            "temas_buscar": [tema]
        }

    # ----------------------------------
    # MODO CONSOLA (interactivo)
    # ----------------------------------
    else:
        posts_por_tema, temas_buscar = preguntar_config_usuario()
        config = {
            "posts_por_tema": posts_por_tema,
            "temas_buscar": temas_buscar
        }

    # ----------------------------------
    # EJECUTAR ORQUESTADOR
    # ----------------------------------
    orquestador = OrquestadorExtractores(
        config=config,
        max_workers=MAX_WORKERS
    )

    try:
        orquestador.ejecutar()
        logger.info("✓ Pipeline finalizado")
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Pipeline interrumpido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal en pipeline: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()