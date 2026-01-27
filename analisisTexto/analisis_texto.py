import pandas as pd
from pathlib import Path
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.util import ngrams

# ===============================
# CARGAR DATOS LIMPIOS
# ===============================
archivos = [
    "datos_limpios/X_limpio.csv",
    "datos_limpios/linkedin_limpio.csv",
    "datos_limpios/facebook_limpio.csv",
    "datos_limpios/reddit_limpio.csv",
]

textos = []

for archivo in archivos:
    ruta = Path(archivo)
    if ruta.exists():
        df = pd.read_csv(ruta, encoding="utf-8")
        textos.extend(df["contenido"].dropna().tolist())

texto_total = " ".join(textos)

#print(f"Total documentos: {len(textos)}")
print(f"Total caracteres: {len(texto_total)}")

# ===============================
# A) BOLSA DE PALABRAS
# ===============================
wordcloud = WordCloud(
    width=1200,
    height=800,
    background_color="white",
    collocations=False
).generate(texto_total)

plt.figure(figsize=(14, 8))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("Bolsa de palabras - Nicolas Madura Capturado", fontsize=20)
plt.show()


print("==========Parte B: Análisis de Texto==========")
# ===============================
# B) FRECUENCIA DE PALABRAS
# ===============================
print("==============================")
print("\nTop 5 palabras más frecuentes por red social:\n")

for archivo in archivos:
    ruta = Path(archivo)
    if not ruta.exists():
        continue

    df = pd.read_csv(ruta, encoding="utf-8")
    textos_red = df["contenido"].dropna().tolist()
    texto_red = " ".join(textos_red)

    palabras = texto_red.split()
    frecuencias = Counter(palabras)

    nombre_red = archivo.replace("_posts_ram_2026_limpio.csv", "").upper()

    print(f"--- {nombre_red} ---")
    for palabra, freq in frecuencias.most_common(5):
        print(f"{palabra:15s} -> {freq}")
    print()


# ===============================
# B) TF-IDF (PALABRAS MÁS RELEVANTES)
# ===============================
vectorizer = TfidfVectorizer(max_features=20)
tfidf = vectorizer.fit_transform(textos)

palabras_tfidf = vectorizer.get_feature_names_out()
importancias = tfidf.sum(axis=0).A1

tfidf_resultado = sorted(
    zip(palabras_tfidf, importancias),
    key=lambda x: x[1],
    reverse=True
)

print("==============================")
print("\nTop 20 palabras por TF-IDF(Global):")
for palabra, score in tfidf_resultado:
    print(f"{palabra:15s} -> {score:.4f}")

# ===============================
# B) BIGRAMAS (PARES DE PALABRAS)
# ===============================
bigramas = []
for texto in textos:
    tokens = texto.split()
    bigramas.extend(list(ngrams(tokens, 2)))

frecuencia_bigramas = Counter(bigramas)

print("==============================")
print("\nTop 15 bigramas más comunes(Global):")
for bigrama, freq in frecuencia_bigramas.most_common(15):
    print(f"{bigrama[0]} {bigrama[1]} -> {freq}")
