"""
==========================================
EXTRACTOR DE POSTS Y COMENTARIOS DE REDDIT
==========================================
"""

from playwright.async_api import async_playwright
import asyncio
import pandas as pd
from datetime import datetime
import random
import os
import math

# =====================================================
# CONFIGURACIÓN GLOBAL - POSTS
# =====================================================

TERMINOS_BUSQUEDA = [
    "nicolas maduro capturado",
]

# Configuración de posts
MAX_POSTS = 10
POSTS_ESTIMADOS_INICIAL = 8
POSTS_ESTIMADOS_POR_SCROLL = 7
MAX_SCROLLS = 5

# =====================================================
# CONFIGURACIÓN GLOBAL - COMENTARIOS
# =====================================================

# Control de extracción
EXTRAER_COMENTARIOS = True  # Activar/desactivar extracción de comentarios
MAX_COMENTARIOS_POR_POST = 50  # Límite de comentarios por post

# Profundidad de búsqueda
BUSQUEDA_PROFUNDA = False  # True = click en "Load more", False = solo scroll
MAX_EXPANDIR_COLAPSADOS = 2  # Cuántos [+] expandir (0 = ninguno)

# Scroll inteligente de comentarios
MAX_SCROLLS_COMENTARIOS = 5  # Máximo de scrolls por post
MIN_COMENTARIOS_THRESHOLD = 5  # Si hay menos, salir rápido

# Tiempos para comentarios (PARAMETRIZABLES)
PAUSA_SCROLL_COMENTARIOS = 1.5  # Pausa entre scrolls en comentarios
PAUSA_PRIMERA_CARGA_COMENTARIOS = 3.0  # Espera inicial de carga de comentarios
PAUSA_ENTRE_POSTS_COMENTARIOS = (2, 4)  # Pausa entre posts (min, max) en segundos
PAUSA_EXPANSION_COLAPSADOS = 1.5  # Pausa después de expandir [+]
PAUSA_LOAD_MORE = 2.0  # Pausa después de click en "Load more"
PAUSA_ENTRE_SCROLLS_COMENTARIOS = 1.0  # Pausa entre scrolls consecutivos

# Detección de duplicados
DEDUPLICAR_COMENTARIOS = True  # Evitar comentarios repetidos

# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

# Perfil persistente
PROFILE_DIR = './reddit_profile'

# Viewport optimizado
VIEWPORT = {
    'width': 1280,
    'height': 720
}

# MODO PARAMETRIZABLE
MODO_RAPIDO = False  # True = 18-25 seg, False = 30-45 seg

# Configuraciones por modo
CONFIG_RAPIDO = {
    'tiempo_espera': (1.5, 2.5),
    'scroll_pausa': 1.0,
    'probabilidad_mouse': 0.2,
    'pausa_entre_terminos': (1, 2),
    'wait_until': 'domcontentloaded',
    'mouse_steps': (3, 8)
}

CONFIG_BALANCEADO = {
    'tiempo_espera': (3, 4),
    'scroll_pausa': 1.5,
    'probabilidad_mouse': 0.4,
    'pausa_entre_terminos': (3, 6),
    'wait_until': 'networkidle',
    'mouse_steps': (5, 15)
}

# Seleccionar configuración según modo
CONFIG = CONFIG_RAPIDO if MODO_RAPIDO else CONFIG_BALANCEADO

FECHA_EXTRACCION = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# =====================================================
# FUNCIONES DE GESTIÓN DE SESIÓN
# =====================================================

async def verificar_y_preparar_sesion(page):
    """Verifica si ya hay sesión activa de Reddit"""
    
    print("\n🔍 Verificando sesión de Reddit...")
    
    try:
        await page.goto('https://www.reddit.com', wait_until=CONFIG['wait_until'], timeout=30000)
    except:
        await page.goto('https://www.reddit.com', wait_until='domcontentloaded')
    
    await asyncio.sleep(2)
    
    # Intentar detectar sesión
    try:
        user_indicators = [
            'button[id*="user-drawer-button"]',
            '[data-testid="user-drawer-button"]',
            'a[href*="/user/"]',
        ]
        
        for selector in user_indicators:
            user_button = await page.query_selector(selector)
            if user_button:
                print("✓ Sesión activa detectada en Reddit")
                try:
                    username = await page.query_selector(f'{selector} span')
                    if username:
                        user_text = await username.text_content()
                        print(f"  Usuario: {user_text}")
                except:
                    pass
                return True
    except:
        pass
    
    # No hay sesión - pedir login
    print("\n" + "="*60)
    print("⚠️  NO HAY SESIÓN ACTIVA EN REDDIT")
    print("="*60)
    print("\n📋 INSTRUCCIONES:\n")
    print("1. En el navegador Chrome:")
    print("   → Haz click en 'Log In'")
    print("   → Inicia sesión con tu cuenta")
    print("   → Resuelve captcha si aparece\n")
    print("2. Vuelve a la consola y presiona ENTER\n")
    print("="*60)
    print("NOTA: Solo necesitas hacer esto UNA VEZ.")
    print("="*60 + "\n")
    
    # input("Presiona ENTER cuando hayas iniciado sesión... ")
    
    print("\n🔄 Verificando sesión...")
    try:
        await page.reload(wait_until=CONFIG['wait_until'], timeout=15000)
    except:
        await page.reload(wait_until='domcontentloaded')
    
    await asyncio.sleep(2)
    
    for selector in user_indicators:
        user_button = await page.query_selector(selector)
        if user_button:
            print("✓ Sesión confirmada. Continuando...\n")
            return True
    
    print("⚠️  No se detectó sesión. Continuando de todas formas...\n")
    return False


async def detectar_navegador_disponible(p):
    """Intenta usar Chrome/Edge real, con fallback a Chromium"""
    
    navegadores = [
        ('chrome', 'Google Chrome'),
        ('msedge', 'Microsoft Edge'),
        (None, 'Chromium (Playwright)')
    ]
    
    for channel, nombre in navegadores:
        try:
            print(f"🔍 Intentando usar: {nombre}...")
            
            if channel:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=PROFILE_DIR,
                    headless=False,
                    channel=channel,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                    ],
                    viewport=VIEWPORT,
                    locale='es-EC',
                    timezone_id='America/Guayaquil',
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                )
            else:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=PROFILE_DIR,
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--no-sandbox',
                    ],
                    viewport=VIEWPORT,
                    locale='es-EC',
                    timezone_id='America/Guayaquil',
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                )
            
            print(f"✓ Usando: {nombre}\n")
            return context, nombre
            
        except:
            print(f"  ✗ No disponible")
            continue
    
    raise Exception("❌ No se pudo iniciar ningún navegador")


# =====================================================
# FUNCIONES DE SCRAPING - GENERALES
# =====================================================

async def simular_interaccion_humana(page, tipo='scroll', config=CONFIG):
    """Simula comportamiento humano"""
    
    try:
        if tipo == 'scroll':
            scroll_amount = random.randint(300, 800)
            await page.evaluate(f"window.scrollBy(0, {scroll_amount});")
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
        elif tipo == 'mouse_move':
            # Mouse aleatorio según probabilidad
            if random.random() < config['probabilidad_mouse']:
                await page.mouse.move(
                    random.randint(100, VIEWPORT['width'] - 100),
                    random.randint(100, VIEWPORT['height'] - 100),
                    steps=random.randint(*config['mouse_steps'])
                )
                return True
            return False
            
        elif tipo == 'pause':
            await asyncio.sleep(random.uniform(1.5, 3.5))
            
    except Exception as e:
        print(f"⚠ Error en simulación: {e}")
        return False


async def scroll_pagina(page, pausa, config=CONFIG):
    """Hace scroll con pausa configurable"""
    
    try:
        altura_antes = await page.evaluate("document.body.scrollHeight")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await asyncio.sleep(pausa)
        altura_despues = await page.evaluate("document.body.scrollHeight")
        
        cambio = altura_despues > altura_antes
        if cambio:
            print(f"  📜 Scroll: {altura_antes:,} → {altura_despues:,} px")
        
        return cambio
    except Exception as e:
        print(f"✗ Error en scroll: {e}")
        return False


# =====================================================
# FUNCIONES DE SCRAPING - POSTS
# =====================================================

async def contar_posts_en_dom(page):
    """Cuenta posts actualmente en el DOM"""
    
    try:
        count = await page.evaluate("""
            () => {
                const trackers = document.querySelectorAll(
                    'search-telemetry-tracker[data-testid="search-sdui-post"]'
                );
                if (trackers.length > 0) return trackers.length;
                
                // Fallback
                return document.querySelectorAll(
                    'div[data-testid="search-post-unit"]'
                ).length;
            }
        """)
        return count
    except:
        return 0


async def extraer_posts_reddit(page, termino, max_posts=10, config=CONFIG):
    """Extrae posts con scroll inteligente y selectores robustos"""
    
    print(f"\n{'='*60}")
    print(f"REDDIT | Buscando: {termino}")
    print(f"{'='*60}")
    
    url_busqueda = f"https://www.reddit.com/search/?q={termino.replace(' ', '%20')}&sort=new"
    
    print(f"Navegando a: {url_busqueda}")
    
    try:
        await page.goto(url_busqueda, wait_until=config['wait_until'], timeout=30000)
    except:
        await page.goto(url_busqueda, wait_until='domcontentloaded')
    
    # Esperar selector de posts
    print("⏳ Esperando carga de posts...")
    try:
        await page.wait_for_selector(
            'search-telemetry-tracker[data-testid="search-sdui-post"], div[data-testid="search-post-unit"]',
            timeout=10000
        )
    except:
        print("⚠ Timeout esperando posts, continuando...")
    
    # Pausa humana
    pausa_inicial = random.uniform(*config['tiempo_espera'])
    await asyncio.sleep(pausa_inicial)
    
    # Movimiento de mouse inicial
    moved = await simular_interaccion_humana(page, 'mouse_move', config)
    if moved:
        print("🖱️  Movimiento de mouse")
    
    # Contar posts iniciales
    posts_en_dom = await contar_posts_en_dom(page)
    print(f"📊 Posts en DOM: {posts_en_dom}")
    
    # Script de extracción optimizado
    script = """
    (function () {
        const posts = [];
        const seen = new Set();
        
        // SELECTOR PRINCIPAL: tracker (más robusto)
        let trackers = document.querySelectorAll(
            'search-telemetry-tracker[data-testid="search-sdui-post"]'
        );
        
        // FALLBACK: div interno
        if (trackers.length === 0) {
            trackers = document.querySelectorAll('div[data-testid="search-post-unit"]');
        }
        
        trackers.forEach(tracker => {
            try {
                // VALIDACIÓN 1: Obtener post ID
                const postId = tracker.getAttribute('data-thingid');
                
                if (!postId) return;
                if (!postId.startsWith('t3_')) return;
                if (seen.has(postId)) return;
                seen.add(postId);
                
                // VALIDACIÓN 2: No es separador
                if (tracker.tagName === 'HR' || 
                    tracker.classList.contains('list-divider-line')) {
                    return;
                }
                
                // Obtener container
                let container = tracker.querySelector('div[data-testid="search-post-unit"]');
                if (!container && tracker.getAttribute('data-testid') === 'search-post-unit') {
                    container = tracker;
                }
                if (!container) return;
                
                // TÍTULO
                const titleEl = container.querySelector('a[data-testid="post-title-text"]');
                if (!titleEl) return;
                
                const titulo = titleEl.textContent.trim();
                if (!titulo || titulo.length < 10) return;
                if (titulo.includes('[deleted]') || titulo.includes('[removed]')) return;
                
                const url = titleEl.href || '';
                
                // SUBREDDIT
                let subreddit = 'Desconocido';
                const subEl = container.querySelector('a[href*="/r/"]');
                if (subEl) subreddit = subEl.textContent.trim();
                
                // TIMESTAMP
                let timestamp = '';
                const timeEl = container.querySelector('faceplate-timeago');
                if (timeEl) {
                    timestamp = timeEl.getAttribute('ts') || timeEl.textContent.trim();
                }
                
                // VOTOS Y COMENTARIOS con conversión de números
                let votos = 0;
                let comentarios = 0;
                
                const statsEl = container.querySelector('[data-testid="search-counter-row"]');
                if (statsEl) {
                    const text = statsEl.textContent;
                    
                    const parseNumber = (str) => {
                        if (!str) return 0;
                        str = str.toLowerCase().replace(',', '.');
                        if (str.includes('mil')) {
                            return Math.round(parseFloat(str) * 1000);
                        } else if (str.includes('k')) {
                            return Math.round(parseFloat(str) * 1000);
                        } else {
                            return parseInt(str.replace(/\./g, '').replace(/\s/g, ''));
                        }
                    };
                    
                    const votosMatch = text.match(/([\d,\.]+\s*(?:mil|k)?)\s*votos?/i);
                    const comMatch = text.match(/([\d,\.]+\s*(?:mil|k)?)\s*comentarios?/i);
                    
                    if (votosMatch) votos = parseNumber(votosMatch[1]);
                    if (comMatch) comentarios = parseNumber(comMatch[1]);
                }
                
                // THUMBNAIL
                let thumbnail = '';
                const imgEl = container.querySelector('faceplate-img[data-testid="search_post_thumbnail"]');
                if (imgEl) {
                    thumbnail = imgEl.getAttribute('src') || imgEl.getAttribute('data-src') || '';
                }
                
                posts.push({
                    postId: postId,
                    subreddit: subreddit,
                    titulo: titulo.substring(0, 500),
                    url: url,
                    timestamp: timestamp,
                    votos: votos,
                    comentarios: comentarios,
                    thumbnail: thumbnail
                });
                
            } catch (e) {
                console.error('Error procesando post:', e);
            }
        });
        
        return posts;
    })();
    """
    
    # Extracción inicial
    print("\n→ Extracción inicial")
    posts_actuales = await page.evaluate(script)
    
    posts_extraidos = []
    posts_ids_vistos = set()
    
    # Agregar posts iniciales
    for post in posts_actuales:
        if post['postId'] not in posts_ids_vistos:
            posts_ids_vistos.add(post['postId'])
            
            post_data = {
                "id_post": post["postId"],
                "tipo": "post",
                "autor": post["subreddit"],  # Subreddit como autor del post
                "contenido": post["titulo"],
                "votos": post["votos"],
                "comentarios": post["comentarios"],
                "fecha": post["timestamp"],
                "url": post["url"],
                "thumbnail": post["thumbnail"],
                "tema_busqueda": termino,
                "fecha_extraccion": FECHA_EXTRACCION
            }
            
            posts_extraidos.append(post_data)
            
            print(
                f"✓ Post {len(posts_extraidos)}/{max_posts} "
                f"| {post['postId'][:12]}... "
                f"| {post['subreddit']:20} "
                f"| {post['votos']:,} votos | {post['comentarios']} comentarios"
            )
            
            if len(posts_extraidos) >= max_posts:
                break
    
    # SCROLL INTELIGENTE
    if len(posts_extraidos) < max_posts:
        posts_faltantes = max_posts - len(posts_extraidos)
        scrolls_estimados = math.ceil(posts_faltantes / POSTS_ESTIMADOS_POR_SCROLL)
        
        print(f"\n📊 Faltan {posts_faltantes} posts, iniciando scroll inteligente...")
        print(f"   Scrolls estimados: ~{scrolls_estimados}")
        
        intentos_scroll = 0
        sin_nuevos = 0
        
        while len(posts_extraidos) < max_posts and intentos_scroll < MAX_SCROLLS:
            
            print(f"\n[Scroll {intentos_scroll + 1}/{MAX_SCROLLS}]")
            
            # Mouse aleatorio
            moved = await simular_interaccion_humana(page, 'mouse_move', config)
            if moved:
                print("  🖱️  Movimiento de mouse")
            
            # Scroll
            hubo_cambio = await scroll_pagina(page, config['scroll_pausa'], config)
            intentos_scroll += 1
            
            if not hubo_cambio:
                sin_nuevos += 1
                if sin_nuevos >= 3:
                    print("  ⚠ No hay más posts disponibles")
                    break
            else:
                sin_nuevos = 0
            
            await asyncio.sleep(random.uniform(1, 2))
            
            # Extraer nuevos posts
            posts_actuales = await page.evaluate(script)
            
            nuevos_agregados = 0
            for post in posts_actuales:
                if post['postId'] not in posts_ids_vistos and len(posts_extraidos) < max_posts:
                    posts_ids_vistos.add(post['postId'])
                    
                    post_data = {
                        "id_post": post["postId"],
                        "tipo": "post",
                        "autor": post["subreddit"],
                        "contenido": post["titulo"],
                        "votos": post["votos"],
                        "comentarios": post["comentarios"],
                        "fecha": post["timestamp"],
                        "url": post["url"],
                        "thumbnail": post["thumbnail"],
                        "tema_busqueda": termino,
                        "fecha_extraccion": FECHA_EXTRACCION
                    }
                    
                    posts_extraidos.append(post_data)
                    nuevos_agregados += 1
                    
                    print(
                        f"  ✓ Post {len(posts_extraidos)}/{max_posts} "
                        f"| {post['postId'][:12]}... "
                        f"| {post['subreddit']:20} "
                        f"| {post['votos']:,} votos"
                    )
            
            if nuevos_agregados == 0:
                sin_nuevos += 1
            else:
                sin_nuevos = 0
            
            if len(posts_extraidos) >= max_posts:
                print(f"\n  ✓ Objetivo alcanzado ({len(posts_extraidos)}/{max_posts})")
                break
    
    print(f"\n{'='*60}")
    print(f"REDDIT | Total extraído: {len(posts_extraidos)} posts")
    print(f"{'='*60}")
    
    return posts_extraidos


# =====================================================
# FUNCIONES DE SCRAPING - COMENTARIOS
# =====================================================

async def contar_comentarios_en_dom(page):
    """Cuenta comentarios actualmente en el DOM"""
    
    try:
        count = await page.evaluate("""
            () => {
                const comments = document.querySelectorAll('shreddit-comment');
                return comments.length;
            }
        """)
        return count
    except:
        return 0


async def detectar_boton_load_more(page):
    """Detecta si existe el botón 'Load more comments'"""
    
    try:
        boton = await page.query_selector('button:has-text("Load more comments"), button:has-text("Ver más comentarios")')
        return boton is not None
    except:
        return False


async def expandir_comentarios_colapsados(page, max_expandir=2):
    """Expande comentarios colapsados [+]"""
    
    if max_expandir <= 0:
        return 0
    
    try:
        print(f"  🔓 Expandiendo hasta {max_expandir} comentarios colapsados...")
        
        expandidos = await page.evaluate(f"""
            (maxExpandir) => {{
                const buttons = document.querySelectorAll('button[aria-label*="Expand"], button[aria-label*="Expandir"]');
                let count = 0;
                
                for (let i = 0; i < Math.min(buttons.length, maxExpandir); i++) {{
                    try {{
                        buttons[i].click();
                        count++;
                    }} catch (e) {{
                        console.error('Error expandiendo:', e);
                    }}
                }}
                
                return count;
            }}
        """, max_expandir)
        
        if expandidos > 0:
            print(f"    ✓ {expandidos} comentarios expandidos")
            await asyncio.sleep(PAUSA_EXPANSION_COLAPSADOS)
        
        return expandidos
    except Exception as e:
        print(f"  ⚠ Error expandiendo colapsados: {e}")
        return 0


async def extraer_comentarios_post(context, post_url, post_id, max_comentarios=50):
    """
    Extrae comentarios de un post usando nueva pestaña
    
    Args:
        context: Contexto del navegador
        post_url: URL del post
        post_id: ID del post
        max_comentarios: Máximo de comentarios a extraer
    
    Returns:
        Lista de diccionarios con comentarios extraídos
    """
    
    print(f"\n  💬 Extrayendo comentarios del post {post_id[:12]}...")
    
    # Abrir nueva pestaña
    page_comentarios = await context.new_page()
    
    try:
        # Navegar al post
        print(f"    → Abriendo post en nueva pestaña...")
        try:
            await page_comentarios.goto(post_url, wait_until=CONFIG['wait_until'], timeout=30000)
        except:
            await page_comentarios.goto(post_url, wait_until='domcontentloaded')
        
        # Esperar primera carga de comentarios
        print(f"    ⏳ Esperando carga de comentarios...")
        try:
            await page_comentarios.wait_for_selector('shreddit-comment', timeout=10000)
        except:
            print(f"    ⚠ Timeout esperando comentarios")
        
        await asyncio.sleep(PAUSA_PRIMERA_CARGA_COMENTARIOS)
        
        # Contar comentarios iniciales
        comentarios_visibles = await contar_comentarios_en_dom(page_comentarios)
        print(f"    📊 Comentarios visibles: {comentarios_visibles}")
        
        # VALIDACIÓN: ¿Vale la pena hacer scroll?
        if comentarios_visibles < MIN_COMENTARIOS_THRESHOLD:
            print(f"    ⚠ Menos de {MIN_COMENTARIOS_THRESHOLD} comentarios, extracción rápida")
            comentarios_extraidos = await extraer_comentarios_simples(page_comentarios, post_id)
            return comentarios_extraidos
        
        # Expandir comentarios colapsados si está habilitado
        if MAX_EXPANDIR_COLAPSADOS > 0:
            await expandir_comentarios_colapsados(page_comentarios, MAX_EXPANDIR_COLAPSADOS)
        
        # Script de extracción de comentarios
        script_comentarios = """
        (function () {
            const comentarios = [];
            const seen = new Set();
            
            const comments = document.querySelectorAll('shreddit-comment');
            
            comments.forEach(comment => {
                try {
                    const commentId = comment.getAttribute('thingid');
                    
                    if (!commentId) return;
                    if (!commentId.startsWith('t1_')) return;
                    if (seen.has(commentId)) return;
                    seen.add(commentId);
                    
                    const author = comment.getAttribute('author') || 'Desconocido';
                    const score = parseInt(comment.getAttribute('score')) || 0;
                    const depth = parseInt(comment.getAttribute('depth')) || 0;
                    
                    // Timestamp
                    let timestamp = '';
                    const timeEl = comment.querySelector('time');
                    if (timeEl) {
                        timestamp = timeEl.getAttribute('datetime') || timeEl.textContent.trim();
                    }
                    
                    // Texto del comentario
                    let texto = '';
                    const textEl = comment.querySelector('div[slot="comment"]');
                    if (textEl) {
                        texto = textEl.textContent.trim();
                    }
                    
                    // Solo agregar si tiene texto
                    if (texto && texto.length > 0) {
                        comentarios.push({
                            commentId: commentId,
                            author: author,
                            score: score,
                            depth: depth,
                            timestamp: timestamp,
                            texto: texto.substring(0, 2000)  // Limitar longitud
                        });
                    }
                    
                } catch (e) {
                    console.error('Error procesando comentario:', e);
                }
            });
            
            return comentarios;
        })();
        """
        
        # Extracción inicial
        comentarios_actuales = await page_comentarios.evaluate(script_comentarios)
        
        comentarios_extraidos = []
        comentarios_ids_vistos = set()
        
        # Agregar comentarios iniciales
        for comment in comentarios_actuales:
            if comment['commentId'] not in comentarios_ids_vistos and len(comentarios_extraidos) < max_comentarios:
                comentarios_ids_vistos.add(comment['commentId'])
                
                comment_data = {
                    "id_post": post_id,
                    "tipo": "comentario",
                    "autor": comment["author"],
                    "contenido": comment["texto"],
                    "votos": comment["score"],
                    "depth": comment["depth"],
                    "fecha": comment["timestamp"],
                    "tema_busqueda": "",  # Se agregará después
                    "fecha_extraccion": FECHA_EXTRACCION
                }
                
                comentarios_extraidos.append(comment_data)
        
        print(f"    ✓ Extraídos {len(comentarios_extraidos)} comentarios iniciales")
        
        # SCROLL INTELIGENTE si necesitamos más comentarios
        if len(comentarios_extraidos) < max_comentarios and comentarios_visibles >= MIN_COMENTARIOS_THRESHOLD:
            
            print(f"    📜 Iniciando scroll para más comentarios...")
            
            intentos_scroll = 0
            sin_nuevos = 0
            
            while len(comentarios_extraidos) < max_comentarios and intentos_scroll < MAX_SCROLLS_COMENTARIOS:
                
                # Scroll
                hubo_cambio = await scroll_pagina(page_comentarios, PAUSA_SCROLL_COMENTARIOS, CONFIG)
                intentos_scroll += 1
                
                if not hubo_cambio:
                    sin_nuevos += 1
                    if sin_nuevos >= 2:
                        print(f"      ⚠ No hay más comentarios disponibles")
                        break
                else:
                    sin_nuevos = 0
                
                # Detectar botón "Load more"
                if await detectar_boton_load_more(page_comentarios):
                    if not BUSQUEDA_PROFUNDA:
                        print(f"      📍 Botón 'Load more' detectado, deteniendo scroll")
                        break
                    else:
                        # Click en Load more si búsqueda profunda está activada
                        print(f"      🔽 Click en 'Load more comments'...")
                        try:
                            boton = await page_comentarios.query_selector('button:has-text("Load more comments"), button:has-text("Ver más comentarios")')
                            if boton:
                                await boton.click()
                                await asyncio.sleep(PAUSA_LOAD_MORE)
                        except Exception as e:
                            print(f"      ⚠ Error clickeando 'Load more': {e}")
                
                await asyncio.sleep(PAUSA_ENTRE_SCROLLS_COMENTARIOS)
                
                # Extraer nuevos comentarios
                comentarios_actuales = await page_comentarios.evaluate(script_comentarios)
                
                nuevos_agregados = 0
                for comment in comentarios_actuales:
                    if comment['commentId'] not in comentarios_ids_vistos and len(comentarios_extraidos) < max_comentarios:
                        comentarios_ids_vistos.add(comment['commentId'])
                        
                        comment_data = {
                            "id_post": post_id,
                            "tipo": "comentario",
                            "autor": comment["author"],
                            "contenido": comment["texto"],
                            "votos": comment["score"],
                            "depth": comment["depth"],
                            "fecha": comment["timestamp"],
                            "tema_busqueda": "",
                            "fecha_extraccion": FECHA_EXTRACCION
                        }
                        
                        comentarios_extraidos.append(comment_data)
                        nuevos_agregados += 1
                
                if nuevos_agregados == 0:
                    sin_nuevos += 1
                else:
                    print(f"      ✓ +{nuevos_agregados} nuevos comentarios (Total: {len(comentarios_extraidos)})")
                    sin_nuevos = 0
        
        print(f"    ✅ Total: {len(comentarios_extraidos)} comentarios extraídos")
        
        return comentarios_extraidos
        
    except Exception as e:
        print(f"    ❌ Error extrayendo comentarios: {e}")
        return []
        
    finally:
        # Cerrar pestaña
        await page_comentarios.close()
        print(f"    🔒 Pestaña cerrada")


async def extraer_comentarios_simples(page, post_id):
    """Extracción rápida sin scroll para posts con pocos comentarios"""
    
    script_comentarios = """
    (function () {
        const comentarios = [];
        const seen = new Set();
        
        const comments = document.querySelectorAll('shreddit-comment');
        
        comments.forEach(comment => {
            try {
                const commentId = comment.getAttribute('thingid');
                
                if (!commentId || !commentId.startsWith('t1_')) return;
                if (seen.has(commentId)) return;
                seen.add(commentId);
                
                const author = comment.getAttribute('author') || 'Desconocido';
                const score = parseInt(comment.getAttribute('score')) || 0;
                const depth = parseInt(comment.getAttribute('depth')) || 0;
                
                let timestamp = '';
                const timeEl = comment.querySelector('time');
                if (timeEl) {
                    timestamp = timeEl.getAttribute('datetime') || timeEl.textContent.trim();
                }
                
                let texto = '';
                const textEl = comment.querySelector('div[slot="comment"]');
                if (textEl) {
                    texto = textEl.textContent.trim();
                }
                
                if (texto && texto.length > 0) {
                    comentarios.push({
                        commentId: commentId,
                        author: author,
                        score: score,
                        depth: depth,
                        timestamp: timestamp,
                        texto: texto.substring(0, 2000)
                    });
                }
                
            } catch (e) {
                console.error('Error procesando comentario:', e);
            }
        });
        
        return comentarios;
    })();
    """
    
    comentarios_actuales = await page.evaluate(script_comentarios)
    
    comentarios_extraidos = []
    for comment in comentarios_actuales:
        comment_data = {
            "id_post": post_id,
            "tipo": "comentario",
            "autor": comment["author"],
            "contenido": comment["texto"],
            "votos": comment["score"],
            "depth": comment["depth"],
            "fecha": comment["timestamp"],
            "tema_busqueda": "",
            "fecha_extraccion": FECHA_EXTRACCION
        }
        comentarios_extraidos.append(comment_data)
    
    return comentarios_extraidos


# =====================================================
# MAIN
# =====================================================

async def main(posts_por_tema=None, temas_buscar=None, modo_interactivo=True):
    """Main optimizado con extracción de posts y comentarios"""
    
    if temas_buscar is None:
        temas_buscar = TERMINOS_BUSQUEDA
    
    if posts_por_tema is None:
        posts_por_tema = MAX_POSTS
    
    primera_vez = not os.path.exists(PROFILE_DIR)
    
    if modo_interactivo:
        modo_texto = "RÁPIDO" if MODO_RAPIDO else "BALANCEADO"
        print(f"""
        ╔════════════════════════════════════════════════════╗
        ║   EXTRACTOR REDDIT - Stealth Mode v3.0           ║
        ║   Posts + Comentarios                             ║
        ╚════════════════════════════════════════════════════╝
        
⚙️  CONFIGURACIÓN - POSTS:
   • Modo: {modo_texto}
   • Viewport: {VIEWPORT['width']}×{VIEWPORT['height']} px
   • Posts objetivo: {posts_por_tema} por término
   • Scroll: Inteligente
   • Mouse: Aleatorio {int(CONFIG['probabilidad_mouse']*100)}%

💬 CONFIGURACIÓN - COMENTARIOS:
   • Extracción: {'✓ ACTIVADA' if EXTRAER_COMENTARIOS else '✗ DESACTIVADA'}
   • Max comentarios/post: {MAX_COMENTARIOS_POR_POST}
   • Búsqueda profunda: {'✓ SÍ' if BUSQUEDA_PROFUNDA else '✗ NO'}
   • Expandir colapsados: {MAX_EXPANDIR_COLAPSADOS}
   • Min threshold: {MIN_COMENTARIOS_THRESHOLD}
        """)
        
        if primera_vez:
            print("🆕 PRIMERA EJECUCIÓN DETECTADA")
            print(f"   → Se creará perfil en: {PROFILE_DIR}")
            print("   → Necesitarás iniciar sesión en Reddit\n")
        else:
            print("✓ Perfil existente detectado")
            print(f"   → Usando sesión guardada\n")
        
        await asyncio.sleep(2)
    
    tiempo_inicio = datetime.now()
    todos_posts = []
    todos_comentarios = []
    
    async with async_playwright() as p:
        
        context, navegador_usado = await detectar_navegador_disponible(p)
        
        if len(context.pages) > 0:
            page = context.pages[0]
        else:
            page = await context.new_page()
        
        # Scripts anti-detección
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        try:
            sesion_ok = await verificar_y_preparar_sesion(page)
            
            if not sesion_ok and primera_vez:
                print("⚠️  Continuando sin sesión confirmada...\n")
            
            # Extracción de posts
            for i, termino in enumerate(temas_buscar, 1):
                print(f"\n[{i}/{len(temas_buscar)}] Procesando término: '{termino}'")
                
                posts = await extraer_posts_reddit(
                    page,
                    termino,
                    max_posts=posts_por_tema,
                    config=CONFIG
                )
                
                todos_posts.extend(posts)
                
                # Extracción de comentarios si está activada
                if EXTRAER_COMENTARIOS and len(posts) > 0:
                    print(f"\n{'─'*60}")
                    print(f"💬 EXTRAYENDO COMENTARIOS ({len(posts)} posts)")
                    print(f"{'─'*60}")
                    
                    for idx, post in enumerate(posts, 1):
                        print(f"\n  [{idx}/{len(posts)}] Post: {post['id_post'][:12]}...")
                        
                        comentarios = await extraer_comentarios_post(
                            context,
                            post['url'],
                            post['id_post'],
                            max_comentarios=MAX_COMENTARIOS_POR_POST
                        )
                        
                        # Agregar tema_busqueda a cada comentario
                        for comentario in comentarios:
                            comentario['tema_busqueda'] = post['tema_busqueda']
                        
                        todos_comentarios.extend(comentarios)
                        
                        # Pausa entre posts (parametrizada)
                        if idx < len(posts):
                            pausa = random.uniform(*PAUSA_ENTRE_POSTS_COMENTARIOS)
                            print(f"  ⏸  Pausa {pausa:.1f}s antes del siguiente post...")
                            await asyncio.sleep(pausa)
                
                if i < len(temas_buscar):
                    pausa = random.uniform(*CONFIG['pausa_entre_terminos'])
                    print(f"\n⏸  Pausa de {pausa:.1f}s antes del siguiente término...")
                    await asyncio.sleep(pausa)
            
            # Guardar datos en UN SOLO CSV unificado
            os.makedirs('datos_extraidos', exist_ok=True)
            
            if todos_posts or todos_comentarios:
                # Combinar posts y comentarios en un solo dataset
                datos_unificados = []
                
                # Agregar posts
                for post in todos_posts:
                    datos_unificados.append({
                        "id_post": post["id_post"],
                        "tipo": post["tipo"],
                        "autor": post["autor"],
                        "contenido": post["contenido"],
                        "votos": post.get("votos", 0),
                        "depth": 0,  # Posts tienen depth 0
                        "fecha": post["fecha"],
                        "tema_busqueda": post["tema_busqueda"],
                        "fecha_extraccion": post["fecha_extraccion"],
                        # Campos adicionales solo para posts
                        "comentarios_count": post.get("comentarios", 0),
                        "url": post.get("url", ""),
                        "thumbnail": post.get("thumbnail", "")
                    })
                
                # Agregar comentarios después de cada post
                for post in todos_posts:
                    comentarios_del_post = [c for c in todos_comentarios if c['id_post'] == post['id_post']]
                    for comentario in comentarios_del_post:
                        datos_unificados.append({
                            "id_post": comentario["id_post"],
                            "tipo": comentario["tipo"],
                            "autor": comentario["autor"],
                            "contenido": comentario["contenido"],
                            "votos": comentario.get("votos", 0),
                            "depth": comentario.get("depth", 0),
                            "fecha": comentario["fecha"],
                            "tema_busqueda": comentario["tema_busqueda"],
                            "fecha_extraccion": comentario["fecha_extraccion"],
                            # Campos vacíos para comentarios
                            "comentarios_count": "",
                            "url": "",
                            "thumbnail": ""
                        })
                
                # Guardar CSV único
                df_unificado = pd.DataFrame(datos_unificados)
                df_unificado['contenido'] = df_unificado['contenido'].str.replace(r'[\n\r\t]+', ' ', regex=True).str.strip()
                nombre_archivo = 'datos_extraidos/reddit.csv'
                df_unificado.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
            
            tiempo_total = (datetime.now() - tiempo_inicio).total_seconds()
            
            print(f"\n{'='*60}")
            print(f"✓ EXTRACCIÓN COMPLETADA")
            print(f"{'='*60}")
            
            if todos_posts or todos_comentarios:
                print(f"📁 Archivo unificado: {nombre_archivo}")
                print(f"📊 Total registros: {len(datos_unificados)}")
                print(f"   • Posts: {len(todos_posts)}")
                print(f"   • Comentarios: {len(todos_comentarios)}")
                print(f"🔑 Posts únicos: {len(set(p['id_post'] for p in todos_posts))}")
                if todos_comentarios:
                    comentarios_unicos = len(set((c['id_post'], c.get('autor', ''), c.get('contenido', '')[:50]) for c in todos_comentarios))
                    print(f"🔑 Comentarios únicos: {comentarios_unicos}")
            
            print(f"\n🌐 Navegador: {navegador_usado}")
            print(f"💾 Perfil: {PROFILE_DIR}")
            print(f"⏱️  Tiempo total: {tiempo_total:.1f} segundos")
            
            if EXTRAER_COMENTARIOS and todos_posts:
                promedio = tiempo_total / len(todos_posts)
                print(f"⏱️  Tiempo promedio/post: {promedio:.1f} segundos")
            
            print(f"{'='*60}\n")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            print("\n🔒 Cerrando navegador...")
            await context.close()
            print("✓ Sesión guardada\n")


if __name__ == "__main__":
    asyncio.run(main(
        posts_por_tema=MAX_POSTS,
        temas_buscar=TERMINOS_BUSQUEDA,
        modo_interactivo=True
    ))