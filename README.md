## Hola.

FASE 4: ANÁLISIS ESTADÍSTICO EN PYTHON

    Análisis de polaridad automatizado
    Frecuencia de palabras
    N-gramas
    TF-IDF
    Detección de palabras con carga emocional ⭐
    Análisis de negaciones ⭐
    Estadísticas generales

# DETALLADO

FASE 2: ANÁLISIS ESTADÍSTICO COMPLETO EN PYTHON
Ejecutas todas las técnicas y mantienes todo en memoria (variables Python):

Análisis de polaridad automatizado

Clasificación por comentario
Scores y métricas globales


Frecuencia de palabras

General y por sentimiento


N-gramas

Bigramas y trigramas


TF-IDF

Palabras distintivas por sentimiento


Detección de palabras con carga emocional ⭐

Scores emocionales
Top palabras positivas/negativas


Análisis de negaciones ⭐

Conteo de negaciones
Bigramas con negación
Palabras más negadas


Estadísticas generales

Longitudes, distribuciones, etc.



Resultado: Todas las métricas y datos en diccionarios/variables Python (aún NO guardadas en JSON)

---


Crea un diagrama de flujo profesional y claro que represente el proceso 
completo de análisis de sentimientos de comentarios de redes sociales. 
El diagrama debe mostrar las siguientes fases:

FASE 1: EXTRACCIÓN DE DATOS
- Obtención de comentarios de red social sobre un tema específico
- Almacenamiento en CSV (columnas: id, texto, fecha, fuente)

FASE 2: LIMPIEZA DE DATOS
- Eliminación de URLs, menciones, hashtags
- Corrección de caracteres especiales
- Normalización de texto (mayúsculas/minúsculas)
- Eliminación de duplicados
- Eliminación de emoticones
- Manejo de valores nulos
→ Resultado: CSV limpio

FASE 3: PREPROCESAMIENTO NLP
- Tokenización (división en palabras)
- Eliminación de stopwords (conservando negaciones)
- Lemmatización (reducción a forma base)
→ Resultado: CSV procesado y listo para análisis

FASE 4: ANÁLISIS ESTADÍSTICO EN PYTHON
Análisis automatizado de polaridad (TextBlob/VADER/Transformers):
  - Clasificación: Positivo/Negativo/Neutral
  - Score de polaridad (-1 a +1)
  - Score de subjetividad (0 a 1)

Análisis de frecuencias:
  - Top palabras más usadas (general)
  - Top palabras por sentimiento

Análisis de N-gramas:
  - Bigramas más frecuentes (general y por sentimiento)
  - Trigramas más frecuentes (general y por sentimiento)

Análisis TF-IDF:
  - Palabras distintivas por sentimiento

Estadísticas generales:
  - Distribución de sentimientos (%)
  - Polaridad promedio
  - Intensidad promedio
  - Longitud de comentarios por sentimiento
→ Resultado: CSV enriquecido + métricas estadísticas

FASE 5: GENERACIÓN DE RESUMEN ESTRUCTURADO
- Compilación de todos los resultados numéricos
- Creación de documento resumen con:
  * Distribución de sentimientos
  * Top palabras generales y por sentimiento
  * N-gramas más frecuentes
  * Palabras distintivas (TF-IDF)
  * Métricas clave
→ Resultado: Documento resumen estructurado

FASE 6: INTERPRETACIÓN CON LLM
- Envío del resumen al LLM (1 sola llamada)
- Solicitud de interpretación cualitativa:
  * Sentimiento predominante
  * Aspectos positivos identificados
  * Aspectos negativos identificados
  * Patrones e insights
  * Conclusiones principales
  * Recomendaciones
→ Resultado: Interpretación cualitativa profesional

FASE 7: VISUALIZACIONES
- Gráficos de distribución de sentimientos
- WordClouds (general y por sentimiento)
- Gráficos de barras (top palabras)
- Gráficos de N-gramas
- Heatmaps de TF-IDF
- Distribución de polaridad
→ Resultado: Dashboard visual

FASE 8: PRESENTACIÓN FINAL
- Combinación de:
  * Análisis cuantitativo (números y estadísticas)
  * Interpretación cualitativa (insights del LLM)
  * Visualizaciones (gráficos y nubes de palabras)
- Conclusiones sobre sentimientos predominantes del tema
- Recomendaciones accionables

Usa colores diferenciados para cada fase principal.
Incluye flechas claras que muestren el flujo de datos.
Marca con iconos o símbolos cada tipo de análisis.
Resalta que solo se usa el LLM UNA VEZ al final (para ahorrar costos).
El estilo debe ser profesional, limpio y fácil de entender para presentar 
a un equipo técnico.


# LLM CONSULTA
ANÁLISIS DE SENTIMIENTOS - [TEMA DE LA RED SOCIAL]
Fecha de análisis: [FECHA]
Total de comentarios analizados: [N]

========================================
DISTRIBUCIÓN DE SENTIMIENTOS
========================================
- Comentarios Positivos: [N] ([%]%)
- Comentarios Negativos: [N] ([%]%)
- Comentarios Neutrales: [N] ([%]%)

Polaridad promedio general: [valor]
Intensidad promedio: [valor]

========================================
MÉTRICAS DE POLARIDAD POR SENTIMIENTO
========================================
Positivos:
  - Polaridad promedio: [valor]
  - Rango: [min] a [max]

Negativos:
  - Polaridad promedio: [valor]
  - Rango: [min] a [max]

Neutrales:
  - Polaridad promedio: [valor]
  - Rango: [min] a [max]

========================================
TOP 20 PALABRAS MÁS FRECUENTES (GENERAL)
========================================
1. [palabra]: [N] veces
2. [palabra]: [N] veces
...

========================================
PALABRAS MÁS FRECUENTES EN POSITIVOS
========================================
1. [palabra]: [N] veces
...

========================================
PALABRAS MÁS FRECUENTES EN NEGATIVOS
========================================
1. [palabra]: [N] veces
...

========================================
BIGRAMAS MÁS COMUNES EN POSITIVOS
========================================
1. "[bigrama]": [N] veces
...

========================================
BIGRAMAS MÁS COMUNES EN NEGATIVOS
========================================
1. "[bigrama]": [N] veces
...

========================================
TRIGRAMAS MÁS COMUNES EN NEGATIVOS
========================================
1. "[trigrama]": [N] veces
...

========================================
PALABRAS DISTINTIVAS (TF-IDF)
========================================
Características de sentimientos POSITIVOS:
1. [palabra] (TF-IDF: [score])
...

Características de sentimientos NEGATIVOS:
1. [palabra] (TF-IDF: [score])
...

========================================
ANÁLISIS DE CARGA EMOCIONAL
========================================
Total de palabras con carga positiva detectadas: [N]
Total de palabras con carga negativa detectadas: [N]
Ratio negativo/positivo: [valor]

Top 10 palabras con mayor carga POSITIVA:
1. [palabra] (score: +[N], frecuencia: [N] veces)
...

Top 10 palabras con mayor carga NEGATIVA:
1. [palabra] (score: -[N], frecuencia: [N] veces)
...

Distribución de emociones específicas:
- Alegría: [N] ocurrencias
- Tristeza: [N] ocurrencias
- Enojo: [N] ocurrencias
- Miedo: [N] ocurrencias
- Sorpresa: [N] ocurrencias
- Confianza: [N] ocurrencias

========================================
ANÁLISIS DE NEGACIONES
========================================
Total de negaciones encontradas: [N]
Comentarios con al menos una negación: [N] ([%]%)

Negaciones por sentimiento:
- En positivos: [N] negaciones (promedio [X] por comentario)
- En negativos: [N] negaciones (promedio [X] por comentario)
- En neutrales: [N] negaciones (promedio [X] por comentario)

Bigramas con negación más frecuentes:
1. "[bigrama]": [N] veces
2. "[bigrama]": [N] veces
...

Palabras más frecuentemente negadas:
1. "[palabra]" → negada [N] veces
2. "[palabra]" → negada [N] veces
...

========================================
MÉTRICAS ADICIONALES
========================================
Longitud promedio de comentarios:
- General: [N] palabras
- Positivos: [N] palabras
- Negativos: [N] palabras
- Neutrales: [N] palabras


# LLM CONSULT V2

Eres un experto analista de sentimientos y ciencia de datos especializado 
en análisis de redes sociales. He realizado un análisis estadístico 
exhaustivo de comentarios sobre [TEMA] utilizando técnicas de procesamiento 
de lenguaje natural.

A continuación te presento los resultados completos del análisis:

[AQUÍ VA EL RESUMEN COMPLETO DE LA FASE 2]

Basándote ÚNICAMENTE en estos datos estadísticos, proporciona una 
interpretación profesional, clara y detallada que incluya:

1. Una descripción del sentimiento predominante y su intensidad
2. Los aspectos específicos del tema que generan sentimientos positivos
3. Los aspectos específicos del tema que generan sentimientos negativos
4. Patrones o tendencias relevantes identificados en los datos
5. Insights interesantes o sorprendentes que revelen los números
6. Conclusiones principales sobre la percepción general del tema
7. Recomendaciones accionables basadas en los hallazgos (si aplica)

Tu interpretación debe ser objetiva, basada en evidencia, y expresada 
en un lenguaje profesional pero accesible. Evita especular más allá de 
lo que los datos muestran.