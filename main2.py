"""
ORQUESTADOR - ANÁLISIS LLM
Ejecución de análisis de sentimientos + LLM sobre CSVs generados por los extractores
"""

from concurrent.futures import ProcessPoolExecutor, TimeoutError
import logging
import subprocess
import sys
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURACIÓN PRINCIPAL
# ==========================================

TEMA_ANALISIS = "nicolas muñoz"
TIMEOUT = 900  
MAX_WORKERS = 4
PRUEBA_RAPIDA = False  

# ==========================================
# SCRIPTS DE ANÁLISIS 
# ==========================================

ANALISIS_SCRIPTS = [
    {"nombre": "LinkedIn", "archivo": "Parte2/promptLinkedin.py", "csv_input": "datos_limpios/linkedin_limpio.csv"},
    {"nombre": "Twitter/X", "archivo": "Parte2/promptx.py", "csv_input": "datos_limpios/X_limpio.csv"},
    {"nombre": "Facebook", "archivo": "Parte2/promptFacebook.py", "csv_input": "datos_limpios/facebook_limpio.csv"},
    {"nombre": "Reddit", "archivo": "Parte2/promptReddit.py", "csv_input": "datos_limpios/reddit_limpio.csv"},
]

# ==========================================
# EJECUTAR UN ANÁLISIS EN PROCESO
# ==========================================

def ejecutar_analisis(nombre, archivo, csv_input, tema):
    """
    Ejecuta el script de análisis como proceso independiente.
    """
    try:
        logger.info(f"Iniciando análisis: {nombre}")
        
        if not os.path.exists(archivo):
            raise FileNotFoundError(f"Script no encontrado: {archivo}")
        if not os.path.exists(csv_input):
            raise FileNotFoundError(f"CSV de entrada no encontrado: {csv_input}")

        # Ejecutar el script pasando CSV y TEMA_ANALISIS como argumentos
        comando = [sys.executable, archivo, csv_input, tema]
        resultado = subprocess.run(comando, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if resultado.returncode != 0:
            raise RuntimeError(resultado.stderr)

        logger.info(f"{nombre}: Análisis completado exitosamente")
        return {"nombre": nombre, "estado": "exitoso", "stdout": resultado.stdout}

    except Exception as e:
        logger.error(f"{nombre}: Error - {str(e)}")
        return {"nombre": nombre, "estado": "error", "error": str(e)}

# ==========================================
# ORQUESTADOR
# ==========================================

def main():
    logger.info("="*70)
    logger.info("ORQUESTADOR - FASE ANÁLISIS LLMs")
    logger.info("="*70)

    inicio = datetime.now()
    resultados = {}
    errores = {}

    if not PRUEBA_RAPIDA:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            for script in ANALISIS_SCRIPTS:
                future = executor.submit(
                    ejecutar_analisis,
                    script["nombre"],
                    script["archivo"],
                    script["csv_input"],
                    TEMA_ANALISIS
                )
                futures[future] = script["nombre"]

            for future in futures:
                nombre = futures[future]
                try:
                    res = future.result(timeout=TIMEOUT)
                    if res["estado"] == "exitoso":
                        resultados[nombre] = res
                    else:
                        errores[nombre] = res.get("error")
                except TimeoutError:
                    errores[nombre] = f"Timeout después de {TIMEOUT} segundos"
                except Exception as e:
                    errores[nombre] = str(e)

        fin = datetime.now()
        tiempo_total = (fin - inicio).total_seconds()

        logger.info("="*70)
        logger.info("RESUMEN FINAL DEL ORQUESTADOR")
        logger.info("="*70)
        logger.info(f"Análisis exitosos: {len(resultados)}")
        logger.info(f"Análisis con error: {len(errores)}")
        logger.info(f"Tiempo total: {tiempo_total:.2f} segundos")

        if errores:
            logger.info("Errores detectados:")
            for nombre, error in errores.items():
                logger.error(f"  {nombre}: {error}")

        logger.info("="*70)
    else:
        logger.info("Modo PRUEBA RÁPIDA activado - Se omite la fase de análisis LLM")
        logger.info("="*70)

    ### Abrir el dashboard automáticamente
    print("\n" + "="*60)
    print("✅ Análisis completados exitosamente")
    print("="*60)

    # Preguntar 
    respuesta = input("\n¿Deseas abrir el dashboard ahora? (s/n): ").lower().strip()

    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        dashboard_script = os.path.join('dashboard', 'run_dashboard.py')
        
        print("\n🚀 Iniciando dashboard...")
        
        try:
            subprocess.run(["python", dashboard_script])
        except KeyboardInterrupt:
            print("\n🛑 Dashboard cerrado")
    else:
        print("\n💡 Puedes abrir el dashboard más tarde ejecutando:")
        print("   python run_dashboard.py")
        print("   (desde el directorio del dashboard)")

    print("\n🎉 ¡Hasta luego!")

if __name__ == "__main__":
    main()
