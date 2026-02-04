## SentimentScope

SentimentScope es una aplicación web que permite al usuario realizar búsquedas de información en múltiples redes sociales de manera concurrente, procesando y clasificando los comentarios obtenidos según su sentimiento. Esta aplicación ofrece un análisis consolidado del sentimiento global, así como visualizaciones específicas para cada red social.

La solución se apoya en una arquitectura que integra un servidor web en Flask con una interfaz basada en Jinja, HTML y CSS para definir consultas y visualizar resultados. En el backend, se realiza scraping concurrente de diversas redes sociales, se almacenan los datos en CSV y se limpian con NLTK. Luego, los comentarios procesados se envían a un modelo de lenguaje (LLM) mediante prompts para su clasificación por sentimiento.

Los resultados se almacenan en formatos CSV/JSON y se visualizan en un dashboard interactivo desarrollado con Jinja, HTML y CSS. La aplicación entrega un análisis global y por plataforma, junto con un storytelling que interpreta los patrones de sentimiento detectados.


## Arquitectura

Arquitectura definida:

<img width="928" height="888" alt="ArquitecturaAPP" src="https://github.com/user-attachments/assets/8168a3d2-64e4-4c59-ae15-0b2924858f27" />

## Estructura

```
SISTEMA
│
├── Capa de Interfaz y Control
│   │
│   ├── Servidor de Aplicación
│   │   ├── Interfaz de usuario (input de TEMA)
│   │   ├── Control de ejecución de FASES
│   │   ├── Disparo de Procesos
│   │   └── Acceso a resultados
│   │
│   └── Dashboard
│       ├── Resultado global consolidado
│       ├── Resultados por elemento
│       └── Historial de comentarios
│           ├── comentario
│           └── valor emocional
│
├── FASE 1 — Preparación de Datos
│   │
│   ├── Módulos de extracción
│   ├── Generación de datasets base
│   └── FASE 2 - Procesos de limpieza
│       └── Datasets limpios
│
├── FASE 3 — Procesamiento Analítico
│   │
│   ├── Módulos de procesamiento por elemento
│   ├── Generación de texto procesado
│   ├── Construcción de prompt
│   ├── Interpretación por modelo
│   └── Resultados estructurados
│
└── Variable Transversal
    │
    └── TEMA
        ├── define ejecución
        ├── atraviesa ambos pipelines
        └── condiciona la visualización
```
