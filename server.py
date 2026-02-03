#!/usr/bin/env python3
"""
Servidor Flask — Sistema de Procesamiento Analítico
Arquitectura multi-fase con dashboard de resultados.
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

app = Flask(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================
CARPETA_RESULTADOS = "resultados"


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

# Cola para logs en tiempo real (permite polling sin duplicados)
log_queue = queue.Queue()

NOMBRES_FASES = {
    1: "Preparación de Datos",
    2: "Limpieza de Datos",
    3: "Procesamiento Analítico",
}


# ============================================================
# LÓGICA DE PROCESAMIENTO (Fases)
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


def ejecutar_fase(numero_fase, tema):
    """
    Ejecuta el script de una fase y captura su output línea por línea.
    Lanza excepción si el proceso termina con código != 0.
    """
    estado_proceso["fase_actual"] = numero_fase
    estado_proceso["fase_nombre"] = NOMBRES_FASES[numero_fase]

    try:
        proceso = subprocess.Popen(
            ## Cambio por MAIN
            [sys.executable, "main.py", str(numero_fase), tema],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for linea in proceso.stdout:
            linea = linea.strip()
            if linea:
                registrar_log(numero_fase, linea)

        proceso.wait()

        if proceso.returncode != 0:
            raise Exception(f"Fase {numero_fase} falló con código {proceso.returncode}")

    except Exception as e:
        registrar_log(numero_fase, f"❌ ERROR: {e}")
        raise


def proceso_completo(tema):
    """Ejecuta las 3 fases secuencialmente. Se ejecuta en un thread separado."""
    try:
        estado_proceso["timestamp_inicio"] = datetime.now().isoformat()

        for fase in range(1, 4):
            ejecutar_fase(fase, tema)

        estado_proceso["completado"] = True
        estado_proceso["timestamp_fin"] = datetime.now().isoformat()
        registrar_log(3, "✓ Proceso completo finalizado exitosamente")

    except Exception as e:
        estado_proceso["error"] = str(e)
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
# LÓGICA DE RESULTADOS (lectura de archivos)
# ============================================================

def leer_archivos_resultados():
    """
    Escanea la carpeta de resultados y agrupa archivos por fuente.
    Devuelve un dict con estructura:
        {
            "facebook": { "json": {...}, "csv": [...] },
            "linkedin": { "json": {...}, "csv": [...] },
            ...
        }
    """
    fuentes = {}

    if not os.path.exists(CARPETA_RESULTADOS):
        return fuentes

    for nombre_archivo in os.listdir(CARPETA_RESULTADOS):
        ruta = os.path.join(CARPETA_RESULTADOS, nombre_archivo)
        # Extraer nombre de fuente (todo antes del primer guión bajo)
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
    """
    Suma los conteos de sentimiento (POSITIVO/NEGATIVO/NEUTRAL)
    de todos los CSVs y devuelve el resumen global.
    """
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

    # Determinar cuál predomina
    predomina = max(conteo, key=lambda k: conteo[k] if k != "total" else -1)
    conteo["predomina"] = predomina

    return conteo


def generar_llm_global(sentimiento_global):
    """
    Envía el resumen numérico al modelo Gemini para obtener un análisis global interpretado.
    """

    # Clave de la API de Google Gemini
    API_KEY = ""

    prompt = f"""
    Aquí tienes un resumen de sentimiento agregado de múltiples redes sociales:

    - Positivos: {sentimiento_global['positivo']}
    - Negativos: {sentimiento_global['negativo']}
    - Neutrales: {sentimiento_global['neutral']}

    Total analizado: {sentimiento_global['total']}
    Sentimiento predominante: {sentimiento_global['predomina']}

    Proporciona un análisis interpretado en un solo párrafo, con texto limpio y lenguaje sencillo, 
    sin incluir listas ni datos numéricos dentro de la explicación. 
    Describe de manera general qué significado tiene el resultado obtenido, 
    qué tan fuerte es la polarización del público, 
    qué nivel aproximado de confiabilidad podría tener la tendencia observada y 
    qué conclusiones razonables se pueden tomar del panorama completo.
    """

    try:
        # --- Cliente Gemini ---
        import google.genai as genai
        genai.configure(api_key=API_KEY)

        model = genai.GenerativeModel("gemini-3-flash-preview")

        response = model.generate_content(prompt)

        # La respuesta viene en response.text
        return response.text.strip()

    except Exception as e:
        return f"Error en análisis por LLM (Gemini): {str(e)}"


def obtener_datos_dashboard():
    """
    Punto de entrada principal para el dashboard.
    Retorna todo lo que necesita la plantilla:
        - fuentes con sus JSONs y CSVs
        - sentimiento global consolidado
    """
    fuentes = leer_archivos_resultados()
    sentimiento_global = calcular_sentimiento_global(fuentes)
    analisis_llm = generar_llm_global(sentimiento_global)

    return {
        "fuentes": fuentes,
        "sentimiento_global": sentimiento_global,
        "analisis_llm": analisis_llm,
    }


# ============================================================
# ENDPOINTS — Páginas
# ============================================================

@app.route("/")
def index():
    """Pantalla inicial con formulario de búsqueda."""
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    """Dashboard de resultados. Redirige al inicio si el proceso no termina."""
    if not estado_proceso["completado"]:
        return redirect(url_for("index"))

    datos = obtener_datos_dashboard()

    return render_template(
        "dashboard.html",
        tema=estado_proceso["tema"],
        logs=estado_proceso["logs"],
        fuentes=datos["fuentes"],
        sentimiento_global=datos["sentimiento_global"],
    )


# ============================================================
# ENDPOINTS — API (polling y datos)
# ============================================================

@app.route("/iniciar", methods=["POST"])
def iniciar():
    """Inicia el procesamiento en background a partir del tema enviado."""
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
    """Retorna el estado actual del proceso (usado por polling en index.html)."""
    fase = estado_proceso["fase_actual"]
    return jsonify({
        "tema": estado_proceso["tema"],
        "fase_actual": fase,
        "fase_nombre": estado_proceso["fase_nombre"],
        "completado": estado_proceso["completado"],
        "error": estado_proceso["error"],
        "progreso_porcentaje": (fase / 3 * 100) if fase > 0 else 0,
    })


@app.route("/api/logs")
def api_logs():
    """Retorna solo los logs nuevos desde la última consulta (polling)."""
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
    """Retorna todos los datos de resultados para consumo externo."""
    return jsonify(obtener_datos_dashboard())


# ============================================================
# EJECUTAR SERVIDOR
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Iniciando Sistema de Procesamiento por Fases")
    print("=" * 60)
    print(f"📍 URL: http://localhost:5000")
    print(f"⚙️  Modo: Desarrollo (debug=True)")
    print("=" * 60)

    app.run(debug=True, host="0.0.0.0", port=5000)