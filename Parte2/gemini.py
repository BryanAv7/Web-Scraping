from google import genai
import json

# PON TU API KEY AQUÍ DIRECTO
API_KEY = ""

# Crear cliente usando la key directamente
client = genai.Client(api_key=API_KEY)

def clasificar_sentimiento(texto):
    prompt = f"""
Clasifica el sentimiento del texto SOLO en una de estas categorías:

POSITIVO
NEGATIVO
NEUTRO

Responde únicamente en JSON:
{{
  "sentimiento": "POSITIVO | NEGATIVO | NEUTRO"
}}

Texto:
\"\"\"{texto}\"\"\"
"""

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt
    )

    data = json.loads(response.text)
    return data["sentimiento"]


# Prueba rápida
if __name__ == "__main__":
    texto = "La atención fue pésima, no vuelvo nunca más"
    print("Texto:", texto)
    print("Sentimiento:", clasificar_sentimiento(texto))
