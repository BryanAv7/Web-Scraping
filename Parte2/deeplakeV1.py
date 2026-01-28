from mistralai import Mistral

# Tu API Key de Mistral
MISTRAL_API_KEY = ""

# Inicializamos Mistral
with Mistral(api_key=MISTRAL_API_KEY) as mistral:

    # Función simple para clasificar sentimiento
    def clasificar_sentimiento(frase):
        prompt = f"""
Clasifica el sentimiento del siguiente texto como:
POSITIVO, NEGATIVO o NEUTRO.
Devuelve solo una palabra.

Texto: "{frase}"
"""
        res = mistral.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            stream=False
        )
        return res.choices[0].message.content.strip()

    # --- Ejemplo ---
    frase = "La atención fue pésima, no vuelvo nunca más"
    sentimiento = clasificar_sentimiento(frase)

    print("Texto:", frase)
    print("Sentimiento:", sentimiento)
