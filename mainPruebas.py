"""
MAIN DE TEST - SOLO DASHBOARD
"""

import subprocess
import sys
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("="*70)
    logger.info("TEST DASHBOARD - Servidor de datos")
    logger.info("="*70)

    dashboard_script = os.path.join('dashboard', 'run_dashboard.py')
    
    if not os.path.exists(dashboard_script):
        logger.error(f"No se encontró el script del dashboard: {dashboard_script}")
        return

    print("\n🚀 Iniciando dashboard en modo test...")
    print("🌐 Dashboard en http://localhost:8000")
    print("💡 El servidor seguirá corriendo aunque cierres el navegador")
    
    try:
        # Poner el servidor en segundo plano y mantenerlo activo
        subprocess.Popen([sys.executable, dashboard_script])
    except Exception as e:
        logger.error(f"Error al iniciar el dashboard: {e}")
        print("\n💡 Puedes abrir el dashboard manualmente ejecutando:")
        print("   python run_dashboard.py")
    
    print("\n🎉 Servidor lanzado. Puedes abrir tu navegador y explorar los datos.")

if __name__ == "__main__":
    main()
