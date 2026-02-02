"""
ORQUESTADOR - ANÁLISIS LLM
Ejecución concurrente de análisis de sentimientos + LLM sobre CSVs generados por los extractores
"""

import logging
import subprocess
import sys
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# ==========================================
# CONFIGURACIÓN PRINCIPAL
# ==========================================

TEMA_ANALISIS = "nicolas muñoz"
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
        resultado = subprocess.run(
            comando, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            errors='replace',
            stdin=subprocess.DEVNULL
        )

        if resultado.returncode != 0:
            raise RuntimeError(resultado.stderr)

        logger.info(f"{nombre}: Análisis completado exitosamente")
        return {"nombre": nombre, "estado": "exitoso", "stdout": resultado.stdout}

    except Exception as e:
        logger.error(f"{nombre}: Error - {str(e)}")
        return {"nombre": nombre, "estado": "error", "error": str(e)}

# ==========================================
# ORQUESTADOR CONCURRENTE
# ==========================================

def main():
    logger.info("="*70)
    logger.info("ORQUESTADOR - FASE ANÁLISIS LLMs (CONCURRENTE)")
    logger.info("="*70)

    inicio = datetime.now()
    resultados = {}
    errores = {}

    if not PRUEBA_RAPIDA:
        # ==========================
        # Ejecutar scripts concurrentemente con hilos
        # ==========================
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_nombre = {
                executor.submit(ejecutar_analisis, s["nombre"], s["archivo"], s["csv_input"], TEMA_ANALISIS): s["nombre"]
                for s in ANALISIS_SCRIPTS
            }

            for future in as_completed(future_to_nombre):
                nombre = future_to_nombre[future]
                try:
                    res = future.result()
                    if res["estado"] == "exitoso":
                        resultados[nombre] = res
                    else:
                        errores[nombre] = res.get("error")
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

    # Abrir el dashboard automáticamente
    print("\n" + "="*60)
    print("✅ Análisis completados exitosamente")
    print("="*60)

    dashboard_script = os.path.join('dashboard', 'run_dashboard.py')
    
    print("\n🚀 Iniciando dashboard automáticamente...")
    
    try:
        subprocess.run([sys.executable, dashboard_script])
    except KeyboardInterrupt:
        print("\n🛑 Dashboard cerrado")
    except Exception as e:
        print(f"\n⚠️ Error al abrir dashboard: {e}")
        print("\n💡 Puedes abrir el dashboard manualmente ejecutando:")
        print("   python run_dashboard.py")
        print("   (desde el directorio del dashboard)")

    print("\n🎉 ¡Hasta luego!")

if __name__ == "__main__":
    main()
