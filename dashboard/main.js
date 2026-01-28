// ========================================
// CONFIGURACIÓN Y CONSTANTES
// ========================================

const CONFIG = {
    // Array con las rutas de los 4 archivos JSON
    jsonPaths: {
        'archivo1': {
            path: '/resultados/facebook_analisis_completo.json',
            nombre: 'Facebook'
        },
        'archivo2': {
            path: '/resultados/Linkedin_analisis_completo.json',
            nombre: 'Linkedin'
        },
        'archivo3': {
            path: '/resultados/reddit_analisis_completo.json',
            nombre: 'Reddit'
        },
        'archivo4': {
            path: '/resultados/X_analisis_completo.json',
            nombre: 'X (Twitter)'
        }
    },
    retryAttempts: 3,
    retryDelay: 1000
};

// Variables globales para almacenar los datos
let todosLosDatos = {}; // Almacena los 4 JSONs cargados
let datosAnalisis = null; // JSON actualmente mostrado
let archivoActual = null; // Clave del archivo actualmente seleccionado

// ========================================
// INICIALIZACIÓN
// ========================================

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🚀 Iniciando dashboard...');
    
    try {
        // Cargar todos los JSONs
        await cargarTodosLosJSONs();
        
        if (Object.keys(todosLosDatos).length === 0) {
            throw new Error('No se pudieron cargar los archivos JSON');
        }
        
        // Seleccionar el primer archivo por defecto
        const primerArchivo = Object.keys(todosLosDatos)[0];
        archivoActual = primerArchivo;
        datosAnalisis = todosLosDatos[primerArchivo];
        
        // Validar estructura del JSON
        validarEstructuraJSON(datosAnalisis);
        
        // Configurar el selector de archivos
        configurarSelectorArchivos();
        
        // Inicializar componentes del dashboard
        inicializarDashboard();
        
        // Ocultar loader y mostrar dashboard
        document.getElementById('loader').style.display = 'none';
        document.getElementById('dashboard').style.display = 'flex';
        
        console.log('✅ Dashboard inicializado correctamente');
        
    } catch (error) {
        console.error('❌ Error al inicializar dashboard:', error);
        mostrarError(error.message);
    }
});

// ========================================
// CARGA DE TODOS LOS JSONs
// ========================================

async function cargarTodosLosJSONs() {
    console.log('📥 Cargando todos los archivos JSON...');
    
    const promesas = Object.entries(CONFIG.jsonPaths).map(async ([key, config]) => {
        try {
            const data = await cargarJSON(config.path, config.nombre);
            return { key, data };
        } catch (error) {
            console.warn(`⚠️ No se pudo cargar ${config.nombre}:`, error.message);
            return { key, data: null };
        }
    });
    
    const resultados = await Promise.all(promesas);
    
    // Guardar solo los que se cargaron exitosamente
    resultados.forEach(({ key, data }) => {
        if (data) {
            todosLosDatos[key] = data;
            console.log(`✅ ${CONFIG.jsonPaths[key].nombre} cargado correctamente`);
        }
    });
    
    console.log(`📊 Total archivos cargados: ${Object.keys(todosLosDatos).length}`);
}

async function cargarJSON(path, nombre, intento = 1) {
    console.log(`📥 Intento ${intento} de cargar ${nombre} desde: ${path}`);
    
    try {
        const response = await fetch(path);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        console.error(`❌ Error en intento ${intento} para ${nombre}:`, error.message);
        
        // Reintentar si no se alcanzó el límite
        if (intento < CONFIG.retryAttempts) {
            console.log(`⏳ Reintentando en ${CONFIG.retryDelay}ms...`);
            await esperar(CONFIG.retryDelay);
            return cargarJSON(path, nombre, intento + 1);
        }
        
        // Si agotó los intentos, lanzar error
        throw new Error(`No se pudo cargar ${nombre} después de ${CONFIG.retryAttempts} intentos.`);
    }
}

function validarEstructuraJSON(data) {
    console.log('🔍 Validando estructura del JSON...');
    
    const camposRequeridos = [
        'metadata',
        'analisis_polaridad',
        'frecuencia_palabras',
        'analisis_ngramas',
        'analisis_tfidf',
        'palabras_carga_emocional',
        'analisis_negaciones',
        'metricas_adicionales',
        'interpretacion_llm'
    ];
    
    const camposFaltantes = camposRequeridos.filter(campo => !data[campo]);
    
    if (camposFaltantes.length > 0) {
        throw new Error(`El JSON no tiene la estructura esperada. Campos faltantes: ${camposFaltantes.join(', ')}`);
    }
    
    console.log('✅ Estructura del JSON validada');
}

function esperar(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function mostrarError(mensaje) {
    document.getElementById('loader').style.display = 'none';
    document.getElementById('error-container').style.display = 'flex';
    document.getElementById('error-message').textContent = mensaje;
}

// ========================================
// CONFIGURACIÓN DEL SELECTOR DE ARCHIVOS
// ========================================

function configurarSelectorArchivos() {
    console.log('⚙️ Configurando selector de archivos...');
    
    const selector = document.getElementById('archivo-selector');
    
    if (!selector) {
        console.warn('⚠️ No se encontró el elemento #archivo-selector');
        return;
    }
    
    // Llenar el selector con las opciones disponibles
    selector.innerHTML = '';
    
    Object.entries(todosLosDatos).forEach(([key, data]) => {
        const option = document.createElement('option');
        option.value = key;
        option.textContent = CONFIG.jsonPaths[key].nombre;
        
        // Marcar como seleccionado si es el archivo actual
        if (key === archivoActual) {
            option.selected = true;
        }
        
        selector.appendChild(option);
    });
    
    // Agregar event listener para detectar cambios
    selector.addEventListener('change', (e) => {
        const nuevoArchivo = e.target.value;
        console.log(`🔄 Cambiando a: ${CONFIG.jsonPaths[nuevoArchivo].nombre}`);
        actualizarDashboard(nuevoArchivo);
    });
    
    console.log('✅ Selector de archivos configurado');
}

// ========================================
// ACTUALIZACIÓN DEL DASHBOARD
// ========================================

function actualizarDashboard(archivoKey) {
    console.log(`🔄 Actualizando dashboard con ${CONFIG.jsonPaths[archivoKey].nombre}...`);
    
    try {
        // Actualizar variables globales
        archivoActual = archivoKey;
        datosAnalisis = todosLosDatos[archivoKey];
        
        // Validar que el archivo existe
        if (!datosAnalisis) {
            throw new Error(`No se encontraron datos para ${CONFIG.jsonPaths[archivoKey].nombre}`);
        }
        
        // Re-llenar todos los componentes del dashboard
        llenarMetadata();
        llenarResumenEjecutivo();
        llenarInterpretacionLLM();
        llenarConclusiones();
        
        // Regenerar todas las visualizaciones
        generarTodasLasVisualizaciones();
        
        console.log('✅ Dashboard actualizado correctamente');
        
    } catch (error) {
        console.error('❌ Error al actualizar dashboard:', error);
        alert(`Error al actualizar el dashboard: ${error.message}`);
    }
}

// ========================================
// INICIALIZACIÓN DEL DASHBOARD
// ========================================

function inicializarDashboard() {
    console.log('⚙️ Inicializando componentes del dashboard...');
    
    // 1. Configurar navegación
    configurarNavegacion();
    
    // 2. Configurar pestañas
    configurarPestanas();
    
    // 3. Llenar metadata en sidebar
    llenarMetadata();
    
    // 4. Llenar resumen ejecutivo
    llenarResumenEjecutivo();
    
    // 5. Llenar interpretación LLM
    llenarInterpretacionLLM();
    
    // 6. Generar todas las visualizaciones
    generarTodasLasVisualizaciones();
    
    // 7. Llenar conclusiones
    llenarConclusiones();
    
    console.log('✅ Componentes inicializados');
}

// ========================================
// NAVEGACIÓN
// ========================================

function configurarNavegacion() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            const sectionId = link.getAttribute('data-section');
            
            // Actualizar links activos
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Mostrar sección correspondiente
            const sections = document.querySelectorAll('.content-section');
            sections.forEach(section => {
                section.classList.remove('active');
                if (section.id === sectionId) {
                    section.classList.add('active');
                    
                    // Scroll suave al inicio de la sección
                    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            });
        });
    });
}

// ========================================
// PESTAÑAS
// ========================================

function configurarPestanas() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Actualizar botones activos
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Mostrar contenido correspondiente
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `tab-${tabName}`) {
                    content.classList.add('active');
                }
            });
        });
    });
}

// ========================================
// METADATA EN SIDEBAR
// ========================================

function llenarMetadata() {
    const metadata = datosAnalisis.metadata;
    
    document.getElementById('tema-analisis').textContent = metadata.tema || 'Sin tema';
    document.getElementById('total-comentarios').textContent = metadata.total_comentarios || 0;
    
    // Formatear fecha
    if (metadata.fecha_analisis) {
        const fecha = new Date(metadata.fecha_analisis);
        document.getElementById('fecha-analisis').textContent = fecha.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
    
    document.getElementById('modelo-llm').textContent = datosAnalisis.interpretacion_llm?.modelo_usado || 'N/A';
}

// ========================================
// RESUMEN EJECUTIVO
// ========================================

function llenarResumenEjecutivo() {
    const polaridad = datosAnalisis.analisis_polaridad;
    const metadata = datosAnalisis.metadata;
    
    // Metrics cards
    document.getElementById('metric-total').textContent = metadata.total_comentarios;
    document.getElementById('metric-polaridad').textContent = polaridad.metricas_globales.polaridad_promedio.toFixed(3);
    document.getElementById('metric-confianza').textContent = 
        `${(polaridad.metricas_globales.confianza_promedio * 100).toFixed(1)}%`;
    
    // Sentimiento predominante
    const distribucion = polaridad.distribucion_sentimientos;
    let predominante = 'Neutral';
    let icono = '😐';
    
    if (distribucion.porcentaje_positivos > distribucion.porcentaje_negativos && 
        distribucion.porcentaje_positivos > distribucion.porcentaje_neutrales) {
        predominante = 'Positivo';
        icono = '😊';
    } else if (distribucion.porcentaje_negativos > distribucion.porcentaje_positivos && 
               distribucion.porcentaje_negativos > distribucion.porcentaje_neutrales) {
        predominante = 'Negativo';
        icono = '😞';
    }
    
    document.getElementById('metric-sentimiento').textContent = predominante;
    document.getElementById('metric-sentimiento-icon').textContent = icono;
}

// ========================================
// INTERPRETACIÓN LLM
// ========================================

function llenarInterpretacionLLM() {
    const interpretacion = datosAnalisis.interpretacion_llm;
    
    // Texto completo
    const textoInterpretacion = interpretacion.interpretacion_completa;
    document.getElementById('interpretacion-texto').innerHTML = formatearInterpretacion(textoInterpretacion);
    
    // Modelo usado
    document.getElementById('llm-model-name').textContent = interpretacion.modelo_usado;
    
    // Extraer highlights (parsing básico)
    extraerHighlights(textoInterpretacion);
}

function formatearInterpretacion(texto) {
    // Convertir títulos con ### en headers
    texto = texto.replace(/### (.*)/g, '<h3>$1</h3>');
    
    // Convertir negrita
    texto = texto.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Convertir listas con viñetas
    texto = texto.replace(/^\* (.*)/gm, '<li>$1</li>');
    texto = texto.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    
    // Convertir saltos de línea
    texto = texto.replace(/\n\n/g, '</p><p>');
    
    return `<p>${texto}</p>`;
}
//
function extraerHighlights(texto) {
    // Parsing simple para extraer secciones clave
    const secciones = texto.split('###');
    
    secciones.forEach(seccion => {
        if (seccion.includes('sentimiento predominante')) {
            const contenido = seccion.split('\n')[1]?.substring(0, 200) + '...';
            document.getElementById('highlight-sentimiento').textContent = contenido || 'Ver interpretación completa';
        }
        else if (seccion.includes('aspectos específicos que generan sentimientos positivos')) {
            const contenido = seccion.split('\n')[1]?.substring(0, 200) + '...';
            document.getElementById('highlight-positivos').textContent = contenido || 'Ver interpretación completa';
        }
        else if (seccion.includes('aspectos específicos que generan sentimientos negativos')) {
            const contenido = seccion.split('\n')[1]?.substring(0, 200) + '...';
            document.getElementById('highlight-negativos').textContent = contenido || 'Ver interpretación completa';
        }
        else if (seccion.includes('Patrones o tendencias')) {
            const contenido = seccion.split('\n')[1]?.substring(0, 200) + '...';
            document.getElementById('highlight-patrones').textContent = contenido || 'Ver interpretación completa';
        }
    });
}

// ========================================
// CONCLUSIONES
// ========================================

function llenarConclusiones() {
    const polaridad = datosAnalisis.analisis_polaridad;
    const interpretacion = datosAnalisis.interpretacion_llm.interpretacion_completa;
    
    // Sentimiento predominante
    const dist = polaridad.distribucion_sentimientos;
    let texto = `El análisis revela que ${dist.porcentaje_neutrales}% de los comentarios son neutrales, 
${dist.porcentaje_negativos}% negativos y ${dist.porcentaje_positivos}% positivos. 
La polaridad promedio de ${polaridad.metricas_globales.polaridad_promedio.toFixed(3)} indica una tendencia 
ligeramente ${polaridad.metricas_globales.polaridad_promedio < 0 ? 'negativa' : 'positiva'}.`;
    
    document.getElementById('conclusion-sentimiento').textContent = texto;
    
    // Hallazgos estadísticos
    const hallazgos = [
        `Total de ${datosAnalisis.metadata.total_comentarios} comentarios analizados`,
        `Confianza promedio del modelo: ${(polaridad.metricas_globales.confianza_promedio * 100).toFixed(1)}%`,
        `${datosAnalisis.palabras_carga_emocional.resumen.total_palabras_positivas} palabras con carga positiva detectadas`,
        `${datosAnalisis.palabras_carga_emocional.resumen.total_palabras_negativas} palabras con carga negativa detectadas`,
        `${datosAnalisis.analisis_negaciones.resumen.porcentaje_con_negacion}% de comentarios contienen negaciones`
    ];
    
    const listaHallazgos = document.getElementById('conclusion-estadisticos');
    listaHallazgos.innerHTML = hallazgos.map(h => `<li>${h}</li>`).join('');
    
    // Extraer insights y recomendaciones del texto del LLM
    const seccionesLLM = interpretacion.split('###');
    
    seccionesLLM.forEach(seccion => {
        if (seccion.includes('Insights interesantes')) {
            const contenido = seccion.substring(seccion.indexOf('\n') + 1).trim().substring(0, 500);
            document.getElementById('conclusion-insights').textContent = contenido || 'Ver interpretación completa del LLM';
        }
        else if (seccion.includes('Recomendaciones')) {
            const contenido = seccion.substring(seccion.indexOf('\n') + 1).trim().substring(0, 500);
            document.getElementById('conclusion-recomendaciones').textContent = contenido || 'Ver interpretación completa del LLM';
        }
    });
}

// ========================================
// DESCARGA DEL JSON
// ========================================

function descargarJSON() {
    const dataStr = JSON.stringify(datosAnalisis, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analisis_${datosAnalisis.metadata.tema.replace(/\s+/g, '_')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    console.log('📥 JSON descargado');
}

// Hacer disponible globalmente
window.descargarJSON = descargarJSON;