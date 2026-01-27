import pandas as pd
import re
import unicodedata
from pathlib import Path
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from pathlib import Path

# ===============================
# DESCARGA DE RECURSOS NLTK
# ===============================
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("corpora/stopwords")
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("punkt", quiet=True)
    nltk.download("stopwords", quiet=True)
    nltk.download("wordnet", quiet=True)

# ===============================
# CONFIGURACIÓN NLP
# ===============================
lemmatizer = WordNetLemmatizer()
stopwords_es = set(stopwords.words("spanish"))

# ===============================
# CONFIGURACIÓN GUARDADO
# ===============================

RUTA_SALIDA = Path("datos_limpios")
RUTA_SALIDA.mkdir(parents=True, exist_ok=True)

# ===============================
# PALABRAS A ELIMINAR (ESPAÑOL)
# ===============================
stopwords_es.update({
    # Redes sociales / web
    "twitter", "x", "linkedin", "post", "tweet", "like", "comment",
    "share", "rt", "follow", "url", "http", "https", "www",
    "video", "foto", "imagen", "link", "bitly", "lnkd",

    # Tecnológicas irrelevantes para semántica
    "mil", "ma", "usd", "rtx", "ddr", "ram", "vram", "nand",

    # Meses
    "ene", "feb", "mar", "abr", "may", "jun", "jul", "ago",
    "sep", "oct", "nov", "dic",

    # Dominios
    "com", "net", "org",

    # Conectores basura
    "ma", "mas", "menos",

    # Scraping roto
    "mostrar", "cita", "gif", "ver", "click",

    # Nombres propios (ruido)
    "michael", "quesada", "juan", "carlos", "ortiz", "daniel", "patel",
    "eduardo", "antonio", "tomex", "rocamora", "manteca", "bravo", "chopper",
    "citawall", "citabeth", "citayuchen", "citaflunxo", "massccitabeth",
    "elchapuzasinformatico", "vandal", "elespanol",

    # Adverbios genéricos
    "realmente", "totalmente", "simplemente", "directamente", "principalmente",
    "completamente", "absolutamente", "claramente",

    # Palabras muy cortas o basura
    "do", "uma", "na", "pra", "mo", "oh", "yo", "go", "segun",

    # Palabras incompletas frecuentes
    "serum", "plenum", "lasmostrar", "ymostrar", "mascitabeth",
    "warningmostrar", "ano", "ahi"
})

# ===============================
# PATRONES REGEX
# ===============================
PATRONES = {
    "urls": r"https?://\S+|www\.\S+",
    "correos": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "menciones": r"@\w+",
    "hashtags": r"#(\w+)",
    "emojis": (
        "[" 
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+"
    ),
    "risas": r"\b(xd+|xddd+|jaja+[a-z]*|jeje+[a-z]*|lol+|lmao+|rofl+)\b",
    "basura_social": r"\b(lamostrar|amostrar|losmostrar|mostrar|gif|brainrot|cite|cita|masde|pricefabricantes)\b",
    "metricas": r"\b(ma\s*)?mil\b",
    "alargamientos": r"(.)\1{2,}",
    "num_letra": r"(\d)([a-zA-Z])",
    "letra_num": r"([a-zA-Z])(\d)",
    "numeros": r"\b\d+\b",
    "simbolos": r"[^\w\s]",
    "espacios": r"\s+",
    "palabras_rotas": r"\b(serum|plenum|lasmostrar|ymostrar|mascitabeth|warningmostrar|ano|ahi)\b"
}

# ===============================
# 1. LIMPIEZA Y NORMALIZACIÓN
# ===============================
def limpiar_texto(texto: str) -> str:
    if pd.isna(texto):
        return ""

    texto = str(texto)
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = texto.lower()

    for patron in [
        "urls", "correos", "menciones", "hashtags", "emojis",
        "risas", "basura_social", "metricas", "palabras_rotas"
    ]:
        texto = re.sub(PATRONES[patron], " ", texto)

    texto = re.sub(PATRONES["num_letra"], r"\1 \2", texto)
    texto = re.sub(PATRONES["letra_num"], r"\1 \2", texto)
    texto = re.sub(PATRONES["alargamientos"], r"\1\1", texto)
    texto = re.sub(PATRONES["numeros"], " ", texto)
    texto = re.sub(PATRONES["simbolos"], " ", texto)
    texto = re.sub(PATRONES["espacios"], " ", texto)

    return texto.strip()

# ===============================
# TOKENIZACIÓN + STOPWORDS + LEMMATIZACIÓN
# ===============================
def procesar_texto(texto: str) -> str:
    texto = limpiar_texto(texto)

    try:
        tokens = word_tokenize(texto, language="spanish")
    except:
        tokens = texto.split()

    tokens = [
        t for t in tokens
        if (
            t not in stopwords_es
            and len(t) >= 3
            and t.isalpha()
            and len(t) < 25
        )
    ]

    tokens_lem = [lemmatizer.lemmatize(t) for t in tokens]

    # Requiere al menos 4 palabras útiles
    if len(tokens_lem) < 4:
        return ""

    return " ".join(tokens_lem)

# ===============================
# PROCESAR CSV
# ===============================
def procesar_csv(ruta_csv):
    ruta = Path(ruta_csv)
    if not ruta.exists():
        print(f"Archivo no encontrado: {ruta}")
        return

    df = pd.read_csv(ruta, encoding="utf-8")

    if "contenido" not in df.columns:
        print("ERROR: El CSV debe tener una columna llamada 'contenido'")
        return

    print(f"Procesando archivo: {ruta.name}")
    print(f"Filas totales: {len(df)}")

    df["contenido"] = df["contenido"].apply(procesar_texto)
    df = df[df["contenido"].str.strip() != ""]

    salida = RUTA_SALIDA / f"{ruta.stem}_limpio.csv"
    df[["contenido"]].to_csv(salida, index=False, encoding="utf-8-sig")

    print(f"Archivo limpio guardado en: {salida}")
    print(f"Filas finales limpias: {len(df)}")

# ===============================
# MAIN
# ===============================
if __name__ == "__main__":
    archivos = [
        "datos_extraidos/X.csv",
        "datos_extraidos/linkedin.csv",
        "datos_extraidos/facebook.csv",
        "datos_extraidos/reddit.csv",
    ]

    for archivo in archivos:
        procesar_csv(archivo)
