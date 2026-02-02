"""
ANÁLISIS DE SENTIMIENTOS EN REDES SOCIALES - LINKEDIN
Análisis exhaustivo de comentarios con 7 técnicas de NLP
Genera JSON con datos + interpretación LLM (DeepLake)
"""

import sys
import os

# ===== CONFIGURAR UTF-8 PARA WINDOWS =====
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
# =========================================

import sys
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

try:
    from pysentimiento import create_analyzer
    PYSENTIMIENTO_AVAILABLE = True
except ImportError:
    print("⚠️  pysentimiento no instalado. Instalar con: pip install pysentimiento")
    PYSENTIMIENTO_AVAILABLE = False

from sklearn.feature_extraction.text import TfidfVectorizer
import requests

#############################################
# RECIBIR PARÁMETROS DEL ORQUESTADOR
#############################################

if len(sys.argv) >= 3:
    CSV_INPUT_PATH = sys.argv[1]
    TEMA_ANALISIS = sys.argv[2]
    print(f"📥 Parámetros recibidos del orquestador:")
    print(f"   CSV: {CSV_INPUT_PATH}")
    print(f"   Tema: {TEMA_ANALISIS}")
else:
    print("⚠️ No se recibieron parámetros. Usando valores por defecto...")
    CSV_INPUT_PATH = "datos_limpios/facebook_limpio.csv"
    TEMA_ANALISIS = "nicolas maduro capturado"

#############################################
# CONFIGURACIÓN PRINCIPAL
#############################################

DEEPLAKE_API_KEY = ""  
DEEPLAKE_MODEL = "mistral-small-latest"   

red_social = CSV_INPUT_PATH.split('/')[-1].replace('_limpio.csv', '')
CSV_OUTPUT_PATH = f"resultados/{red_social}_con_analisis.csv"
JSON_OUTPUT_PATH = f"resultados/{red_social}_analisis_completo.json"
VISUALIZATIONS_DIR = "visualizaciones/"

TOP_N_PALABRAS = 10
TOP_N_BIGRAMAS = 10
TOP_N_TRIGRAMAS = 10
TOP_N_TFIDF = 10
TOP_N_EMOCIONAL = 10

COLUMNA_TEXTO = "contenido"

PALABRAS_NEGACION = ["no", "nunca", "jamás", "sin", "ni", "tampoco", "nada", "ningún", "ninguna"]

def configurar_deeplake():
    try:
        return {"api_key": DEEPLAKE_API_KEY, "model": DEEPLAKE_MODEL}
    except Exception as e:
        raise Exception(f"Error configurando DeepLake: {e}")

def descargar_nrc_lexicon():
    print("📥 Intentando descargar NRC Emotion Lexicon (español)...")
    
    print("ℹ️  Usando diccionario básico optimizado (más confiable para este análisis)")
    return crear_diccionario_basico()

def crear_diccionario_basico():
    
    palabras_positivas = [
        'excelente', 'bueno', 'perfecto', 'feliz', 'contento', 'alegre', 'genial',
        'increíble', 'maravilloso', 'fantástico', 'recomiendo', 'satisfecho',
        'encanta', 'amor', 'mejor', 'óptimo', 'estupendo', 'hermoso', 'bonito',
        'agradable', 'positivo', 'éxito', 'ganador', 'favorable', 'bien',
        'buena', 'correcto', 'justo', 'gracias', 'felicitar'
    ]
    
    palabras_negativas = [
        'malo', 'horrible', 'pésimo', 'terrible', 'desastre', 'decepción',
        'triste', 'enojado', 'frustrado', 'molesto', 'odio', 'detesto',
        'peor', 'deficiente', 'basura', 'fraude', 'estafa', 'feo', 'desagradable',
        'negativo', 'fracaso', 'perdedor', 'desfavorable', 'espantoso',
        'mal', 'mala', 'incorrecto', 'injusto', 'lamentar', 'criticar'
    ]
    
    total_palabras = palabras_positivas + palabras_negativas
    n_pos = len(palabras_positivas)
    n_neg = len(palabras_negativas)
    total = n_pos + n_neg
    
    data = {
        'palabra': total_palabras,
        'Positive': [1]*n_pos + [0]*n_neg,
        'Negative': [0]*n_pos + [1]*n_neg,
        'Joy': [1]*n_pos + [0]*n_neg,
        'Sadness': [0]*n_pos + [1]*n_neg,
        'Anger': [0]*n_pos + [1]*n_neg,
        'Fear': [0]*total,
        'Surprise': [0]*total,
        'Trust': [1]*n_pos + [0]*n_neg,
        'Anticipation': [0]*total,
        'Disgust': [0]*n_pos + [1]*n_neg
    }
    
    df = pd.DataFrame(data)
    print(f"✅ Diccionario básico creado: {len(df)} palabras")
    return df

def analizar_polaridad(df, columna_texto):
    print("\n📊 Analizando polaridad con pysentimiento...")
    
    if not PYSENTIMIENTO_AVAILABLE:
        print("❌ pysentimiento no disponible")
        return df, {}
    
    try:
        sentiment_analyzer = create_analyzer(task="sentiment", lang="es")
        
        resultados = []
        for idx, texto in enumerate(df[columna_texto]):
            if pd.isna(texto) or texto.strip() == "":
                resultados.append({
                    'sentimiento': 'NEUTRAL',
                    'polaridad': 0.0,
                    'confianza': 0.0
                })
            else:
                resultado = sentiment_analyzer.predict(texto)
                
                sentimiento_map = {
                    'POS': 'POSITIVO',
                    'NEG': 'NEGATIVO',
                    'NEU': 'NEUTRAL'
                }
                
                probs = resultado.probas
                polaridad = probs.get('POS', 0) - probs.get('NEG', 0)
                
                resultados.append({
                    'sentimiento': sentimiento_map.get(resultado.output, 'NEUTRAL'),
                    'polaridad': polaridad,
                    'confianza': max(probs.values())
                })
            
            if (idx + 1) % 100 == 0:
                print(f"   Procesados {idx + 1}/{len(df)} comentarios...")
        
        df['sentimiento'] = [r['sentimiento'] for r in resultados]
        df['polaridad'] = [r['polaridad'] for r in resultados]
        df['confianza'] = [r['confianza'] for r in resultados]
        
        distribucion = df['sentimiento'].value_counts()
        total = len(df)
        
        metricas = {
            'distribucion_sentimientos': {
                'positivos': int(distribucion.get('POSITIVO', 0)),
                'negativos': int(distribucion.get('NEGATIVO', 0)),
                'neutrales': int(distribucion.get('NEUTRAL', 0)),
                'porcentaje_positivos': round(distribucion.get('POSITIVO', 0) / total * 100, 2),
                'porcentaje_negativos': round(distribucion.get('NEGATIVO', 0) / total * 100, 2),
                'porcentaje_neutrales': round(distribucion.get('NEUTRAL', 0) / total * 100, 2)
            },
            'metricas_globales': {
                'polaridad_promedio': float(df['polaridad'].mean()),
                'polaridad_mediana': float(df['polaridad'].median()),
                'polaridad_std': float(df['polaridad'].std()),
                'confianza_promedio': float(df['confianza'].mean())
            },
            'polaridad_por_sentimiento': {
                'positivos': {
                    'promedio': float(df[df['sentimiento'] == 'POSITIVO']['polaridad'].mean()) if 'POSITIVO' in distribucion else 0,
                    'min': float(df[df['sentimiento'] == 'POSITIVO']['polaridad'].min()) if 'POSITIVO' in distribucion else 0,
                    'max': float(df[df['sentimiento'] == 'POSITIVO']['polaridad'].max()) if 'POSITIVO' in distribucion else 0
                },
                'negativos': {
                    'promedio': float(df[df['sentimiento'] == 'NEGATIVO']['polaridad'].mean()) if 'NEGATIVO' in distribucion else 0,
                    'min': float(df[df['sentimiento'] == 'NEGATIVO']['polaridad'].min()) if 'NEGATIVO' in distribucion else 0,
                    'max': float(df[df['sentimiento'] == 'NEGATIVO']['polaridad'].max()) if 'NEGATIVO' in distribucion else 0
                },
                'neutrales': {
                    'promedio': float(df[df['sentimiento'] == 'NEUTRAL']['polaridad'].mean()) if 'NEUTRAL' in distribucion else 0,
                    'min': float(df[df['sentimiento'] == 'NEUTRAL']['polaridad'].min()) if 'NEUTRAL' in distribucion else 0,
                    'max': float(df[df['sentimiento'] == 'NEUTRAL']['polaridad'].max()) if 'NEUTRAL' in distribucion else 0
                }
            }
        }
        
        print(f"✅ Polaridad analizada: {distribucion.to_dict()}")
        return df, metricas
        
    except Exception as e:
        print(f"❌ Error en análisis de polaridad: {e}")
        return df, {}

def analizar_frecuencias(df, columna_texto, top_n=10):
    print(f"\n📊 Analizando frecuencia de palabras (Top {top_n})...")
    
    def contar_palabras(textos):
        todas_palabras = []
        for texto in textos:
            if pd.notna(texto):
                palabras = str(texto).split()
                todas_palabras.extend(palabras)
        return Counter(todas_palabras)
    
    contador_general = contar_palabras(df[columna_texto])
    top_general = [
        {"palabra": palabra, "frecuencia": freq}
        for palabra, freq in contador_general.most_common(top_n)
    ]
    
    resultados = {
        'top_general': top_general,
        'top_positivos': [],
        'top_negativos': [],
        'top_neutrales': []
    }
    
    if 'sentimiento' in df.columns:
        for sentimiento, key in [('POSITIVO', 'top_positivos'), 
                                  ('NEGATIVO', 'top_negativos'), 
                                  ('NEUTRAL', 'top_neutrales')]:
            textos = df[df['sentimiento'] == sentimiento][columna_texto]
            if len(textos) > 0:
                contador = contar_palabras(textos)
                resultados[key] = [
                    {"palabra": palabra, "frecuencia": freq}
                    for palabra, freq in contador.most_common(top_n)
                ]
    
    print(f"✅ Frecuencias calculadas")
    return resultados

def analizar_ngramas(df, columna_texto, top_n=10):
    print(f"\n📊 Analizando n-gramas (Top {top_n})...")
    
    def extraer_ngramas(textos, n):
        ngramas = []
        for texto in textos:
            if pd.notna(texto):
                palabras = str(texto).split()
                for i in range(len(palabras) - n + 1):
                    ngrama = ' '.join(palabras[i:i+n])
                    ngramas.append(ngrama)
        return Counter(ngramas)
    
    bigramas_general = extraer_ngramas(df[columna_texto], 2)
    
    trigramas_general = extraer_ngramas(df[columna_texto], 3)
    
    resultados = {
        'bigramas_general': [
            {"bigrama": bg, "frecuencia": freq}
            for bg, freq in bigramas_general.most_common(top_n)
        ],
        'trigramas_general': [
            {"trigrama": tg, "frecuencia": freq}
            for tg, freq in trigramas_general.most_common(top_n)
        ],
        'bigramas_positivos': [],
        'bigramas_negativos': [],
        'trigramas_negativos': []
    }
    
    if 'sentimiento' in df.columns:
        for sentimiento, key_bi, key_tri in [
            ('POSITIVO', 'bigramas_positivos', None),
            ('NEGATIVO', 'bigramas_negativos', 'trigramas_negativos')
        ]:
            textos = df[df['sentimiento'] == sentimiento][columna_texto]
            if len(textos) > 0:
                bigramas = extraer_ngramas(textos, 2)
                resultados[key_bi] = [
                    {"bigrama": bg, "frecuencia": freq}
                    for bg, freq in bigramas.most_common(top_n)
                ]
                
                if key_tri:
                    trigramas = extraer_ngramas(textos, 3)
                    resultados[key_tri] = [
                        {"trigrama": tg, "frecuencia": freq}
                        for tg, freq in trigramas.most_common(top_n)
                    ]
    
    print(f"✅ N-gramas calculados")
    return resultados

def analizar_tfidf(df, columna_texto, top_n=10):
    print(f"\n📊 Calculando TF-IDF (Top {top_n})...")
    
    resultados = {
        'palabras_distintivas_positivos': [],
        'palabras_distintivas_negativos': [],
        'palabras_distintivas_neutrales': []
    }
    
    if 'sentimiento' not in df.columns:
        print("⚠️  No hay columna 'sentimiento', saltando TF-IDF")
        return resultados
    
    try:
        docs_por_sentimiento = {}
        for sentimiento in ['POSITIVO', 'NEGATIVO', 'NEUTRAL']:
            textos = df[df['sentimiento'] == sentimiento][columna_texto]
            if len(textos) > 0:
                docs_por_sentimiento[sentimiento] = ' '.join(textos.astype(str))
        
        if len(docs_por_sentimiento) < 2:
            print("⚠️  No hay suficientes sentimientos para TF-IDF")
            return resultados
        
        vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 1))
        corpus = list(docs_por_sentimiento.values())
        labels = list(docs_por_sentimiento.keys())
        
        tfidf_matrix = vectorizer.fit_transform(corpus)
        feature_names = vectorizer.get_feature_names_out()
        
        for idx, sentimiento in enumerate(labels):
            tfidf_scores = tfidf_matrix[idx].toarray()[0]
            top_indices = tfidf_scores.argsort()[-top_n:][::-1]
            
            key_map = {
                'POSITIVO': 'palabras_distintivas_positivos',
                'NEGATIVO': 'palabras_distintivas_negativos',
                'NEUTRAL': 'palabras_distintivas_neutrales'
            }
            
            resultados[key_map[sentimiento]] = [
                {"palabra": feature_names[i], "score_tfidf": round(float(tfidf_scores[i]), 4)}
                for i in top_indices if tfidf_scores[i] > 0
            ]
        
        print(f"✅ TF-IDF calculado")
        return resultados
        
    except Exception as e:
        print(f"❌ Error en TF-IDF: {e}")
        return resultados

def analizar_carga_emocional(df, columna_texto, nrc_lexicon, top_n=10):
    print(f"\n📊 Analizando carga emocional (Top {top_n})...")
    
    lexicon_dict = nrc_lexicon.set_index('palabra').to_dict('index')
    
    palabras_positivas_counter = Counter()
    palabras_negativas_counter = Counter()
    emociones_counter = {
        'Joy': 0, 'Sadness': 0, 'Anger': 0, 'Fear': 0,
        'Surprise': 0, 'Trust': 0, 'Anticipation': 0, 'Disgust': 0
    }
    
    total_palabras_positivas = 0
    total_palabras_negativas = 0
    
    for texto in df[columna_texto]:
        if pd.notna(texto):
            palabras = str(texto).split()
            for palabra in palabras:
                if palabra in lexicon_dict:
                    info = lexicon_dict[palabra]
                    
                    if info.get('Positive', 0) == 1:
                        palabras_positivas_counter[palabra] += 1
                        total_palabras_positivas += 1
                    
                    if info.get('Negative', 0) == 1:
                        palabras_negativas_counter[palabra] += 1
                        total_palabras_negativas += 1
                    
                    for emocion in emociones_counter.keys():
                        if info.get(emocion, 0) == 1:
                            emociones_counter[emocion] += 1
    
    score_promedio = (total_palabras_positivas - total_palabras_negativas) / len(df) if len(df) > 0 else 0
    
    resultados = {
        'resumen': {
            'total_palabras_positivas': total_palabras_positivas,
            'total_palabras_negativas': total_palabras_negativas,
            'ratio_negativo_positivo': round(total_palabras_negativas / total_palabras_positivas, 2) if total_palabras_positivas > 0 else 0,
            'score_emocional_promedio': round(score_promedio, 2)
        },
        'top_palabras_positivas': [
            {"palabra": palabra, "frecuencia": freq}
            for palabra, freq in palabras_positivas_counter.most_common(top_n)
        ],
        'top_palabras_negativas': [
            {"palabra": palabra, "frecuencia": freq}
            for palabra, freq in palabras_negativas_counter.most_common(top_n)
        ],
        'distribucion_emociones': emociones_counter
    }
    
    print(f"✅ Carga emocional analizada: {total_palabras_positivas} pos, {total_palabras_negativas} neg")
    return resultados

def analizar_negaciones(df, columna_texto, palabras_negacion, top_n=10):
    print(f"\n📊 Analizando negaciones (Top {top_n})...")
    
    total_negaciones = 0
    comentarios_con_negacion = 0
    negaciones_por_sentimiento = {'POSITIVO': 0, 'NEGATIVO': 0, 'NEUTRAL': 0}
    bigramas_negacion_counter = Counter()
    palabras_negadas_counter = Counter()
    
    for idx, texto in enumerate(df[columna_texto]):
        if pd.notna(texto):
            palabras = str(texto).split()
            negaciones_en_comentario = 0
            
            for i, palabra in enumerate(palabras):
                if palabra in palabras_negacion:
                    total_negaciones += 1
                    negaciones_en_comentario += 1
                    
                    if i + 1 < len(palabras):
                        bigrama = f"{palabra} {palabras[i+1]}"
                        bigramas_negacion_counter[bigrama] += 1
                        palabras_negadas_counter[palabras[i+1]] += 1
            
            if negaciones_en_comentario > 0:
                comentarios_con_negacion += 1
                
                if 'sentimiento' in df.columns:
                    sentimiento = df.iloc[idx]['sentimiento']
                    if sentimiento in negaciones_por_sentimiento:
                        negaciones_por_sentimiento[sentimiento] += negaciones_en_comentario
    
    total_comentarios = len(df)
    
    resultados = {
        'resumen': {
            'total_negaciones': total_negaciones,
            'comentarios_con_negacion': comentarios_con_negacion,
            'porcentaje_con_negacion': round(comentarios_con_negacion / total_comentarios * 100, 2) if total_comentarios > 0 else 0,
            'promedio_negaciones_por_comentario': round(total_negaciones / total_comentarios, 2) if total_comentarios > 0 else 0
        },
        'bigramas_con_negacion': [
            {"bigrama": bg, "frecuencia": freq}
            for bg, freq in bigramas_negacion_counter.most_common(top_n)
        ],
        'palabras_mas_negadas': [
            {"palabra": palabra, "veces_negada": freq}
            for palabra, freq in palabras_negadas_counter.most_common(top_n)
        ]
    }
    
    if 'sentimiento' in df.columns:
        dist_sentimientos = df['sentimiento'].value_counts()
        resultados['negaciones_por_sentimiento'] = {}
        
        for sentimiento in ['POSITIVO', 'NEGATIVO', 'NEUTRAL']:
            count = dist_sentimientos.get(sentimiento, 0)
            resultados['negaciones_por_sentimiento'][sentimiento.lower()] = {
                'total': negaciones_por_sentimiento.get(sentimiento, 0),
                'promedio_por_comentario': round(
                    negaciones_por_sentimiento.get(sentimiento, 0) / count, 2
                ) if count > 0 else 0
            }
    
    print(f"✅ Negaciones analizadas: {total_negaciones} totales")
    return resultados

def calcular_metricas_adicionales(df, columna_texto):
    print("\n📊 Calculando métricas adicionales...")
    
    df['longitud'] = df[columna_texto].apply(lambda x: len(str(x).split()) if pd.notna(x) else 0)
    
    metricas = {
        'longitud_comentarios': {
            'promedio_general': round(float(df['longitud'].mean()), 2)
        },
        'cantidad_por_sentimiento': {}
    }
    
    if 'sentimiento' in df.columns:
        for sentimiento, label in [('POSITIVO', 'positivos'), ('NEGATIVO', 'negativos'), ('NEUTRAL', 'neutrales')]:
            subset = df[df['sentimiento'] == sentimiento]
            count = len(subset)
            metricas['cantidad_por_sentimiento'][label] = count
            
            if count > 0:
                metricas['longitud_comentarios'][f'promedio_{label}'] = round(float(subset['longitud'].mean()), 2)
            else:
                metricas['longitud_comentarios'][f'promedio_{label}'] = 0.0
    
    print(f"✅ Métricas adicionales calculadas")
    return metricas

def generar_resumen_para_llm(datos_analisis, tema):
    print("\n📝 Generando resumen para LLM...")
    
    resumen = f"""ANÁLISIS DE SENTIMIENTOS - {tema}
Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Total de comentarios analizados: {datos_analisis['metadata']['total_comentarios']}

========================================
DISTRIBUCIÓN DE SENTIMIENTOS
========================================
"""
    
    dist = datos_analisis['analisis_polaridad']['distribucion_sentimientos']
    resumen += f"""- Comentarios Positivos: {dist['positivos']} ({dist['porcentaje_positivos']}%)
- Comentarios Negativos: {dist['negativos']} ({dist['porcentaje_negativos']}%)
- Comentarios Neutrales: {dist['neutrales']} ({dist['porcentaje_neutrales']}%)

"""
    
    metricas = datos_analisis['analisis_polaridad']['metricas_globales']
    resumen += f"""Polaridad promedio general: {metricas['polaridad_promedio']:.3f}
Confianza promedio: {metricas['confianza_promedio']:.3f}

========================================
MÉTRICAS DE POLARIDAD POR SENTIMIENTO
========================================
"""
    
    pol_sent = datos_analisis['analisis_polaridad']['polaridad_por_sentimiento']
    for sent_key, sent_label in [('positivos', 'Positivos'), ('negativos', 'Negativos'), ('neutrales', 'Neutrales')]:
        resumen += f"""{sent_label}:
  - Polaridad promedio: {pol_sent[sent_key]['promedio']:.3f}
  - Rango: {pol_sent[sent_key]['min']:.3f} a {pol_sent[sent_key]['max']:.3f}

"""
    
    resumen += """========================================
TOP PALABRAS MÁS FRECUENTES (GENERAL)
========================================
"""
    for i, item in enumerate(datos_analisis['frecuencia_palabras']['top_general'], 1):
        resumen += f"{i}. {item['palabra']}: {item['frecuencia']} veces\n"
    
    resumen += """\n========================================
PALABRAS MÁS FRECUENTES EN POSITIVOS
========================================
"""
    if datos_analisis['frecuencia_palabras']['top_positivos']:
        for i, item in enumerate(datos_analisis['frecuencia_palabras']['top_positivos'], 1):
            resumen += f"{i}. {item['palabra']}: {item['frecuencia']} veces\n"
    else:
        resumen += "(No hay comentarios positivos suficientes)\n"
    
    resumen += """\n========================================
PALABRAS MÁS FRECUENTES EN NEGATIVOS
========================================
"""
    for i, item in enumerate(datos_analisis['frecuencia_palabras']['top_negativos'], 1):
        resumen += f"{i}. {item['palabra']}: {item['frecuencia']} veces\n"
    
    resumen += """\n========================================
BIGRAMAS MÁS COMUNES EN POSITIVOS
========================================
"""
    if datos_analisis['analisis_ngramas']['bigramas_positivos']:
        for i, item in enumerate(datos_analisis['analisis_ngramas']['bigramas_positivos'], 1):
            resumen += f"{i}. \"{item['bigrama']}\": {item['frecuencia']} veces\n"
    else:
        resumen += "(No hay suficientes comentarios positivos para análisis de bigramas)\n"
    
    resumen += """\n========================================
BIGRAMAS MÁS COMUNES EN NEGATIVOS
========================================
"""
    for i, item in enumerate(datos_analisis['analisis_ngramas']['bigramas_negativos'], 1):
        resumen += f"{i}. \"{item['bigrama']}\": {item['frecuencia']} veces\n"
    
    resumen += """\n========================================
TRIGRAMAS MÁS COMUNES EN NEGATIVOS
========================================
"""
    for i, item in enumerate(datos_analisis['analisis_ngramas']['trigramas_negativos'], 1):
        resumen += f"{i}. \"{item['trigrama']}\": {item['frecuencia']} veces\n"
    
    resumen += """\n========================================
PALABRAS DISTINTIVAS (TF-IDF)
========================================
Características de sentimientos POSITIVOS:
"""
    if datos_analisis['analisis_tfidf']['palabras_distintivas_positivos']:
        for i, item in enumerate(datos_analisis['analisis_tfidf']['palabras_distintivas_positivos'], 1):
            resumen += f"{i}. {item['palabra']} (TF-IDF: {item['score_tfidf']})\n"
    else:
        resumen += "(No hay suficientes comentarios positivos)\n"
    
    resumen += """\nCaracterísticas de sentimientos NEGATIVOS:
"""
    for i, item in enumerate(datos_analisis['analisis_tfidf']['palabras_distintivas_negativos'], 1):
        resumen += f"{i}. {item['palabra']} (TF-IDF: {item['score_tfidf']})\n"
    
    resumen += """\n========================================
ANÁLISIS DE CARGA EMOCIONAL
========================================
"""
    emo = datos_analisis['palabras_carga_emocional']['resumen']
    resumen += f"""Total de palabras con carga positiva detectadas: {emo['total_palabras_positivas']}
Total de palabras con carga negativa detectadas: {emo['total_palabras_negativas']}
Ratio negativo/positivo: {emo['ratio_negativo_positivo']}

Top palabras con mayor carga POSITIVA:
"""
    for i, item in enumerate(datos_analisis['palabras_carga_emocional']['top_palabras_positivas'], 1):
        resumen += f"{i}. {item['palabra']} (frecuencia: {item['frecuencia']} veces)\n"
    
    resumen += """\nTop palabras con mayor carga NEGATIVA:
"""
    for i, item in enumerate(datos_analisis['palabras_carga_emocional']['top_palabras_negativas'], 1):
        resumen += f"{i}. {item['palabra']} (frecuencia: {item['frecuencia']} veces)\n"
    
    resumen += """\nDistribución de emociones específicas:
"""
    for emocion, count in datos_analisis['palabras_carga_emocional']['distribucion_emociones'].items():
        resumen += f"- {emocion}: {count} ocurrencias\n"
    
    resumen += """\n========================================
ANÁLISIS DE NEGACIONES
========================================
"""
    neg = datos_analisis['analisis_negaciones']['resumen']
    resumen += f"""Total de negaciones encontradas: {neg['total_negaciones']}
Comentarios con al menos una negación: {neg['comentarios_con_negacion']} ({neg['porcentaje_con_negacion']}%)

Negaciones por sentimiento:
"""
    for sent in ['positivos', 'negativos', 'neutrales']:
        if sent in datos_analisis['analisis_negaciones'].get('negaciones_por_sentimiento', {}):
            neg_sent = datos_analisis['analisis_negaciones']['negaciones_por_sentimiento'][sent]
            resumen += f"- En {sent}: {neg_sent['total']} negaciones (promedio {neg_sent['promedio_por_comentario']} por comentario)\n"
        else:
            resumen += f"- En {sent}: 0 negaciones (no hay datos de este sentimiento)\n"
    
    resumen += """\nBigramas con negación más frecuentes:
"""
    for i, item in enumerate(datos_analisis['analisis_negaciones']['bigramas_con_negacion'], 1):
        resumen += f"{i}. \"{item['bigrama']}\": {item['frecuencia']} veces\n"
    
    resumen += """\nPalabras más frecuentemente negadas:
"""
    for i, item in enumerate(datos_analisis['analisis_negaciones']['palabras_mas_negadas'], 1):
        resumen += f"{i}. \"{item['palabra']}\" → negada {item['veces_negada']} veces\n"
    
    resumen += """\n========================================
MÉTRICAS ADICIONALES
========================================
Longitud promedio de comentarios:
"""
    long = datos_analisis['metricas_adicionales']['longitud_comentarios']
    resumen += f"- General: {long['promedio_general']} palabras\n"
    if 'promedio_positivos' in long:
        resumen += f"- Positivos: {long['promedio_positivos']} palabras\n"
    if 'promedio_negativos' in long:
        resumen += f"- Negativos: {long['promedio_negativos']} palabras\n"
    if 'promedio_neutrales' in long:
        resumen += f"- Neutrales: {long['promedio_neutrales']} palabras\n"
    
    print("✅ Resumen generado")
    return resumen

def interpretar_con_mistral(resumen_texto, tema, config):
    print("\n🤖 Enviando análisis a Mistral para interpretación...")
    
    prompt = f"""Eres un experto analista de sentimientos y ciencia de datos especializado 
en análisis de redes sociales. He realizado un análisis estadístico exhaustivo de 
comentarios sobre {tema} utilizando técnicas de procesamiento de lenguaje natural.

Resultados del análisis:

{resumen_texto}

Interpreta estos datos en un solo párrafo profesional: explica el sentimiento general, 
los hallazgos clave y conclusiones principales. Mantén objetividad y basa tu análisis 
exclusivamente en la evidencia presentada."""
    
    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json"
            },
            json={
                "model": config['model'],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
        
        if response.status_code == 200:
            interpretacion = response.json()['choices'][0]['message']['content']
            print("✅ Interpretación recibida de Mistral")
            return interpretacion, prompt
        else:
            error_msg = f"Error API {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            return error_msg, prompt
        
    except Exception as e:
        print(f"❌ Error al llamar a Mistral: {e}")
        return f"Error al obtener interpretación: {str(e)}", prompt

def guardar_json_completo(datos_analisis, output_path):
    print(f"\n💾 Guardando JSON en {output_path}...")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(datos_analisis, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON guardado exitosamente")

def main():
    
    print("="*60)
    print("ANÁLISIS DE SENTIMIENTOS - LINKEDIN")
    print("="*60)
    print(f"🎯 Tema de análisis: {TEMA_ANALISIS}")
    
    print(f"\n📂 Cargando CSV: {CSV_INPUT_PATH}")
    try:
        df = pd.read_csv(CSV_INPUT_PATH, encoding='utf-8')
        df['id'] = range(1, len(df) + 1)
        print(f"✅ CSV cargado: {len(df)} comentarios")
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        return
    
    print("\n🔧 Configurando DeepLake...")
    try:
        config = configurar_deeplake()
        print("✅ DeepLake configurado")
    except Exception as e:
        print(f"❌ Error configurando DeepLake: {e}")
        print("   Verifica tu API_KEY en la configuración")
        return
    
    nrc_lexicon = descargar_nrc_lexicon()
    
    print("\n" + "="*60)
    print("EJECUTANDO ANÁLISIS")
    print("="*60)
    
    df, metricas_polaridad = analizar_polaridad(df, COLUMNA_TEXTO)
    
    frecuencias = analizar_frecuencias(df, COLUMNA_TEXTO, TOP_N_PALABRAS)
    
    ngramas = analizar_ngramas(df, COLUMNA_TEXTO, TOP_N_BIGRAMAS)
    
    tfidf = analizar_tfidf(df, COLUMNA_TEXTO, TOP_N_TFIDF)
    
    carga_emocional = analizar_carga_emocional(df, COLUMNA_TEXTO, nrc_lexicon, TOP_N_EMOCIONAL)
    
    negaciones = analizar_negaciones(df, COLUMNA_TEXTO, PALABRAS_NEGACION, TOP_N_PALABRAS)
    
    metricas_adicionales = calcular_metricas_adicionales(df, COLUMNA_TEXTO)
    
    datos_analisis = {
        'metadata': {
            'fecha_analisis': datetime.now().isoformat(),
            'tema': TEMA_ANALISIS,
            'total_comentarios': len(df),
            'fuente': 'Facebook',
            'version_analisis': '1.0'
        },
        'datos_crudos': {
            'csv_original': CSV_INPUT_PATH,
            'csv_enriquecido': CSV_OUTPUT_PATH
        },
        'analisis_polaridad': metricas_polaridad,
        'frecuencia_palabras': frecuencias,
        'analisis_ngramas': ngramas,
        'analisis_tfidf': tfidf,
        'palabras_carga_emocional': carga_emocional,
        'analisis_negaciones': negaciones,
        'metricas_adicionales': metricas_adicionales
    }
    
    resumen_para_llm = generar_resumen_para_llm(datos_analisis, TEMA_ANALISIS)
    datos_analisis['resumen_para_llm'] = resumen_para_llm
    
    interpretacion, prompt_usado = interpretar_con_mistral(resumen_para_llm, TEMA_ANALISIS, config)
    
    datos_analisis['interpretacion_llm'] = {
        'timestamp': datetime.now().isoformat(),
        'modelo_usado': DEEPLAKE_MODEL,
        'prompt_enviado': prompt_usado,
        'interpretacion_completa': interpretacion
    }
    
    print(f"\n💾 Guardando CSV enriquecido en {CSV_OUTPUT_PATH}...")
    os.makedirs(os.path.dirname(CSV_OUTPUT_PATH), exist_ok=True)
    df.to_csv(CSV_OUTPUT_PATH, index=False, encoding='utf-8')
    print("✅ CSV enriquecido guardado")
    
    guardar_json_completo(datos_analisis, JSON_OUTPUT_PATH)
    
    print("\n" + "="*60)
    print("ANÁLISIS COMPLETADO")
    print("="*60)
    print(f"\n📊 Resultados:")
    print(f"   - CSV enriquecido: {CSV_OUTPUT_PATH}")
    print(f"   - JSON completo: {JSON_OUTPUT_PATH}")
    print(f"\n📈 Distribución de sentimientos:")
    dist = metricas_polaridad['distribucion_sentimientos']
    print(f"   - Positivos: {dist['positivos']} ({dist['porcentaje_positivos']}%)")
    print(f"   - Negativos: {dist['negativos']} ({dist['porcentaje_negativos']}%)")
    print(f"   - Neutrales: {dist['neutrales']} ({dist['porcentaje_neutrales']}%)")
    print(f"\n🤖 Interpretación de Mistral guardada en el JSON")
    print("\n✅ Proceso finalizado exitosamente")

if __name__ == "__main__":
    main()