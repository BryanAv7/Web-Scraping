
import cohere

# Tu API Key de Cohere Trial
API_KEY = ""
co = cohere.Client(API_KEY)

def clasificar_sentimiento(texto):
    # Modelo para clasificación / chat
    prompt = f"""
Clasifica el sentimiento del siguiente texto como:
POSITIVO, NEGATIVO o NEUTRO.
Devuelve solo una palabra.

Texto: "{texto}"
"""
    response = co.chat(
        model="command-a-03-2025",  
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return response.output_text.strip()


# Prueba
frase = "La atención fue pésima, no vuelvo nunca más"
print("Texto:", frase)
print("Sentimiento:", clasificar_sentimiento(frase))
