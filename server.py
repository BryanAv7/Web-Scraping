#!/usr/bin/env python3
"""
Servidor Flask — Sistema de Procesamiento Analítico
Ejecución en una sola fase con timeout y UTF-8.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import subprocess
import threading
import queue
import json
import csv
import os
import sys
import time

app = Flask(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================
CARPETA_RESULTADOS = "resultados"
TIMEOUT_PROCESO = 1800  # 30 minutos máximo


# ============================================================
# ESTADO GLOBAL DEL PROCESO
# ============================================================
estado_proceso = {
    "tema": None,
    "fase_actual": 0,
    "fase_nombre": "",
    "completado": False,
    "error": None,
    "logs": [],
    "timestamp_inicio": None,
    "timestamp_fin": None,
}

log_queue = queue.Queue()

NOMBRES_FASES = {
    1: "Extracción y Análisis Completo",
}


# ============================================================
# LÓGICA DE PROCESAMIENTO
# ============================================================

def registrar_log(fase, mensaje):
    """Agrega un log al estado global y a la cola de polling."""
    entrada = {
        "fase": fase,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "mensaje": mensaje,
    }
    estado_proceso["logs"].append(entrada)
    log_queue.put(entrada)


def ejecutar_proceso_completo(tema):
    """
    Ejecuta main.py UNA SOLA VEZ con timeout y UTF-8.
    """
    estado_proceso["fase_actual"] = 1
    estado_proceso["fase_nombre"] = NOMBRES_FASES[1]

    try:
        registrar_log(1, f"Iniciando extraccion para: {tema}")
        
        # FORZAR UTF-8 (CRÍTICO PARA WINDOWS)
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        proceso = subprocess.Popen(
            [sys.executable, "main.py", tema],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace',
            env=env
        )

        inicio = time.time()
        ultimo_output = time.time()
        TIMEOUT_SIN_OUTPUT = 300
        
        while True:
            if time.time() - inicio > TIMEOUT_PROCESO:
                registrar_log(1, f"Timeout total ({TIMEOUT_PROCESO}s)")
                proceso.kill()
                raise Exception(f"Proceso excedio {TIMEOUT_PROCESO}s")
            
            if time.time() - ultimo_output > TIMEOUT_SIN_OUTPUT:
                registrar_log(1, f"Sin respuesta por {TIMEOUT_SIN_OUTPUT}s")
                proceso.kill()
                raise Exception(f"Proceso colgado")
            
            linea = proceso.stdout.readline()
            
            if not linea and proceso.poll() is not None:
                break
            
            if linea:
                linea = linea.strip()
                if linea:
                    registrar_log(1, linea)
                    ultimo_output = time.time()
            
            time.sleep(0.1)
        
        if proceso.returncode != 0:
            raise Exception(f"Proceso fallo con codigo {proceso.returncode}")
        
        registrar_log(1, "Proceso completado exitosamente")

    except Exception as e:
        registrar_log(1, f"ERROR: {e}")
        raise


def proceso_completo(tema):
    """Wrapper que ejecuta el proceso en el thread de Flask."""
    try:
        estado_proceso["timestamp_inicio"] = datetime.now().isoformat()
        ejecutar_proceso_completo(tema)
        estado_proceso["completado"] = True
        estado_proceso["timestamp_fin"] = datetime.now().isoformat()
        registrar_log(1, "Pipeline finalizado")
    except Exception as e:
        estado_proceso["error"] = str(e)
        estado_proceso["completado"] = False
        print(f"Error en proceso completo: {e}")


def reiniciar_estado(tema):
    """Resetea el estado global y limpia la cola de logs."""
    estado_proceso.update({
        "tema": tema,
        "fase_actual": 0,
        "fase_nombre": "",
        "completado": False,
        "error": None,
        "logs": [],
        "timestamp_inicio": None,
        "timestamp_fin": None,
    })

    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except queue.Empty:
            break


# ============================================================
# LÓGICA DE RESULTADOS
# ============================================================

def leer_archivos_resultados():
    fuentes = {}
    if not os.path.exists(CARPETA_RESULTADOS):
        return fuentes

    for nombre_archivo in os.listdir(CARPETA_RESULTADOS):
        ruta = os.path.join(CARPETA_RESULTADOS, nombre_archivo)
        fuente = nombre_archivo.split("_")[0].lower()

        if fuente not in fuentes:
            fuentes[fuente] = {"json": None, "csv": []}

        if nombre_archivo.endswith(".json"):
            with open(ruta, "r", encoding="utf-8") as f:
                fuentes[fuente]["json"] = json.load(f)

        elif nombre_archivo.endswith(".csv"):
            with open(ruta, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                fuentes[fuente]["csv"] = [row for row in reader]

    return fuentes


def calcular_sentimiento_global(fuentes):
    conteo = {"positivo": 0, "negativo": 0, "neutral": 0}

    for fuente in fuentes.values():
        for fila in fuente["csv"]:
            valor = fila.get("sentimiento", "").strip().upper()
            if valor == "POSITIVO":
                conteo["positivo"] += 1
            elif valor == "NEGATIVO":
                conteo["negativo"] += 1
            elif valor == "NEUTRAL":
                conteo["neutral"] += 1

    total = sum(conteo.values())
    conteo["total"] = total
    predomina = max(conteo, key=lambda k: conteo[k] if k != "total" else -1)
    conteo["predomina"] = predomina

    return conteo


def generar_llm_global(sentimiento_global):
    API_KEY = ""

    prompt = f"""
    Resumen de sentimiento de múltiples redes sociales:
    - Positivos: {sentimiento_global['positivo']}
    - Negativos: {sentimiento_global['negativo']}
    - Neutrales: {sentimiento_global['neutral']}
    Total: {sentimiento_global['total']}
    Predominante: {sentimiento_global['predomina']}
    
    Proporciona análisis en un párrafo simple.
    """

    try:
        import google.genai as genai
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error en analisis: {str(e)}"

def obtener_datos_dashboard():
    fuentes = leer_archivos_resultados()
    sentimiento_global = calcular_sentimiento_global(fuentes)
    analisis_llm = generar_llm_global(sentimiento_global)

    return {
        "fuentes": fuentes,
        "sentimiento_global": sentimiento_global,
        "analisis_llm": analisis_llm,
    }


# ============================================================
# ENDPOINTS
# ============================================================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if not estado_proceso["completado"]:
        return redirect(url_for("index"))

    datos = obtener_datos_dashboard()

    return render_template(
        "dashboard.html",
        tema=estado_proceso["tema"],
        logs=estado_proceso["logs"],
        fuentes=datos["fuentes"],
        sentimiento_global=datos["sentimiento_global"],
        # AGREGAR ESTA LÍNEA ↓
        analisis_llm=datos["analisis_llm"]
    )


@app.route("/iniciar", methods=["POST"])
def iniciar():
    tema = request.form.get("tema", "").strip()

    if not tema:
        return jsonify({"success": False}), 400

    reiniciar_estado(tema)

    thread = threading.Thread(target=proceso_completo, args=(tema,))
    thread.daemon = True
    thread.start()

    return jsonify({"success": True})


@app.route("/api/estado")
def api_estado():
    fase = estado_proceso["fase_actual"]
    return jsonify({
        "tema": estado_proceso["tema"],
        "fase_actual": fase,
        "fase_nombre": estado_proceso["fase_nombre"],
        "completado": estado_proceso["completado"],
        "error": estado_proceso["error"],
        "progreso_porcentaje": 100 if estado_proceso["completado"] else (50 if fase > 0 else 0),
    })


@app.route("/api/logs")
def api_logs():
    nuevos_logs = []
    while not log_queue.empty():
        try:
            nuevos_logs.append(log_queue.get_nowait())
        except queue.Empty:
            break

    return jsonify({
        "logs": nuevos_logs,
        "completado": estado_proceso["completado"],
    })


@app.route("/api/resultados")
def api_resultados():
    return jsonify(obtener_datos_dashboard())


# ============================================================
# EJECUTAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Iniciando Sistema de Procesamiento")
    print("=" * 60)
    print(f"URL: http://localhost:5000")
    print(f"Timeout: {TIMEOUT_PROCESO}s ({TIMEOUT_PROCESO/60:.0f} min)")
    print("=" * 60)

    app.run(debug=False, host="0.0.0.0", port=5000)