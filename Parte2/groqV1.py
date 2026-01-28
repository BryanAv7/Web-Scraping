from groq import Groq

API_KEY = ""

client = Groq(api_key=API_KEY)

def clasificar_sentimiento(texto):
    prompt = f"""
Clasifica el sentimiento del siguiente texto como:
POSITIVO, NEGATIVO o NEUTRO.
Devuelve solo una palabra.

Texto: "{texto}"
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()


# Prueba
frase = "La atención fue pésima, no vuelvo nunca más"
print("Texto:", frase)
print("Sentimiento:", clasificar_sentimiento(frase))
