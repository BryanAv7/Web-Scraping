// ========================================
// GESTIÓN DE INSTANCIAS DE GRÁFICOS
// ========================================

// Objeto global para almacenar todas las instancias de Chart.js
const chartInstances = {};

/**
 * Destruir todos los gráficos existentes
 */
function destruirTodosLosGraficos() {
    console.log('🧹 Destruyendo gráficos existentes...');
    
    Object.keys(chartInstances).forEach(key => {
        if (chartInstances[key] && typeof chartInstances[key].destroy === 'function') {
            chartInstances[key].destroy();
        }
    });
    
    // Limpiar el objeto
    Object.keys(chartInstances).forEach(key => delete chartInstances[key]);
    
    // Limpiar el wordcloud manualmente (no es Chart.js)
    const wordcloudCanvas = document.getElementById('wordcloud-general');
    if (wordcloudCanvas) {
        const ctx = wordcloudCanvas.getContext('2d');
        ctx.clearRect(0, 0, wordcloudCanvas.width, wordcloudCanvas.height);
    }
    
    console.log('✅ Gráficos destruidos');
}

// ========================================
// GENERACIÓN DE TODAS LAS VISUALIZACIONES
// ========================================

function generarTodasLasVisualizaciones() {
    console.log('📊 Generando visualizaciones...');
    
    try {
        // PRIMERO: Destruir todos los gráficos existentes
        destruirTodosLosGraficos();
        
        // RESUMEN EJECUTIVO
        generarGraficoDistribucion(); // Gráfico 1
        
        // TAB POLARIDAD
        generarGraficoPolaridadSentimiento(); // Gráfico 2
        generarGraficoPolaridadDistribucion(); // Gráfico 3
        generarGraficoPolaridadRangos(); // Gráfico 4
        
        // TAB FRECUENCIAS
        generarWordCloudGeneral(); // Gráfico 5
        generarGraficoTopPalabras(); // Gráfico 6
        generarGraficoPalabrasSentimiento(); // Gráfico 7
        
        // TAB N-GRAMAS
        generarGraficoBigramasGeneral(); // Gráfico 8
        generarGraficoBigramasComparacion(); // Gráfico 9
        generarGraficoTrigramasNegativos(); // Gráfico 10
        
        // TAB TF-IDF
        generarGraficoTFIDFHeatmap(); // Gráfico 11
        generarGraficoTFIDFRadar(); // Gráfico 12
        
        // TAB CARGA EMOCIONAL
        generarGraficoEmociones(); // Gráfico 13
        generarRatioEmocional(); // Gráfico 14
        generarGraficoPalabrasEmocionales(); // Gráfico 15
        
        // TAB NEGACIONES
        llenarDatosNegaciones(); // Gráficos 16-18
        generarGraficoBigramasNegacion();
        
        // TAB MÉTRICAS
        generarGraficoLongitud(); // Gráfico 19
        llenarTablaMetricas();
        
        console.log('✅ Todas las visualizaciones generadas');
        
    } catch (error) {
        console.error('❌ Error generando visualizaciones:', error);
    }
}

// ========================================
// CONFIGURACIÓN COMÚN DE CHART.JS
// ========================================

const COLORES = {
    positivo: '#10b981',
    negativo: '#ef4444',
    neutral: '#6b7280',
    primary: '#3b82f6',
    gradient: ['#3b82f6', '#8b5cf6', '#ec4899']
};

const CONFIG_CHART_DEFAULT = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            display: true,
            position: 'top'
        }
    }
};

// ========================================
// GRÁFICO 1: DISTRIBUCIÓN DE SENTIMIENTOS (DONA)
// ========================================

function generarGraficoDistribucion() {
    const ctx = document.getElementById('chart-distribucion');
    const dist = datosAnalisis.analisis_polaridad.distribucion_sentimientos;
    
    chartInstances['distribucion'] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Neutral', 'Negativo', 'Positivo'],
            datasets: [{
                data: [dist.neutrales, dist.negativos, dist.positivos],
                backgroundColor: [COLORES.neutral, COLORES.negativo, COLORES.positivo],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// ========================================
// GRÁFICO 2: POLARIDAD POR SENTIMIENTO (BARRAS HORIZONTALES)
// ========================================

function generarGraficoPolaridadSentimiento() {
    const ctx = document.getElementById('chart-polaridad-sentimiento');
    const pol = datosAnalisis.analisis_polaridad.polaridad_por_sentimiento;
    
    chartInstances['polaridadSentimiento'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Positivos', 'Negativos', 'Neutrales'],
            datasets: [{
                label: 'Polaridad Promedio',
                data: [pol.positivos.promedio, pol.negativos.promedio, pol.neutrales.promedio],
                backgroundColor: [COLORES.positivo, COLORES.negativo, COLORES.neutral],
                borderWidth: 1
            }]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            indexAxis: 'y',
            scales: {
                x: {
                    min: -1,
                    max: 1,
                    title: {
                        display: true,
                        text: 'Polaridad (-1 = Muy Negativo, +1 = Muy Positivo)'
                    }
                }
            }
        }
    });
}

// ========================================
// GRÁFICO 3: DISTRIBUCIÓN DE POLARIDAD (HISTOGRAMA SIMULADO)
// ========================================

function generarGraficoPolaridadDistribucion() {
    const ctx = document.getElementById('chart-polaridad-distribucion');
    
    // Crear bins para histograma
    const bins = [-1, -0.6, -0.2, 0.2, 0.6, 1];
    const labels = ['Muy Negativo', 'Negativo', 'Neutral', 'Positivo', 'Muy Positivo'];
    
    // Simulación basada en las métricas (en producción real, se necesitarían los datos individuales)
    const pol = datosAnalisis.analisis_polaridad;
    const counts = [
        pol.distribucion_sentimientos.negativos * 0.4,
        pol.distribucion_sentimientos.negativos * 0.6,
        pol.distribucion_sentimientos.neutrales,
        pol.distribucion_sentimientos.positivos * 0.7,
        pol.distribucion_sentimientos.positivos * 0.3
    ];
    
    chartInstances['polaridadDistribucion'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Número de Comentarios',
                data: counts,
                backgroundColor: COLORES.primary,
                borderWidth: 1
            }]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frecuencia'
                    }
                }
            }
        }
    });
}

// ========================================
// GRÁFICO 4: RANGOS DE POLARIDAD (BARRAS CON ERROR)
// ========================================

function generarGraficoPolaridadRangos() {
    const ctx = document.getElementById('chart-polaridad-rangos');
    const pol = datosAnalisis.analisis_polaridad.polaridad_por_sentimiento;
    
    chartInstances['polaridadRangos'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Positivos', 'Negativos', 'Neutrales'],
            datasets: [
                {
                    label: 'Promedio',
                    data: [pol.positivos.promedio, pol.negativos.promedio, pol.neutrales.promedio],
                    backgroundColor: [COLORES.positivo, COLORES.negativo, COLORES.neutral]
                },
                {
                    label: 'Mínimo',
                    data: [pol.positivos.min, pol.negativos.min, pol.neutrales.min],
                    backgroundColor: 'rgba(0,0,0,0.1)',
                    borderColor: 'rgba(0,0,0,0.3)',
                    borderWidth: 1
                },
                {
                    label: 'Máximo',
                    data: [pol.positivos.max, pol.negativos.max, pol.neutrales.max],
                    backgroundColor: 'rgba(0,0,0,0.1)',
                    borderColor: 'rgba(0,0,0,0.3)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            scales: {
                y: {
                    min: -1,
                    max: 1
                }
            }
        }
    });
}

// ========================================
// GRÁFICO 5: WORDCLOUD GENERAL
// ========================================

function generarWordCloudGeneral() {
    const canvas = document.getElementById('wordcloud-general');
    const palabras = datosAnalisis.frecuencia_palabras.top_general;
    
    // Convertir a formato wordcloud2
    const wordList = palabras.map(p => [p.palabra, p.frecuencia]);
    
    // Generar wordcloud
    if (window.WordCloud && wordList.length > 0) {
        WordCloud(canvas, {
            list: wordList,
            gridSize: 8,
            weightFactor: 3,
            fontFamily: 'Inter, sans-serif',
            color: function() {
                // Colores aleatorios del esquema
                const colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#10b981', '#f59e0b'];
                return colors[Math.floor(Math.random() * colors.length)];
            },
            rotateRatio: 0.3,
            backgroundColor: '#f9fafb'
        });
    }
}

// ========================================
// GRÁFICO 6: TOP 10 PALABRAS
// ========================================

function generarGraficoTopPalabras() {
    const ctx = document.getElementById('chart-top-palabras');
    const palabras = datosAnalisis.frecuencia_palabras.top_general;
    
    chartInstances['topPalabras'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: palabras.map(p => p.palabra),
            datasets: [{
                label: 'Frecuencia',
                data: palabras.map(p => p.frecuencia),
                backgroundColor: COLORES.primary
            }]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frecuencia'
                    }
                }
            }
        }
    });
}

// ========================================
// GRÁFICO 7: PALABRAS POR SENTIMIENTO (BARRAS AGRUPADAS)
// ========================================

function generarGraficoPalabrasSentimiento() {
    const ctx = document.getElementById('chart-palabras-sentimiento');
    const freq = datosAnalisis.frecuencia_palabras;
    
    // Tomar las top 5 de cada sentimiento
    const topPos = freq.top_positivos.slice(0, 5);
    const topNeg = freq.top_negativos.slice(0, 5);
    const topNeu = freq.top_neutrales.slice(0, 5);
    
    // Unir todas las palabras únicas
    const todasPalabras = [...new Set([
        ...topPos.map(p => p.palabra),
        ...topNeg.map(p => p.palabra),
        ...topNeu.map(p => p.palabra)
    ])];
    
    // Crear datasets
    const dataPos = todasPalabras.map(palabra => {
        const item = topPos.find(p => p.palabra === palabra);
        return item ? item.frecuencia : 0;
    });
    
    const dataNeg = todasPalabras.map(palabra => {
        const item = topNeg.find(p => p.palabra === palabra);
        return item ? item.frecuencia : 0;
    });
    
    const dataNeu = todasPalabras.map(palabra => {
        const item = topNeu.find(p => p.palabra === palabra);
        return item ? item.frecuencia : 0;
    });
    
    chartInstances['palabrasSentimiento'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: todasPalabras,
            datasets: [
                {
                    label: 'Positivos',
                    data: dataPos,
                    backgroundColor: COLORES.positivo
                },
                {
                    label: 'Negativos',
                    data: dataNeg,
                    backgroundColor: COLORES.negativo
                },
                {
                    label: 'Neutrales',
                    data: dataNeu,
                    backgroundColor: COLORES.neutral
                }
            ]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frecuencia'
                    }
                }
            }
        }
    });
}

// ========================================
// GRÁFICO 8: BIGRAMAS GENERALES
// ========================================

function generarGraficoBigramasGeneral() {
    const ctx = document.getElementById('chart-bigramas-general');
    const bigramas = datosAnalisis.analisis_ngramas.bigramas_general;
    
    chartInstances['bigramasGeneral'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: bigramas.map(b => b.bigrama),
            datasets: [{
                label: 'Frecuencia',
                data: bigramas.map(b => b.frecuencia),
                backgroundColor: COLORES.primary
            }]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

// ========================================
// GRÁFICO 9: BIGRAMAS COMPARACIÓN
// ========================================

function generarGraficoBigramasComparacion() {
    const ctx = document.getElementById('chart-bigramas-comparacion');
    const ngramas = datosAnalisis.analisis_ngramas;
    
    const biPos = ngramas.bigramas_positivos.slice(0, 5);
    const biNeg = ngramas.bigramas_negativos.slice(0, 5);
    
    const labels = [...new Set([
        ...biPos.map(b => b.bigrama),
        ...biNeg.map(b => b.bigrama)
    ])];
    
    const dataPos = labels.map(label => {
        const item = biPos.find(b => b.bigrama === label);
        return item ? item.frecuencia : 0;
    });
    
    const dataNeg = labels.map(label => {
        const item = biNeg.find(b => b.bigrama === label);
        return item ? item.frecuencia : 0;
    });
    
    chartInstances['bigramasComparacion'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Positivos',
                    data: dataPos,
                    backgroundColor: COLORES.positivo
                },
                {
                    label: 'Negativos',
                    data: dataNeg,
                    backgroundColor: COLORES.negativo
                }
            ]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            indexAxis: 'y'
        }
    });
}

// ========================================
// GRÁFICO 10: TRIGRAMAS NEGATIVOS
// ========================================

function generarGraficoTrigramasNegativos() {
    const ctx = document.getElementById('chart-trigramas-negativos');
    const trigramas = datosAnalisis.analisis_ngramas.trigramas_negativos;
    
    chartInstances['trigramasNegativos'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: trigramas.map(t => t.trigrama),
            datasets: [{
                label: 'Frecuencia',
                data: trigramas.map(t => t.frecuencia),
                backgroundColor: COLORES.negativo
            }]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            indexAxis: 'y'
        }
    });
}

// ========================================
// GRÁFICO 11: TF-IDF HEATMAP
// ========================================

function generarGraficoTFIDFHeatmap() {
    const ctx = document.getElementById('chart-tfidf-heatmap');
    const tfidf = datosAnalisis.analisis_tfidf;
    
    // Tomar top 5 de cada sentimiento
    const pos = tfidf.palabras_distintivas_positivos.slice(0, 5);
    const neg = tfidf.palabras_distintivas_negativos.slice(0, 5);
    const neu = tfidf.palabras_distintivas_neutrales.slice(0, 5);
    
    const labels = ['Positivos', 'Negativos', 'Neutrales'];
    
    chartInstances['tfidfHeatmap'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Top 5 Palabras Distintivas'],
            datasets: [
                {
                    label: 'Positivos',
                    data: [pos.reduce((sum, p) => sum + p.score_tfidf, 0) / pos.length],
                    backgroundColor: COLORES.positivo
                },
                {
                    label: 'Negativos',
                    data: [neg.reduce((sum, p) => sum + p.score_tfidf, 0) / neg.length],
                    backgroundColor: COLORES.negativo
                },
                {
                    label: 'Neutrales',
                    data: [neu.reduce((sum, p) => sum + p.score_tfidf, 0) / neu.length],
                    backgroundColor: COLORES.neutral
                }
            ]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Score TF-IDF Promedio'
                    }
                }
            }
        }
    });
}

// ========================================
// GRÁFICO 12: TF-IDF RADAR
// ========================================

function generarGraficoTFIDFRadar() {
    const ctx = document.getElementById('chart-tfidf-radar');
    const tfidf = datosAnalisis.analisis_tfidf;
    
    // Obtener las top 5 palabras de cada sentimiento
    const palabrasPos = tfidf.palabras_distintivas_positivos.slice(0, 5);
    const palabrasNeg = tfidf.palabras_distintivas_negativos.slice(0, 5);
    const palabrasNeu = tfidf.palabras_distintivas_neutrales.slice(0, 5);
    
    // Crear labels (usar palabras únicas)
    const labels = [...new Set([
        ...palabrasPos.map(p => p.palabra),
        ...palabrasNeg.map(p => p.palabra),
        ...palabrasNeu.map(p => p.palabra)
    ])].slice(0, 6);
    
    // Crear datasets
    const dataPos = labels.map(label => {
        const item = palabrasPos.find(p => p.palabra === label);
        return item ? item.score_tfidf : 0;
    });
    
    const dataNeg = labels.map(label => {
        const item = palabrasNeg.find(p => p.palabra === label);
        return item ? item.score_tfidf : 0;
    });
    
    const dataNeu = labels.map(label => {
        const item = palabrasNeu.find(p => p.palabra === label);
        return item ? item.score_tfidf : 0;
    });
    
    chartInstances['tfidfRadar'] = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Positivos',
                    data: dataPos,
                    backgroundColor: 'rgba(16, 185, 129, 0.2)',
                    borderColor: COLORES.positivo,
                    borderWidth: 2
                },
                {
                    label: 'Negativos',
                    data: dataNeg,
                    backgroundColor: 'rgba(239, 68, 68, 0.2)',
                    borderColor: COLORES.negativo,
                    borderWidth: 2
                },
                {
                    label: 'Neutrales',
                    data: dataNeu,
                    backgroundColor: 'rgba(107, 114, 128, 0.2)',
                    borderColor: COLORES.neutral,
                    borderWidth: 2
                }
            ]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            scales: {
                r: {
                    beginAtZero: true
                }
            }
        }
    });
}

// ========================================
// GRÁFICO 13: EMOCIONES
// ========================================

function generarGraficoEmociones() {
    const ctx = document.getElementById('chart-emociones');
    const emociones = datosAnalisis.palabras_carga_emocional.distribucion_emociones;
    
    chartInstances['emociones'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(emociones),
            datasets: [{
                label: 'Ocurrencias',
                data: Object.values(emociones),
                backgroundColor: [
                    '#10b981', // Joy
                    '#6b7280', // Sadness
                    '#ef4444', // Anger
                    '#f59e0b', // Fear
                    '#8b5cf6', // Surprise
                    '#3b82f6', // Trust
                    '#ec4899', // Anticipation
                    '#14b8a6'  // Disgust
                ]
            }]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// ========================================
// GRÁFICO 14: RATIO EMOCIONAL
// ========================================

function generarRatioEmocional() {
    const resumen = datosAnalisis.palabras_carga_emocional.resumen;
    
    const total = resumen.total_palabras_positivas + resumen.total_palabras_negativas;
    const porcentajePos = total > 0 ? (resumen.total_palabras_positivas / total) * 100 : 0;
    const porcentajeNeg = total > 0 ? (resumen.total_palabras_negativas / total) * 100 : 0;
    
    document.getElementById('ratio-positivas').style.width = `${porcentajePos}%`;
    document.getElementById('ratio-negativas').style.width = `${porcentajeNeg}%`;
    
    document.getElementById('count-positivas').textContent = resumen.total_palabras_positivas;
    document.getElementById('count-negativas').textContent = resumen.total_palabras_negativas;
    document.getElementById('ratio-value').textContent = resumen.ratio_negativo_positivo.toFixed(2);
}

// ========================================
// GRÁFICO 15: PALABRAS EMOCIONALES
// ========================================

function generarGraficoPalabrasEmocionales() {
    const ctx = document.getElementById('chart-palabras-emocionales');
    const carga = datosAnalisis.palabras_carga_emocional;
    
    const positivas = carga.top_palabras_positivas.slice(0, 5);
    const negativas = carga.top_palabras_negativas.slice(0, 5);
    
    const labels = [
        ...positivas.map(p => p.palabra + ' (+)'),
        ...negativas.map(p => p.palabra + ' (-)')
    ];
    
    const data = [
        ...positivas.map(p => p.frecuencia),
        ...negativas.map(p => -p.frecuencia) // Negativo para mostrar en dirección opuesta
    ];
    
    const colors = [
        ...Array(positivas.length).fill(COLORES.positivo),
        ...Array(negativas.length).fill(COLORES.negativo)
    ];
    
    chartInstances['palabrasEmocionales'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Frecuencia',
                data: data,
                backgroundColor: colors
            }]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            indexAxis: 'y',
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Frecuencia (positivas a la derecha, negativas a la izquierda)'
                    }
                }
            }
        }
    });
}

// ========================================
// GRÁFICOS 16-18: NEGACIONES
// ========================================

function llenarDatosNegaciones() {
    const neg = datosAnalisis.analisis_negaciones.resumen;
    
    document.getElementById('negaciones-total').textContent = neg.total_negaciones;
    document.getElementById('negaciones-comentarios').textContent = neg.comentarios_con_negacion;
    document.getElementById('negaciones-porcentaje').textContent = `${neg.porcentaje_con_negacion}%`;
    
    // Lista de palabras más negadas
    const palabrasNegadas = datosAnalisis.analisis_negaciones.palabras_mas_negadas;
    const listaHTML = palabrasNegadas.map(p => `
        <div class="palabra-negada-item">
            <span class="palabra">${p.palabra}</span>
            <span class="count">${p.veces_negada}x</span>
        </div>
    `).join('');
    
    document.getElementById('palabras-negadas-list').innerHTML = listaHTML;
}

function generarGraficoBigramasNegacion() {
    const ctx = document.getElementById('chart-bigramas-negacion');
    const bigramas = datosAnalisis.analisis_negaciones.bigramas_con_negacion;
    
    if (bigramas.length === 0) {
        ctx.parentElement.innerHTML = '<p style="text-align:center; color:#6b7280;">No hay suficientes bigramas con negación para visualizar</p>';
        return;
    }
    
    chartInstances['bigramasNegacion'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: bigramas.map(b => b.bigrama),
            datasets: [{
                label: 'Frecuencia',
                data: bigramas.map(b => b.frecuencia),
                backgroundColor: COLORES.negativo
            }]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            indexAxis: 'y'
        }
    });
}

// ========================================
// GRÁFICO 19: LONGITUD DE COMENTARIOS
// ========================================

function generarGraficoLongitud() {
    const ctx = document.getElementById('chart-longitud');
    const longitud = datosAnalisis.metricas_adicionales.longitud_comentarios;
    
    chartInstances['longitud'] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Positivos', 'Negativos', 'Neutrales', 'General'],
            datasets: [{
                label: 'Longitud Promedio (palabras)',
                data: [
                    longitud.promedio_positivos || 0,
                    longitud.promedio_negativos || 0,
                    longitud.promedio_neutrales || 0,
                    longitud.promedio_general
                ],
                backgroundColor: [
                    COLORES.positivo,
                    COLORES.negativo,
                    COLORES.neutral,
                    COLORES.primary
                ]
            }]
        },
        options: {
            ...CONFIG_CHART_DEFAULT,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de Palabras'
                    }
                }
            }
        }
    });
}

// ========================================
// TABLA DE MÉTRICAS
// ========================================

function llenarTablaMetricas() {
    const polaridad = datosAnalisis.analisis_polaridad;
    const metricas = datosAnalisis.metricas_adicionales;
    const dist = polaridad.distribucion_sentimientos;
    const pol = polaridad.polaridad_por_sentimiento;
    const long = metricas.longitud_comentarios;
    
    const filas = [
        {
            sentimiento: 'Positivo',
            clase: 'sentiment-positive',
            cantidad: dist.positivos,
            porcentaje: dist.porcentaje_positivos,
            polaridad: pol.positivos.promedio,
            longitud: long.promedio_positivos || 0
        },
        {
            sentimiento: 'Negativo',
            clase: 'sentiment-negative',
            cantidad: dist.negativos,
            porcentaje: dist.porcentaje_negativos,
            polaridad: pol.negativos.promedio,
            longitud: long.promedio_negativos || 0
        },
        {
            sentimiento: 'Neutral',
            clase: 'sentiment-neutral',
            cantidad: dist.neutrales,
            porcentaje: dist.porcentaje_neutrales,
            polaridad: pol.neutrales.promedio,
            longitud: long.promedio_neutrales || 0
        }
    ];
    
    const tbody = document.getElementById('metrics-table-body');
    tbody.innerHTML = filas.map(fila => `
        <tr>
            <td class="${fila.clase}">${fila.sentimiento}</td>
            <td>${fila.cantidad}</td>
            <td>${fila.porcentaje.toFixed(1)}%</td>
            <td>${fila.polaridad.toFixed(3)}</td>
            <td>${fila.longitud.toFixed(1)}</td>
        </tr>
    `).join('');
}