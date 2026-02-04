/**
 * ESTADÍSTICAS.JS
 * Sistema de visualización de análisis de sentimientos
 * Utiliza Chart.js para crear 10 gráficos académicos interactivos
 */

// ============================================================
// CONFIGURACIÓN GLOBAL
// ============================================================

// Colores académicos consistentes
const COLORES = {
    positivo: 'rgba(76, 175, 80, 0.8)',      // Verde
    negativo: 'rgba(244, 67, 54, 0.8)',      // Rojo  
    neutral: 'rgba(158, 158, 158, 0.8)',     // Gris
    primario: 'rgba(33, 150, 243, 0.8)',     // Azul
    secundario: 'rgba(255, 193, 7, 0.8)',    // Amarillo
    acento: 'rgba(156, 39, 176, 0.8)',       // Púrpura
    
    // Versiones con transparencia
    positivoTransparente: 'rgba(76, 175, 80, 0.2)',
    negativoTransparente: 'rgba(244, 67, 54, 0.2)',
    neutralTransparente: 'rgba(158, 158, 158, 0.2)',
};

// Paleta para emociones (8 colores distintos)
const COLORES_EMOCIONES = [
    'rgba(255, 206, 86, 0.8)',   // Amarillo - Joy
    'rgba(54, 162, 235, 0.8)',   // Azul - Sadness
    'rgba(255, 99, 132, 0.8)',   // Rojo - Anger
    'rgba(153, 102, 255, 0.8)',  // Púrpura - Fear
    'rgba(255, 159, 64, 0.8)',   // Naranja - Surprise
    'rgba(75, 192, 192, 0.8)',   // Verde azulado - Trust
    'rgba(201, 203, 207, 0.8)',  // Gris - Anticipation
    'rgba(255, 99, 71, 0.8)',    // Tomate - Disgust
];

// Configuración por defecto de Chart.js
Chart.defaults.color = '#e0e0e0';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";

// Almacén de instancias de gráficos (para destruirlos al cambiar de red)
const graficosActivos = {};

// ============================================================
// FUNCIONES AUXILIARES
// ============================================================

/**
 * Destruye un gráfico existente si existe
 */
function destruirGrafico(id) {
    if (graficosActivos[id]) {
        graficosActivos[id].destroy();
        delete graficosActivos[id];
    }
}

/**
 * Crea bins para el histograma de polaridad
 */
function crearBinsPolaridad(valores, numBins = 20) {
    const bins = Array(numBins).fill(0);
    const binSize = 2 / numBins; // Rango de -1 a 1
    
    valores.forEach(valor => {
        const binIndex = Math.min(
            Math.floor((valor + 1) / binSize),
            numBins - 1
        );
        bins[binIndex]++;
    });
    
    return bins;
}

/**
 * Genera etiquetas para los bins del histograma
 */
function generarEtiquetasBins(numBins = 20) {
    const etiquetas = [];
    const binSize = 2 / numBins;
    
    for (let i = 0; i < numBins; i++) {
        const inicio = -1 + (i * binSize);
        const fin = inicio + binSize;
        etiquetas.push(`${inicio.toFixed(2)} a ${fin.toFixed(2)}`);
    }
    
    return etiquetas;
}

/**
 * Obtiene color según sentimiento
 */
function obtenerColorSentimiento(sentimiento) {
    const sent = sentimiento.toUpperCase();
    if (sent === 'POSITIVO') return COLORES.positivo;
    if (sent === 'NEGATIVO') return COLORES.negativo;
    return COLORES.neutral;
}

/**
 * Extrae top N elementos de un array de objetos
 */
function extraerTopN(array, n = 10) {
    return array.slice(0, n);
}

// ============================================================
// GRÁFICO 1: DISTRIBUCIÓN DE SENTIMIENTOS (PIE/DOUGHNUT)
// ============================================================

function crearGraficoDistribucion(datos) {
    destruirGrafico('chartDistribucion');
    
    const dist = datos.distribucion_sentimientos || {};
    
    const ctx = document.getElementById('chartDistribucion');
    if (!ctx) return;
    
    graficosActivos['chartDistribucion'] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positivos', 'Negativos', 'Neutrales'],
            datasets: [{
                data: [
                    dist.positivos || 0,
                    dist.negativos || 0,
                    dist.neutrales || 0
                ],
                backgroundColor: [
                    COLORES.positivo,
                    COLORES.negativo,
                    COLORES.neutral
                ],
                borderColor: '#1a1a1a',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: { size: 13 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const porcentaje = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${porcentaje}%)`;
                        }
                    }
                }
            }
        }
    });
}

// ============================================================
// GRÁFICO 2: HISTOGRAMA DE POLARIDAD
// ============================================================

function crearGraficoHistograma(datos) {
    destruirGrafico('chartHistograma');
    
    const polaridades = datos.datos_csv?.polaridad || [];
    
    if (polaridades.length === 0) {
        console.warn('No hay datos de polaridad disponibles');
        return;
    }
    
    const numBins = 20;
    const bins = crearBinsPolaridad(polaridades, numBins);
    const etiquetas = generarEtiquetasBins(numBins);
    
    const ctx = document.getElementById('chartHistograma');
    if (!ctx) return;
    
    graficosActivos['chartHistograma'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: etiquetas,
            datasets: [{
                label: 'Frecuencia',
                data: bins,
                backgroundColor: COLORES.primario,
                borderColor: COLORES.primario,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de comentarios',
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Rango de polaridad',
                        font: { size: 12 }
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45,
                        font: { size: 9 }
                    },
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            return `Rango: ${context[0].label}`;
                        },
                        label: function(context) {
                            return `Comentarios: ${context.parsed.y}`;
                        }
                    }
                }
            }
        }
    });
}

// ============================================================
// GRÁFICO 3: SCATTER PLOT POLARIDAD VS CONFIANZA
// ============================================================

function crearGraficoScatter(datos) {
    destruirGrafico('chartScatter');
    
    const polaridades = datos.datos_csv?.polaridad || [];
    const confianzas = datos.datos_csv?.confianza || [];
    const sentimientos = datos.datos_csv?.sentimiento || [];
    
    if (polaridades.length === 0 || confianzas.length === 0) {
        console.warn('No hay datos suficientes para scatter plot');
        return;
    }
    
    // Separar datos por sentimiento
    const datosPositivos = [];
    const datosNegativos = [];
    const datosNeutrales = [];
    
    for (let i = 0; i < polaridades.length; i++) {
        const punto = { x: polaridades[i], y: confianzas[i] };
        const sent = sentimientos[i]?.toUpperCase();
        
        if (sent === 'POSITIVO') datosPositivos.push(punto);
        else if (sent === 'NEGATIVO') datosNegativos.push(punto);
        else datosNeutrales.push(punto);
    }
    
    const ctx = document.getElementById('chartScatter');
    if (!ctx) return;
    
    graficosActivos['chartScatter'] = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Positivos',
                    data: datosPositivos,
                    backgroundColor: COLORES.positivo,
                    borderColor: COLORES.positivo,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Negativos',
                    data: datosNegativos,
                    backgroundColor: COLORES.negativo,
                    borderColor: COLORES.negativo,
                    pointRadius: 4,
                    pointHoverRadius: 6
                },
                {
                    label: 'Neutrales',
                    data: datosNeutrales,
                    backgroundColor: COLORES.neutral,
                    borderColor: COLORES.neutral,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Polaridad',
                        font: { size: 13 }
                    },
                    min: -1,
                    max: 1,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Confianza',
                        font: { size: 13 }
                    },
                    min: 0,
                    max: 1,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: (${context.parsed.x.toFixed(3)}, ${context.parsed.y.toFixed(3)})`;
                        }
                    }
                }
            }
        }
    });
}

// ============================================================
// GRÁFICO 4: TOP PALABRAS POSITIVAS
// ============================================================

function crearGraficoPalabrasPositivas(datos) {
    destruirGrafico('chartPalabrasPositivas');
    
    const palabras = datos.frecuencia_palabras?.top_positivos || [];
    const top = extraerTopN(palabras, 10);
    
    if (top.length === 0) {
        console.warn('No hay palabras positivas disponibles');
        return;
    }
    
    const ctx = document.getElementById('chartPalabrasPositivas');
    if (!ctx) return;
    
    graficosActivos['chartPalabrasPositivas'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top.map(item => item.palabra),
            datasets: [{
                label: 'Frecuencia',
                data: top.map(item => item.frecuencia),
                backgroundColor: COLORES.positivo,
                borderColor: COLORES.positivo,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frecuencia',
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// ============================================================
// GRÁFICO 5: TOP PALABRAS NEGATIVAS
// ============================================================

function crearGraficoPalabrasNegativas(datos) {
    destruirGrafico('chartPalabrasNegativas');
    
    const palabras = datos.frecuencia_palabras?.top_negativos || [];
    const top = extraerTopN(palabras, 10);
    
    if (top.length === 0) {
        console.warn('No hay palabras negativas disponibles');
        return;
    }
    
    const ctx = document.getElementById('chartPalabrasNegativas');
    if (!ctx) return;
    
    graficosActivos['chartPalabrasNegativas'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top.map(item => item.palabra),
            datasets: [{
                label: 'Frecuencia',
                data: top.map(item => item.frecuencia),
                backgroundColor: COLORES.negativo,
                borderColor: COLORES.negativo,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frecuencia',
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// ============================================================
// GRÁFICO 6: TF-IDF PALABRAS DISTINTIVAS
// ============================================================

function crearGraficoTFIDF(datos) {
    destruirGrafico('chartTFIDF');
    
    const tfidf = datos.analisis_tfidf || {};
    const positivos = extraerTopN(tfidf.palabras_distintivas_positivos || [], 10);
    const negativos = extraerTopN(tfidf.palabras_distintivas_negativos || [], 10);
    const neutrales = extraerTopN(tfidf.palabras_distintivas_neutrales || [], 10);
    
    // Usar las palabras de cualquier conjunto que tenga datos
    let etiquetas = [];
    if (positivos.length > 0) {
        etiquetas = positivos.map(item => item.palabra);
    } else if (negativos.length > 0) {
        etiquetas = negativos.map(item => item.palabra);
    } else if (neutrales.length > 0) {
        etiquetas = neutrales.map(item => item.palabra);
    }
    
    if (etiquetas.length === 0) {
        console.warn('No hay datos TF-IDF disponibles');
        return;
    }
    
    const ctx = document.getElementById('chartTFIDF');
    if (!ctx) return;
    
    const datasets = [];
    
    if (positivos.length > 0) {
        datasets.push({
            label: 'Positivos',
            data: positivos.map(item => item.score_tfidf),
            backgroundColor: COLORES.positivo,
            borderColor: COLORES.positivo,
            borderWidth: 1
        });
    }
    
    if (negativos.length > 0) {
        datasets.push({
            label: 'Negativos',
            data: negativos.map(item => item.score_tfidf),
            backgroundColor: COLORES.negativo,
            borderColor: COLORES.negativo,
            borderWidth: 1
        });
    }
    
    if (neutrales.length > 0) {
        datasets.push({
            label: 'Neutrales',
            data: neutrales.map(item => item.score_tfidf),
            backgroundColor: COLORES.neutral,
            borderColor: COLORES.neutral,
            borderWidth: 1
        });
    }
    
    graficosActivos['chartTFIDF'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: etiquetas,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Score TF-IDF',
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 15
                    }
                }
            }
        }
    });
}

// ============================================================
// GRÁFICO 7: BIGRAMAS FRECUENTES (NEGATIVOS)
// ============================================================

function crearGraficoBigramas(datos) {
    destruirGrafico('chartBigramas');
    
    const bigramas = datos.analisis_ngramas?.bigramas_negativos || [];
    const top = extraerTopN(bigramas, 10);
    
    if (top.length === 0) {
        console.warn('No hay bigramas negativos disponibles');
        return;
    }
    
    const ctx = document.getElementById('chartBigramas');
    if (!ctx) return;
    
    graficosActivos['chartBigramas'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top.map(item => item.bigrama),
            datasets: [{
                label: 'Frecuencia',
                data: top.map(item => item.frecuencia),
                backgroundColor: COLORES.secundario,
                borderColor: COLORES.secundario,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frecuencia',
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// ============================================================
// GRÁFICO 8: TRIGRAMAS FRECUENTES (NEGATIVOS)
// ============================================================

function crearGraficoTrigramas(datos) {
    destruirGrafico('chartTrigramas');
    
    const trigramas = datos.analisis_ngramas?.trigramas_negativos || [];
    const top = extraerTopN(trigramas, 10);
    
    if (top.length === 0) {
        console.warn('No hay trigramas negativos disponibles');
        return;
    }
    
    const ctx = document.getElementById('chartTrigramas');
    if (!ctx) return;
    
    graficosActivos['chartTrigramas'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top.map(item => item.trigrama),
            datasets: [{
                label: 'Frecuencia',
                data: top.map(item => item.frecuencia),
                backgroundColor: COLORES.acento,
                borderColor: COLORES.acento,
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frecuencia',
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                y: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: { size: 10 }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// ============================================================
// GRÁFICO 9: RADAR DE EMOCIONES (NRC)
// ============================================================

function crearGraficoEmociones(datos) {
    destruirGrafico('chartEmociones');
    
    const emociones = datos.distribucion_emociones || {};
    
    const emocionesOrdenadas = [
        'Joy', 'Sadness', 'Anger', 'Fear', 
        'Surprise', 'Trust', 'Anticipation', 'Disgust'
    ];
    
    const valores = emocionesOrdenadas.map(emocion => emociones[emocion] || 0);
    
    if (valores.every(v => v === 0)) {
        console.warn('No hay datos de emociones disponibles');
        return;
    }
    
    const ctx = document.getElementById('chartEmociones');
    if (!ctx) return;
    
    graficosActivos['chartEmociones'] = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: emocionesOrdenadas,
            datasets: [{
                label: 'Intensidad Emocional',
                data: valores,
                backgroundColor: 'rgba(33, 150, 243, 0.2)',
                borderColor: COLORES.primario,
                borderWidth: 2,
                pointBackgroundColor: COLORES.primario,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: COLORES.primario,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    angleLines: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    pointLabels: {
                        font: { size: 12 }
                    },
                    ticks: {
                        backdropColor: 'transparent'
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 15
                    }
                }
            }
        }
    });
}

// ============================================================
// GRÁFICO 10: LONGITUD DE COMENTARIOS POR SENTIMIENTO
// ============================================================

function crearGraficoLongitud(datos) {
    destruirGrafico('chartLongitud');
    
    const longitud = datos.metricas_adicionales?.longitud_comentarios || {};
    
    const promedios = [
        longitud.promedio_positivos || 0,
        longitud.promedio_negativos || 0,
        longitud.promedio_neutrales || 0
    ];
    
    if (promedios.every(v => v === 0)) {
        console.warn('No hay datos de longitud disponibles');
        return;
    }
    
    const ctx = document.getElementById('chartLongitud');
    if (!ctx) return;
    
    graficosActivos['chartLongitud'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Positivos', 'Negativos', 'Neutrales'],
            datasets: [{
                label: 'Promedio de palabras',
                data: promedios,
                backgroundColor: [
                    COLORES.positivo,
                    COLORES.negativo,
                    COLORES.neutral
                ],
                borderColor: [
                    COLORES.positivo,
                    COLORES.negativo,
                    COLORES.neutral
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de palabras',
                        font: { size: 12 }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Promedio: ${context.parsed.y.toFixed(2)} palabras`;
                        }
                    }
                }
            }
        }
    });
}

// ============================================================
// GRÁFICO 11: COMPARATIVA ENTRE REDES
// ============================================================

function crearGraficoComparativa() {
    destruirGrafico('chartComparativa');
    
    const comparativa = estadisticasGlobales?.por_red || {};
    const redes = Object.keys(comparativa);
    
    if (redes.length === 0) {
        console.warn('No hay datos para comparativa');
        return;
    }
    
    const datosPositivos = redes.map(red => comparativa[red].positivos || 0);
    const datosNegativos = redes.map(red => comparativa[red].negativos || 0);
    const datosNeutrales = redes.map(red => comparativa[red].neutrales || 0);
    
    const ctx = document.getElementById('chartComparativa');
    if (!ctx) return;
    
    graficosActivos['chartComparativa'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: redes.map(r => r.charAt(0).toUpperCase() + r.slice(1)),
            datasets: [
                {
                    label: 'Positivos',
                    data: datosPositivos,
                    backgroundColor: COLORES.positivo,
                    borderColor: COLORES.positivo,
                    borderWidth: 1
                },
                {
                    label: 'Negativos',
                    data: datosNegativos,
                    backgroundColor: COLORES.negativo,
                    borderColor: COLORES.negativo,
                    borderWidth: 1
                },
                {
                    label: 'Neutrales',
                    data: datosNeutrales,
                    backgroundColor: COLORES.neutral,
                    borderColor: COLORES.neutral,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    stacked: false,
                    title: {
                        display: true,
                        text: 'Cantidad de comentarios',
                        font: { size: 13 }
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    stacked: false,
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 20,
                        font: { size: 13 }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            }
        }
    });
}

// ============================================================
// FUNCIÓN PRINCIPAL: CREAR TODOS LOS GRÁFICOS
// ============================================================

function crearTodosLosGraficos(nombreRed) {
    console.log(`📊 Creando gráficos para: ${nombreRed}`);
    
    const datos = datosEstadisticas.datos_por_red[nombreRed];
    
    if (!datos) {
        console.error(`No se encontraron datos para la red: ${nombreRed}`);
        return;
    }
    
    // Crear cada gráfico
    try {
        crearGraficoDistribucion(datos);
        crearGraficoHistograma(datos);
        crearGraficoScatter(datos);
        crearGraficoPalabrasPositivas(datos);
        crearGraficoPalabrasNegativas(datos);
        crearGraficoTFIDF(datos);
        crearGraficoBigramas(datos);
        crearGraficoTrigramas(datos);
        crearGraficoEmociones(datos);
        crearGraficoLongitud(datos);
        
        console.log('✅ Gráficos creados exitosamente');
    } catch (error) {
        console.error('❌ Error al crear gráficos:', error);
    }
}

// ============================================================
// FUNCIONES DE CONTROL DE VISUALIZACIÓN
// ============================================================

function ocultarGraficosIndividuales() {
    const secciones = [
        'chartDistribucion', 'chartHistograma', 'chartScatter',
        'chartPalabrasPositivas', 'chartPalabrasNegativas', 'chartTFIDF',
        'chartBigramas', 'chartTrigramas', 'chartEmociones', 'chartLongitud'
    ];
    
    secciones.forEach(id => {
        const elemento = document.getElementById(id);
        if (elemento) {
            elemento.closest('.analysis-section')?.style.setProperty('display', 'none');
        }
    });
}

function mostrarGraficosIndividuales() {
    const secciones = document.querySelectorAll('.analysis-section');
    secciones.forEach(seccion => {
        if (seccion.id !== 'seccionComparativa') {
            seccion.style.removeProperty('display');
        }
    });
}

// ============================================================
// FUNCIÓN DE INICIALIZACIÓN
// ============================================================

function inicializarGraficos(nombreRed) {
    console.log(`🔄 Inicializando visualización para: ${nombreRed}`);
    
    if (nombreRed === 'todas') {
        // Modo comparativa
        ocultarGraficosIndividuales();
        crearGraficoComparativa();
        document.getElementById('seccionComparativa').style.display = 'block';
    } else {
        // Modo individual
        mostrarGraficosIndividuales();
        document.getElementById('seccionComparativa').style.display = 'none';
        crearTodosLosGraficos(nombreRed);
    }
}

// ============================================================
// EVENT LISTENERS
// ============================================================

// Selector de red social
document.getElementById('redSelector')?.addEventListener('change', function(e) {
    const redSeleccionada = e.target.value;
    inicializarGraficos(redSeleccionada);
});

// Inicializar al cargar la página
window.addEventListener('DOMContentLoaded', function() {
    console.log('📈 Sistema de estadísticas cargado');
    console.log('Datos disponibles:', datosEstadisticas);
    
    const primeraRed = datosEstadisticas.redes_disponibles[0];
    
    if (primeraRed) {
        document.getElementById('redSelector').value = primeraRed;
        inicializarGraficos(primeraRed);
    } else {
        console.error('❌ No hay redes sociales disponibles');
    }
});