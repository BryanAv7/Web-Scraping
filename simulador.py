# simulador_fases.py
"""
Script simulador que imita el comportamiento de los scripts reales de cada fase.
Este script será reemplazado por los scripts reales más adelante.
"""

import sys
import time
import random

def simular_fase(numero_fase, tema):
    """Simula la ejecución de una fase con prints y delays"""
    
    print(f"[FASE {numero_fase}] Iniciando procesamiento para tema: '{tema}'")
    time.sleep(0.5)
    
    if numero_fase == 1:
        print(f"[FASE 1] Extrayendo datos para '{tema}'...")
        time.sleep(2)
        print(f"[FASE 1] Procesando 150 elementos...")
        time.sleep(1.5)
        print(f"[FASE 1] Generando dataset base...")
        time.sleep(1)
        print(f"[FASE 1] [OK] Dataset raw generado exitosamente")
        
    elif numero_fase == 2:
        print(f"[FASE 2] Cargando dataset raw de '{tema}'...")
        time.sleep(1.5)
        print(f"[FASE 2] Limpiando datos duplicados...")
        time.sleep(2)
        print(f"[FASE 2] Normalizando formatos...")
        time.sleep(1.5)
        print(f"[FASE 2] Validando integridad...")
        time.sleep(1)
        print(f"[FASE 2] [OK] Dataset limpio generado exitosamente")
        
    elif numero_fase == 3:
        print(f"[FASE 3] Cargando dataset limpio de '{tema}'...")
        time.sleep(1)
        print(f"[FASE 3] Procesando elementos por lotes...")
        time.sleep(2)
        print(f"[FASE 3] Construyendo prompts para modelo...")
        time.sleep(2)
        print(f"[FASE 3] Enviando a modelo de interpretación...")
        time.sleep(3)
        print(f"[FASE 3] Generando resultados estructurados...")
        time.sleep(1.5)
        print(f"[FASE 3] [OK] Dataset procesado generado exitosamente")
    
    print(f"[FASE {numero_fase}] Fase completada exitosamente\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Error: Se requieren 2 argumentos: <numero_fase> <tema>")
        print("Uso: python simulador_fases.py 1 'mi_tema'")
        sys.exit(1)
    
    fase = int(sys.argv[1])
    tema = sys.argv[2]
    
    simular_fase(fase, tema)