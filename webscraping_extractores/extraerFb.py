"""
============================================
EXTRACTOR DE POSTS Y COMENTARIOS DE FACEBOOK
CON APERTURA AUTOMÁTICA DE VIVALDI
============================================
"""

import requests
import json
import time
import pandas as pd
from datetime import datetime
import websocket
import threading
import random
import hashlib
import math
import subprocess
import os

FECHA_EXTRACCION = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# =====================================================
# CONFIGURACIÓN GLOBAL - POSTS
# =====================================================

VIVALDI_DEBUG_PORT = 9225
VIVALDI_PATH = r"C:\Users\USUARIO\AppData\Local\Vivaldi\Application\vivaldi.exe"
BASE_URL = f"http://127.0.0.1:{VIVALDI_DEBUG_PORT}"

# Configuración de posts
MAX_POSTS = 50
POSTS_ESTIMADOS_INICIAL = 3
POSTS_ESTIMADOS_POR_SCROLL = 2
MAX_SCROLLS = 15

# =====================================================
# CONFIGURACIÓN GLOBAL - COMENTARIOS
# =====================================================

EXTRAER_COMENTARIOS = False
MAX_COMENTARIOS_POR_POST = 20

EXPANDIR_VER_MAS = True
MAX_EXPANDIR_COMENTARIOS = 3

MAX_SCROLLS_COMENTARIOS = 3
MIN_COMENTARIOS_THRESHOLD = 3

PAUSA_SCROLL_BASE = (1.5, 2.5)
PAUSA_PRIMERA_CARGA = 8
PAUSA_ENTRE_POSTS = (2, 4)
PAUSA_EXPANSION = 2.0
PAUSA_ENTRE_TERMINOS = (5, 8)

DEDUPLICAR_POSTS = True

# =====================================================
# MODO PARAMETRIZABLE
# =====================================================

MODO_RAPIDO = False

CONFIG_RAPIDO = {
    'tiempo_espera': (1.5, 2.5),
    'scroll_pausa': (1.0, 1.5),
    'probabilidad_mouse': 0.2,
    'max_scrolls_sin_cambio': 2,
}

CONFIG_BALANCEADO = {
    'tiempo_espera': (2.5, 4.0),
    'scroll_pausa': (1.5, 2.5),
    'probabilidad_mouse': 0.4,
    'max_scrolls_sin_cambio': 3,
}

CONFIG = CONFIG_RAPIDO if MODO_RAPIDO else CONFIG_BALANCEADO

# =====================================================
# FUNCIÓN PARA ABRIR VIVALDI
# =====================================================

def abrir_vivaldi_con_debugging():
    """Abre Vivaldi con remote debugging habilitado en el puerto 9225"""
    print("=" * 70)
    print("Iniciando Vivaldi con modo de depuración remota...")
    print(f"Puerto: {VIVALDI_DEBUG_PORT}")
    print("=" * 70)
    
    if not os.path.exists(VIVALDI_PATH):
        print(f"❌ No se encontró Vivaldi en: {VIVALDI_PATH}")
        print("Por favor, verifica la ruta de instalación")
        return None
    
    cmd = [
        VIVALDI_PATH,
        f"--remote-debugging-port={VIVALDI_DEBUG_PORT}",
        "--remote-allow-origins=*",
        "https://www.facebook.com"
    ]
    
    try:
        proceso = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("✅ Vivaldi iniciado correctamente")
        print("⏳ Esperando a que el navegador esté listo...")
        time.sleep(5)
        
        return proceso
        
    except Exception as e:
        print(f"❌ Error al iniciar Vivaldi: {e}")
        return None

# =====================================================
# CLASE CDP CLIENT
# =====================================================

class CDPClient:
    """Cliente CDP con timeout y manejo de errores mejorados"""
    
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self.message_id = 0
        self.responses = {}
        self.events = []
        self.lock = threading.Lock()
        self.running = False
        
    def connect(self):
        """Conecta al WebSocket del navegador"""
        self.ws = websocket.create_connection(self.ws_url)
        self.running = True
        threading.Thread(target=self._receive_messages, daemon=True).start()
        time.sleep(1)
        
    def _receive_messages(self):
        """Recibe mensajes del WebSocket en background"""
        while self.running:
            try:
                message = self.ws.recv()
                data = json.loads(message)
                
                with self.lock:
                    if 'id' in data:
                        self.responses[data['id']] = data
                    elif 'method' in data:
                        self.events.append(data)
            except Exception as e:
                if self.running:
                    print(f"Error recibiendo mensaje: {e}")
                break
    
    def send_command(self, method, params=None, timeout=15):
        """Envía comando CDP con timeout configurable"""
        if not self.running or not self.ws:
            print("✗ WebSocket no conectado")
            return None
            
        self.message_id += 1
        msg_id = self.message_id
        
        command = {
            "id": msg_id,
            "method": method,
            "params": params or {}
        }
        
        try:
            self.ws.send(json.dumps(command))
        except Exception as e:
            print(f"✗ Error enviando comando: {e}")
            return None
        
        start = time.time()
        while True:
            with self.lock:
                if msg_id in self.responses:
                    response = self.responses.pop(msg_id)
                    return response
            
            if time.time() - start > timeout:
                print(f"⚠ Timeout esperando respuesta para {method}")
                return None
            time.sleep(0.05)
    
    def evaluate(self, expression, timeout=10):
        """Ejecuta JavaScript con manejo robusto de errores"""
        try:
            result = self.send_command("Runtime.evaluate", {
                "expression": expression,
                "returnByValue": True
            }, timeout=timeout)
            
            if not result:
                return None
            
            if 'exceptionDetails' in result:
                return None
            
            if 'result' not in result:
                return None
            
            result_obj = result['result']
            
            if list(result_obj.keys()) == ['result']:
                result_obj = result_obj['result']
            
            if 'value' in result_obj:
                return result_obj['value']
            
            obj_type = result_obj.get('type')
            
            if obj_type == 'undefined':
                return None
            
            if obj_type == 'number' and 'description' in result_obj:
                try:
                    return float(result_obj['description'])
                except:
                    pass
            
            if obj_type == 'string' and 'description' in result_obj:
                return result_obj['description']
            
            if obj_type == 'boolean':
                desc = result_obj.get('description', '').lower()
                if desc == 'true':
                    return True
                elif desc == 'false':
                    return False
            
            return None
            
        except Exception as e:
            return None
    
    def navigate(self, url):
        """Navega a URL con espera de carga"""
        result = self.send_command("Page.navigate", {"url": url})
        time.sleep(2)
        
        max_wait = 15
        start = time.time()
        while time.time() - start < max_wait:
            ready = self.evaluate("document.readyState")
            if ready in ['interactive', 'complete']:
                print(f"✓ Página cargada")
                return result
            time.sleep(0.5)
        
        print("⚠ Timeout esperando carga")
        return result
    
    def close(self):
        """Cierra conexión"""
        self.running = False
        if self.ws:
            try:
                self.ws.close()
            except:
                pass

# =====================================================
# FUNCIONES AUXILIARES
# =====================================================

def generar_hash_contenido(contenido):
    """Genera hash único para detectar duplicados"""
    texto_limpio = contenido[:200].strip().lower()
    return hashlib.md5(texto_limpio.encode()).hexdigest()

def contar_posts_en_dom(client):
    """Cuenta posts actualmente en el DOM"""
    try:
        count = client.evaluate("""
            document.querySelectorAll(
                'div[data-ad-comet-preview="message"], div[data-ad-preview="message"]'
            ).length
        """)
        return count if count else 0
    except:
        return 0

def contar_comentarios_visibles(client):
    """Cuenta comentarios visibles en la página actual"""
    try:
        count = client.evaluate("""
            (function() {
                let count = 0;
                document.querySelectorAll('span[dir="auto"]').forEach(span => {
                    const txt = span.textContent.trim();
                    if (txt.length > 20 && txt.length < 400) {
                        count++;
                    }
                });
                return count;
            })();
        """)
        return count if count else 0
    except:
        return 0

# =====================================================
# FUNCIONES DE SCRAPING - GENERALES
# =====================================================

def conectar_navegador():
    """Conecta al navegador Vivaldi en modo debug"""
    try:
        print(f"Intentando conectar a Vivaldi en puerto {VIVALDI_DEBUG_PORT}...")
        response = requests.get(f"{BASE_URL}/json", timeout=5)
        tabs = response.json()
        
        if not tabs:
            print("✗ No hay tabs abiertas en Vivaldi")
            return None

        print(f"✓ Encontradas {len(tabs)} tabs en Vivaldi\n")

        tab = None
        for t in tabs:
            url = t.get('url', '')
            tab_type = t.get('type', '')
            
            if tab_type == 'page' and 'facebook.com' in url:
                tab = t
                print(f"✓ Tab de Facebook encontrada")
                break
        
        if not tab:
            for t in tabs:
                if t.get('type') == 'page':
                    tab = t
                    print(f"⚠ Usando tab: {t.get('url', '')[:60]}")
                    break
        
        if not tab:
            print("\n✗ No se encontró tab tipo 'page'")
            return None
        
        print(f"✓ Conectando a: {tab.get('title', 'Sin título')[:50]}")
        
        ws_url = tab['webSocketDebuggerUrl']
        client = CDPClient(ws_url)
        client.connect()
        
        print("Habilitando Runtime y Page...")
        client.send_command("Runtime.enable")
        client.send_command("Page.enable")
        
        print("Verificando JavaScript...")
        test = client.evaluate("1 + 1")
        
        if test != 2:
            print("✗ JavaScript no funciona correctamente")
            return None
        
        print("✓ JavaScript funcionando\n")
        return client
        
    except requests.exceptions.ConnectionError:
        print(f"✗ No se pudo conectar al puerto {VIVALDI_DEBUG_PORT}")
        return None
    except Exception as e:
        print(f"✗ Error al conectar: {e}")
        return None

def simular_interaccion_humana(client, tipo='scroll', config=CONFIG):
    """Simula comportamiento humano"""
    try:
        if tipo == 'scroll':
            scroll_amount = random.randint(300, 800)
            client.evaluate(f"window.scrollBy(0, {scroll_amount});")
            pausa = random.uniform(0.5, 1.5)
            time.sleep(pausa)
            return True
            
        elif tipo == 'mouse_move':
            if random.random() < config['probabilidad_mouse']:
                script = f"""
                (function() {{
                    const event = new MouseEvent('mousemove', {{
                        clientX: {random.randint(100, 800)},
                        clientY: {random.randint(100, 600)},
                        bubbles: true
                    }});
                    document.dispatchEvent(event);
                }})();
                """
                client.evaluate(script)
                return True
            return False
            
        elif tipo == 'pause':
            pausa = random.uniform(*config['tiempo_espera'])
            time.sleep(pausa)
            return True
            
    except Exception as e:
        return False

def scroll_pagina(client, config=CONFIG):
    """Scroll inteligente con detección de cambios"""
    try:
        altura_antes = client.evaluate("document.body.scrollHeight")
        if altura_antes is None:
            return False
        
        client.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        
        pausa = random.uniform(*config['scroll_pausa'])
        time.sleep(pausa)
        
        altura_despues = client.evaluate("document.body.scrollHeight")
        if altura_despues is None:
            return False
        
        cambio = altura_despues > altura_antes
        if cambio:
            print(f"  📜 Scroll: {altura_antes:,} → {altura_despues:,} px")
        
        return cambio
        
    except Exception as e:
        print(f"✗ Error en scroll: {e}")
        return False

def expandir_contenido(client):
    """Expande botones 'Ver más' y comentarios"""
    try:
        script = """
        (function() {
            let clicks = 0;
            
            const verMasBotones = Array.from(document.querySelectorAll('div[role="button"]'))
                .filter(btn => {
                    const text = btn.textContent.trim();
                    return text === 'Ver más' || text === 'See more' || 
                           text.includes('Ver más');
                });
            
            verMasBotones.slice(0, 10).forEach(btn => {
                try {
                    btn.click();
                    clicks++;
                } catch(e) {}
            });
            
            const comentariosBotones = Array.from(document.querySelectorAll('span'))
                .filter(s => s.textContent.includes('Ver más comentarios') || 
                             s.textContent.includes('comentarios anteriores'));
            
            comentariosBotones.slice(0, 5).forEach(btn => {
                try {
                    btn.click();
                    clicks++;
                } catch(e) {}
            });
            
            return clicks;
        })();
        """
        
        clicks = client.evaluate(script)
        if clicks and clicks > 0:
            print(f"  🔓 Expandidos {clicks} elementos")
            time.sleep(PAUSA_EXPANSION)
        
        return clicks or 0
        
    except Exception as e:
        return 0

# =====================================================
# FUNCIONES DE SCRAPING - POSTS
# =====================================================

def extraer_posts_facebook(client, termino, max_posts=10, config=CONFIG):
    """Extrae posts con scroll inteligente y deduplicación"""
    
    print(f"\n{'='*60}")
    print(f"FACEBOOK | Buscando: {termino}")
    print(f"{'='*60}")
    
    url_busqueda = f"https://www.facebook.com/search/posts/?q={termino.replace(' ', '%20')}"
    print(f"Navegando a: {url_busqueda}")
    
    url_actual = client.evaluate("window.location.href")
    if not url_actual or termino.replace(" ", "%20") not in url_actual:
        client.navigate(url_busqueda)
    
    print(f"⏳ Esperando carga inicial ({PAUSA_PRIMERA_CARGA}s)...")
    time.sleep(PAUSA_PRIMERA_CARGA)
    
    posts_en_dom = contar_posts_en_dom(client)
    print(f"📊 Posts en DOM: {posts_en_dom}")
    
    pausa_inicial = random.uniform(*config['tiempo_espera'])
    time.sleep(pausa_inicial)
    
    moved = simular_interaccion_humana(client, 'mouse_move', config)
    if moved:
        print("🖱️  Movimiento de mouse")
    
    script_extraccion = """
    (function () {
        const posts = [];
        const seen = new Set();
        
        const messageNodes = document.querySelectorAll(
            'div[data-ad-comet-preview="message"], div[data-ad-preview="message"]'
        );
        
        messageNodes.forEach((msgNode, idx) => {
            try {
                let container = msgNode;
                
                for (let i = 0; i < 6; i++) {
                    if (!container.parentElement) break;
                    container = container.parentElement;
                    
                    const textLen = container.textContent?.length || 0;
                    const buttons = container.querySelectorAll('[role="button"]').length;
                    
                    if (textLen > 120 && buttons >= 2) break;
                }
                
                if (!container || seen.has(container)) return;
                seen.add(container);
                
                let contenido = msgNode.textContent.trim();
                if (!contenido || contenido.length < 20) return;
                
                let autor = 'Desconocido';
                const header = container.querySelector('h2, h3, strong, a[role="link"]');
                if (header && header.textContent.length < 100) {
                    autor = header.textContent.trim();
                }
                
                let timestamp = '';
                const timeElem = container.querySelector('a[href*="/posts/"] span, a[href*="story"] span');
                if (timeElem) timestamp = timeElem.textContent.trim();
                
                let numComentarios = 0;
                let numReacciones = 0;
                
                container.querySelectorAll('[aria-label]').forEach(el => {
                    const label = el.getAttribute('aria-label');
                    if (!label) return;
                    
                    const match = label.match(/(\\d+)/);
                    if (!match) return;
                    
                    const val = parseInt(match[1]);
                    
                    if (label.includes('coment')) numComentarios = Math.max(numComentarios, val);
                    if (label.includes('reaccion') || label.includes('Me gusta'))
                        numReacciones = Math.max(numReacciones, val);
                });
                
                let postUrl = '';
                const linkElem = container.querySelector('a[href*="/posts/"], a[href*="story"]');
                if (linkElem) postUrl = linkElem.href;
                
                posts.push({
                    autor: autor,
                    contenido: contenido.substring(0, 2000),
                    timestamp: timestamp,
                    numComentarios: numComentarios,
                    numReacciones: numReacciones,
                    postUrl: postUrl
                });
                
            } catch (e) {
                console.error('Error procesando post', idx, e);
            }
        });
        
        return posts;
    })();
    """
    
    print("\n→ Extracción inicial")
    posts_actuales = client.evaluate(script_extraccion)
    
    if not posts_actuales:
        posts_actuales = []
    
    posts_extraidos = []
    posts_hashes_vistos = set()
    
    for post in posts_actuales:
        contenido_hash = generar_hash_contenido(post['contenido'])
        
        if DEDUPLICAR_POSTS and contenido_hash in posts_hashes_vistos:
            continue
        
        posts_hashes_vistos.add(contenido_hash)
        
        post_data = {
            "id_post": contenido_hash[:12],
            "tipo": "post",
            "autor": post["autor"],
            "contenido": post["contenido"],
            "timestamp": post["timestamp"],
            "num_comentarios": post.get("numComentarios", 0),
            "num_reacciones": post.get("numReacciones", 0),
            "url": post.get("postUrl", ""),
            "tema_busqueda": termino,
            "fecha_extraccion": FECHA_EXTRACCION
        }
        
        posts_extraidos.append(post_data)
        
        print(
            f"✓ Post {len(posts_extraidos)}/{max_posts} "
            f"| {post['autor'][:25]:25} "
            f"| {post.get('numReacciones', 0)} reacciones | {post.get('numComentarios', 0)} comentarios"
        )
        
        if len(posts_extraidos) >= max_posts:
            break
    
    if len(posts_extraidos) < max_posts:
        posts_faltantes = max_posts - len(posts_extraidos)
        scrolls_estimados = math.ceil(posts_faltantes / POSTS_ESTIMADOS_POR_SCROLL)
        
        print(f"\n📊 Faltan {posts_faltantes} posts, iniciando scroll inteligente...")
        print(f"   Scrolls estimados: ~{scrolls_estimados}")
        
        intentos_scroll = 0
        sin_nuevos = 0
        
        while len(posts_extraidos) < max_posts and intentos_scroll < MAX_SCROLLS:
            
            print(f"\n[Scroll {intentos_scroll + 1}/{MAX_SCROLLS}]")
            
            moved = simular_interaccion_humana(client, 'mouse_move', config)
            if moved:
                print("  🖱️  Movimiento de mouse")
            
            hubo_cambio = scroll_pagina(client, config)
            intentos_scroll += 1
            
            if not hubo_cambio:
                sin_nuevos += 1
                if sin_nuevos >= config['max_scrolls_sin_cambio']:
                    print(f"  ⚠ Sin cambios después de {config['max_scrolls_sin_cambio']} intentos")
                    break
            else:
                sin_nuevos = 0
            
            if EXPANDIR_VER_MAS:
                expandir_contenido(client)
            
            time.sleep(random.uniform(1, 2))
            
            posts_actuales = client.evaluate(script_extraccion)
            
            if not posts_actuales:
                posts_actuales = []
            
            nuevos_agregados = 0
            for post in posts_actuales:
                contenido_hash = generar_hash_contenido(post['contenido'])
                
                if contenido_hash not in posts_hashes_vistos and len(posts_extraidos) < max_posts:
                    posts_hashes_vistos.add(contenido_hash)
                    
                    post_data = {
                        "id_post": contenido_hash[:12],
                        "tipo": "post",
                        "autor": post["autor"],
                        "contenido": post["contenido"],
                        "timestamp": post["timestamp"],
                        "num_comentarios": post.get("numComentarios", 0),
                        "num_reacciones": post.get("numReacciones", 0),
                        "url": post.get("postUrl", ""),
                        "tema_busqueda": termino,
                        "fecha_extraccion": FECHA_EXTRACCION
                    }
                    
                    posts_extraidos.append(post_data)
                    nuevos_agregados += 1
                    
                    print(
                        f"  ✓ Post {len(posts_extraidos)}/{max_posts} "
                        f"| {post['autor'][:25]:25} "
                        f"| {post.get('numReacciones', 0)} reacciones"
                    )
            
            if nuevos_agregados == 0:
                sin_nuevos += 1
            else:
                sin_nuevos = 0
            
            if len(posts_extraidos) >= max_posts:
                print(f"\n  ✓ Objetivo alcanzado ({len(posts_extraidos)}/{max_posts})")
                break
    
    print(f"\n{'='*60}")
    print(f"FACEBOOK | Total extraído: {len(posts_extraidos)} posts")
    print(f"{'='*60}")
    
    return posts_extraidos

# =====================================================
# FUNCIONES DE SCRAPING - COMENTARIOS (SIMPLIFICADAS)
# =====================================================

def extraer_comentarios_post(client, post_data, max_comentarios=30):
    """Extrae comentarios de un post específico"""
    
    print(f"\n  💬 Extrayendo comentarios del post {post_data['id_post']}...")
    
    post_url = post_data.get('url', '')
    
    if not post_url or 'facebook.com' not in post_url:
        print(f"    ⚠ URL de post no válida")
        return []
    
    print(f"    → Navegando al post...")
    client.navigate(post_url)
    
    print(f"    ⏳ Esperando carga de comentarios...")
    time.sleep(PAUSA_PRIMERA_CARGA)
    
    comentarios_visibles = contar_comentarios_visibles(client)
    print(f"    📊 Comentarios visibles: {comentarios_visibles}")
    
    if comentarios_visibles < MIN_COMENTARIOS_THRESHOLD:
        print(f"    ⚠ Menos de {MIN_COMENTARIOS_THRESHOLD} comentarios, extracción rápida")
        comentarios = extraer_comentarios_simples(client, post_data['id_post'])
        return comentarios
    
    if MAX_EXPANDIR_COMENTARIOS > 0:
        expandir_comentarios_colapsados(client, MAX_EXPANDIR_COMENTARIOS)
    
    script_comentarios = """
    (function () {
        const comentarios = [];
        const seen = new Set();
        
        document.querySelectorAll('span[dir="auto"]').forEach(span => {
            try {
                const txt = span.textContent.trim();
                
                if (txt.length < 20 || txt.length > 1000) return;
                if (txt.includes('Me gusta') || txt.includes('Responder')) return;
                if (seen.has(txt)) return;
                seen.add(txt);
                
                let autor = 'Desconocido';
                let parent = span.parentElement;
                
                for (let i = 0; i < 5 && parent; i++) {
                    const link = parent.querySelector('a[role="link"]');
                    if (link && link.textContent.length < 100) {
                        autor = link.textContent.trim();
                        break;
                    }
                    parent = parent.parentElement;
                }
                
                comentarios.push({
                    autor: autor,
                    texto: txt.substring(0, 1000)
                });
                
            } catch (e) {
                console.error('Error procesando comentario:', e);
            }
        });
        
        return comentarios;
    })();
    """
    
    comentarios_actuales = client.evaluate(script_comentarios)
    
    if not comentarios_actuales:
        comentarios_actuales = []
    
    comentarios_extraidos = []
    comentarios_textos_vistos = set()
    
    for comentario in comentarios_actuales:
        texto = comentario['texto']
        
        if texto not in comentarios_textos_vistos and len(comentarios_extraidos) < max_comentarios:
            comentarios_textos_vistos.add(texto)
            
            comment_data = {
                "id_post": post_data['id_post'],
                "tipo": "comentario",
                "autor": comentario["autor"],
                "contenido": texto,
                "tema_busqueda": post_data['tema_busqueda'],
                "fecha_extraccion": FECHA_EXTRACCION
            }
            
            comentarios_extraidos.append(comment_data)
    
    print(f"    ✓ Extraídos {len(comentarios_extraidos)} comentarios iniciales")
    
    if len(comentarios_extraidos) < max_comentarios and comentarios_visibles >= MIN_COMENTARIOS_THRESHOLD:
        
        print(f"    📜 Scroll para más comentarios...")
        
        intentos_scroll = 0
        sin_nuevos = 0
        
        while len(comentarios_extraidos) < max_comentarios and intentos_scroll < MAX_SCROLLS_COMENTARIOS:
            
            hubo_cambio = scroll_pagina(client, CONFIG)
            intentos_scroll += 1
            
            if not hubo_cambio:
                sin_nuevos += 1
                if sin_nuevos >= 2:
                    print(f"      ⚠ Sin nuevos comentarios")
                    break
            else:
                sin_nuevos = 0
            
            time.sleep(1)
            
            comentarios_actuales = client.evaluate(script_comentarios)
            
            if not comentarios_actuales:
                comentarios_actuales = []
            
            nuevos_agregados = 0
            for comentario in comentarios_actuales:
                texto = comentario['texto']
                
                if texto not in comentarios_textos_vistos and len(comentarios_extraidos) < max_comentarios:
                    comentarios_textos_vistos.add(texto)
                    
                    comment_data = {
                        "id_post": post_data['id_post'],
                        "tipo": "comentario",
                        "autor": comentario["autor"],
                        "contenido": texto,
                        "tema_busqueda": post_data['tema_busqueda'],
                        "fecha_extraccion": FECHA_EXTRACCION
                    }
                    
                    comentarios_extraidos.append(comment_data)
                    nuevos_agregados += 1
            
            if nuevos_agregados == 0:
                sin_nuevos += 1
            else:
                print(f"      ✓ +{nuevos_agregados} nuevos (Total: {len(comentarios_extraidos)})")
                sin_nuevos = 0
    
    print(f"    ✅ Total: {len(comentarios_extraidos)} comentarios extraídos")
    
    return comentarios_extraidos

def extraer_comentarios_simples(client, post_id):
    """Extracción rápida de comentarios sin scroll"""
    
    script = """
    (function () {
        const comentarios = [];
        const seen = new Set();
        
        document.querySelectorAll('span[dir="auto"]').forEach(span => {
            try {
                const txt = span.textContent.trim();
                
                if (txt.length < 20 || txt.length > 1000) return;
                if (txt.includes('Me gusta') || txt.includes('Responder')) return;
                if (seen.has(txt)) return;
                seen.add(txt);
                
                let autor = 'Desconocido';
                let parent = span.parentElement;
                
                for (let i = 0; i < 5 && parent; i++) {
                    const link = parent.querySelector('a[role="link"]');
                    if (link && link.textContent.length < 100) {
                        autor = link.textContent.trim();
                        break;
                    }
                    parent = parent.parentElement;
                }
                
                comentarios.push({
                    autor: autor,
                    texto: txt.substring(0, 1000)
                });
                
            } catch (e) {}
        });
        
        return comentarios;
    })();
    """
    
    comentarios_actuales = client.evaluate(script)
    
    if not comentarios_actuales:
        return []
    
    comentarios_extraidos = []
    for comentario in comentarios_actuales:
        comment_data = {
            "id_post": post_id,
            "tipo": "comentario",
            "autor": comentario["autor"],
            "contenido": comentario["texto"],
            "tema_busqueda": "",
            "fecha_extraccion": FECHA_EXTRACCION
        }
        comentarios_extraidos.append(comment_data)
    
    return comentarios_extraidos

def expandir_comentarios_colapsados(client, max_expandir=3):
    """Expande comentarios colapsados"""
    
    if max_expandir <= 0:
        return 0
    
    try:
        print(f"  🔓 Expandiendo hasta {max_expandir} comentarios...")
        
        script = f"""
        (function(maxExpandir) {{
            let count = 0;
            
            const buttons = Array.from(document.querySelectorAll('div[role="button"]'))
                .filter(btn => {{
                    const text = btn.textContent.trim();
                    return text.includes('Ver más comentarios') || 
                           text.includes('comentarios anteriores');
                }});
            
            for (let i = 0; i < Math.min(buttons.length, maxExpandir); i++) {{
                try {{
                    buttons[i].click();
                    count++;
                }} catch (e) {{}}
            }}
            
            return count;
        }})({max_expandir});
        """
        
        expandidos = client.evaluate(script)
        
        if expandidos and expandidos > 0:
            print(f"    ✓ {expandidos} comentarios expandidos")
            time.sleep(PAUSA_EXPANSION)
        
        return expandidos or 0
        
    except Exception as e:
        print(f"  ⚠ Error expandiendo: {e}")
        return 0

# =====================================================
# MAIN - CONTROLADO POR ORQUESTADOR
# =====================================================

async def main(posts_por_tema, temas_buscar):
    """Main para ser llamado por el orquestador"""
    
    # Abrir Vivaldi con debugging
    proceso_vivaldi = abrir_vivaldi_con_debugging()
    
    if proceso_vivaldi is None:
        print("❌ No se pudo iniciar Vivaldi. Abortando...")
        return
    
    try:
        # Esperar conexión
        tiempo_inicio = datetime.now()
        todos_posts = []
        todos_comentarios = []
        
        # Conectar
        max_intentos = 5
        intentos = 0
        client = None
        
        while intentos < max_intentos and client is None:
            try:
                intentos += 1
                print(f"Intento de conexión #{intentos}...")
                client = conectar_navegador()
                if client:
                    print("✅ Conectado a Vivaldi")
                    break
            except Exception as e:
                if intentos < max_intentos:
                    print(f"⏳ Esperando conexión... ({intentos}/{max_intentos})")
                    time.sleep(2)
                else:
                    print(f"❌ No se pudo conectar a Vivaldi después de {max_intentos} intentos")
                    return
        
        if not client:
            print("\n✗ No se pudo conectar al navegador")
            return
        
        print("✓ Conexión CDP establecida\n")
        
        # Ajuste de posts por tema
        posts_ajustados = posts_por_tema * 3
        
        # Extracción de posts
        for i, termino in enumerate(temas_buscar, 1):
            print(f"\n[{i}/{len(temas_buscar)}] Procesando término: '{termino}'")
            
            posts = extraer_posts_facebook(
                client,
                termino,
                max_posts=posts_ajustados,
                config=CONFIG
            )
            
            todos_posts.extend(posts)
            
            # Pausa entre términos
            if i < len(temas_buscar):
                pausa = random.uniform(*PAUSA_ENTRE_TERMINOS)
                print(f"\n⏸  Pausa de {pausa:.1f}s antes del siguiente término...")
                time.sleep(pausa)
        
        # Guardar en CSV
        import os
        os.makedirs('datos_extraidos', exist_ok=True)
        
        if todos_posts or todos_comentarios:
            datos_unificados = []
            
            for post in todos_posts:
                datos_unificados.append({
                    "id_post": post["id_post"],
                    "tipo": post["tipo"],
                    "autor": post["autor"],
                    "contenido": post["contenido"],
                    "timestamp": post.get("timestamp", ""),
                    "num_comentarios": post.get("num_comentarios", 0),
                    "num_reacciones": post.get("num_reacciones", 0),
                    "tema_busqueda": post["tema_busqueda"],
                    "fecha_extraccion": post["fecha_extraccion"],
                    "url": post.get("url", "")
                })
            
            for comentario in todos_comentarios:
                datos_unificados.append({
                    "id_post": comentario["id_post"],
                    "tipo": comentario["tipo"],
                    "autor": comentario["autor"],
                    "contenido": comentario["contenido"],
                    "timestamp": "",
                    "num_comentarios": "",
                    "num_reacciones": "",
                    "tema_busqueda": comentario["tema_busqueda"],
                    "fecha_extraccion": comentario["fecha_extraccion"],
                    "url": ""
                })
            
            df_unificado = pd.DataFrame(datos_unificados)
            nombre_archivo = 'datos_extraidos/facebook.csv'
            df_unificado.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
            
            tiempo_total = (datetime.now() - tiempo_inicio).total_seconds()
            
            print(f"\n{'='*60}")
            print(f"✓ EXTRACCIÓN COMPLETADA")
            print(f"{'='*60}")
            print(f"📁 Archivo: {nombre_archivo}")
            print(f"📊 Total registros: {len(datos_unificados)}")
            print(f"   • Posts: {len(todos_posts)}")
            print(f"   • Comentarios: {len(todos_comentarios)}")
            print(f"🔑 Posts únicos: {len(set(p['id_post'] for p in todos_posts))}")
            print(f"\n⏱️  Tiempo total: {tiempo_total:.1f} segundos")
            print(f"{'='*60}\n")
        
        else:
            print("\n✗ No se extrajo ningún post")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    if 'client' in locals() and client:  # o 'proceso_edge' o 'proceso_brave' o 'proceso_vivaldi'
        print("\nCerrando conexión...")

# =====================================================
# MAIN - LOCAL (para ejecución directa)
# =====================================================

def main_local():
    """Main local para ejecución directa del script"""
    
    TERMINOS_BUSQUEDA = [
        "nicolas muñoz",
    ]
    
    posts_por_tema = MAX_POSTS
    
    # Abrir Vivaldi
    proceso_vivaldi = abrir_vivaldi_con_debugging()
    
    if proceso_vivaldi is None:
        print("❌ No se pudo iniciar Vivaldi. Abortando...")
        return
    
    try:
        tiempo_inicio = datetime.now()
        todos_posts = []
        todos_comentarios = []
        
        # Conectar
        max_intentos = 5
        intentos = 0
        client = None
        
        while intentos < max_intentos and client is None:
            try:
                intentos += 1
                print(f"Intento de conexión #{intentos}...")
                client = conectar_navegador()
                if client:
                    print("✅ Conectado a Vivaldi")
                    break
            except Exception as e:
                if intentos < max_intentos:
                    print(f"⏳ Esperando conexión... ({intentos}/{max_intentos})")
                    time.sleep(2)
                else:
                    print(f"❌ No se pudo conectar a Vivaldi después de {max_intentos} intentos")
                    return
        
        if not client:
            print("\n✗ No se pudo conectar al navegador")
            return
        
        print("✓ Conexión CDP establecida\n")
        
        posts_ajustados = posts_por_tema * 3
        
        for i, termino in enumerate(TERMINOS_BUSQUEDA, 1):
            print(f"\n[{i}/{len(TERMINOS_BUSQUEDA)}] Procesando término: '{termino}'")
            
            posts = extraer_posts_facebook(
                client,
                termino,
                max_posts=posts_ajustados,
                config=CONFIG
            )
            
            todos_posts.extend(posts)
            
            if i < len(TERMINOS_BUSQUEDA):
                pausa = random.uniform(*PAUSA_ENTRE_TERMINOS)
                print(f"\n⏸  Pausa de {pausa:.1f}s antes del siguiente término...")
                time.sleep(pausa)
        
        # Guardar CSV
        import os
        os.makedirs('datos_extraidos', exist_ok=True)
        
        if todos_posts or todos_comentarios:
            datos_unificados = []
            
            for post in todos_posts:
                datos_unificados.append({
                    "id_post": post["id_post"],
                    "tipo": post["tipo"],
                    "autor": post["autor"],
                    "contenido": post["contenido"],
                    "timestamp": post.get("timestamp", ""),
                    "num_comentarios": post.get("num_comentarios", 0),
                    "num_reacciones": post.get("num_reacciones", 0),
                    "tema_busqueda": post["tema_busqueda"],
                    "fecha_extraccion": post["fecha_extraccion"],
                    "url": post.get("url", "")
                })
            
            for comentario in todos_comentarios:
                datos_unificados.append({
                    "id_post": comentario["id_post"],
                    "tipo": comentario["tipo"],
                    "autor": comentario["autor"],
                    "contenido": comentario["contenido"],
                    "timestamp": "",
                    "num_comentarios": "",
                    "num_reacciones": "",
                    "tema_busqueda": comentario["tema_busqueda"],
                    "fecha_extraccion": comentario["fecha_extraccion"],
                    "url": ""
                })
            
            df_unificado = pd.DataFrame(datos_unificados)
            nombre_archivo = 'datos_extraidos/facebook.csv'
            df_unificado.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
            
            tiempo_total = (datetime.now() - tiempo_inicio).total_seconds()
            
            print(f"\n{'='*60}")
            print(f"✓ EXTRACCIÓN COMPLETADA")
            print(f"{'='*60}")
            print(f"📁 Archivo: {nombre_archivo}")
            print(f"📊 Total registros: {len(datos_unificados)}")
            print(f"   • Posts: {len(todos_posts)}")
            print(f"   • Comentarios: {len(todos_comentarios)}")
            print(f"🔑 Posts únicos: {len(set(p['id_post'] for p in todos_posts))}")
            print(f"\n⏱️  Tiempo total: {tiempo_total:.1f} segundos")
            print(f"{'='*60}\n")
        
        else:
            print("\n✗ No se extrajo ningún post")
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n" + "=" * 70)
        print("🔒 Cerrando Vivaldi automáticamente...")
        try:
            if proceso_vivaldi:
                proceso_vivaldi.terminate()
                print("✅ Vivaldi cerrado")
        except Exception as e:
            print(f"Error al cerrar Vivaldi: {e}")


# =====================================================
# PUNTO DE ENTRADA
# =====================================================

if __name__ == "__main__":
    import asyncio
    asyncio.run(main(
        posts_por_tema=10,
        temas_buscar=["nicolas muñoz"]
    ))