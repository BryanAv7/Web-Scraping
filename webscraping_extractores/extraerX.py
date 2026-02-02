"""
====================================
EXTRACTOR DE POSTS TWITTER/X
SOLO POSTS + COMENTARIOS – CONTROLADO POR ORQUESTADOR
CON APERTURA AUTOMÁTICA DE BRAVE
====================================
"""

import asyncio
from playwright.async_api import async_playwright
import csv
import random
import logging
from datetime import datetime
from urllib.parse import quote
import hashlib
import subprocess
import time
import os

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)



# ================================
# Configuración de Brave
# ================================
BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
DEBUG_PORT = 9222

# ================================
# Función para abrir Brave con debugging
# ================================
def abrir_brave_con_debugging():
    """
    Abre Brave con remote debugging habilitado en el puerto 9222
    """
    logger.info("=" * 70)
    logger.info("Iniciando Brave con modo de depuración remota...")
    logger.info(f"Puerto: {DEBUG_PORT}")
    logger.info("=" * 70)
    
    # Verificar que Brave existe
    if not os.path.exists(BRAVE_PATH):
        logger.error(f"❌ No se encontró Brave en: {BRAVE_PATH}")
        logger.error("Por favor, verifica la ruta de instalación")
        return None
    
    # Comando para abrir Brave
    cmd = [
        BRAVE_PATH,
        f"--remote-debugging-port={DEBUG_PORT}",
        "https://x.com"  # Abrir directamente en X
    ]
    
    try:
        # Iniciar proceso de Brave
        proceso = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logger.info("✅ Brave iniciado correctamente")
        logger.info("⏳ Esperando a que el navegador esté listo...")
        time.sleep(5)  # Dar tiempo para que Brave se inicie completamente
        
        return proceso
        
    except Exception as e:
        logger.error(f"❌ Error al iniciar Brave: {e}")
        return None

# ================================
# Función para generar ID corto del post
# ================================
def generar_id_post(texto):
    return hashlib.md5(texto.encode("utf-8")).hexdigest()[:10]

class ExtractorTwitterPosts:

    def __init__(self, posts_por_tema, temas_buscar):
        self.posts_por_tema = posts_por_tema
        self.temas_buscar = temas_buscar
        self.datos = []

    async def delay_humano(self, a=1.0, b=2.5):
        await asyncio.sleep(random.uniform(a, b))

    async def scroll_humano(self, page):
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        await self.delay_humano(2, 4)

    # ================================
    # Extraer comentarios del post abierto
    # ================================
    async def extraer_comentarios(self, page, tema, post_id, limite=10):
        comentarios = []
        contador = 0

        try:
            await page.wait_for_selector('[data-testid="tweet"]', timeout=15000)
        except:
            logger.warning("   No se detectaron comentarios")
            return comentarios

        tweets = await page.locator('[data-testid="tweet"]').all()

        for tweet in tweets[1:]:  # el primero es el post original
            if contador >= limite:
                break

            try:
                contenido = ""
                tweet_text = tweet.locator('[data-testid="tweetText"]')
                if await tweet_text.count() > 0:
                    contenido = await tweet_text.first.inner_text()

                if not contenido or len(contenido.strip()) < 10:
                    continue

                contenido = " ".join(contenido.replace("\n", " ").replace("\r", " ").split()).strip()

                autor = "Desconocido"
                try:
                    user_link = tweet.locator('a[href^="/"]').first
                    href = await user_link.get_attribute("href")
                    if href:
                        autor = href.replace("/", "")
                except:
                    pass

                comentarios.append({
                    "tipo": "COMENTARIO",
                    "autor": autor,
                    "contenido": contenido[:500],
                    "tema_busqueda": tema,
                    "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "post_padre": post_id
                })

                contador += 1

            except:
                continue

        logger.info(f"      Comentarios extraídos: {contador}")
        return comentarios

    # ================================
    # Extraer posts por tema
    # ================================
    async def extraer_posts_por_tema(self, page, tema):
        logger.info(f"[BUSCANDO] {tema}")
        logger.info(f"   Objetivo: {self.posts_por_tema} posts")

        tema_encoded = quote(tema)
        url = f"https://x.com/search?q={tema_encoded}&f=top"

        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await self.delay_humano(3, 5)

        try:
            await page.wait_for_selector('[data-testid="tweet"]', timeout=15000)
        except:
            logger.warning("   No se detectó selector principal de tweets")

        contador = 0
        textos_procesados = set()
        intentos_scroll = 0
        MAX_INTENTOS_SCROLL = 25

        while contador < self.posts_por_tema and intentos_scroll < MAX_INTENTOS_SCROLL:
            intentos_scroll += 1
            logger.info(f"   Intento de carga #{intentos_scroll}")

            await self.scroll_humano(page)
            articles = await page.locator('[data-testid="tweet"]').all()
            logger.info(f"   Tweets visibles: {len(articles)}")

            for article in articles:
                if contador >= self.posts_por_tema:
                    break

                try:
                    # ===== TEXTO REAL DEL POST =====
                    tweet_text = article.locator('[data-testid="tweetText"]')
                    contenido = ""
                    if await tweet_text.count() > 0:
                        contenido = await tweet_text.first.inner_text()

                    if not contenido or len(contenido.strip()) < 20:
                        continue

                    contenido = " ".join(contenido.replace("\n", " ").replace("\r", " ").split()).strip()

                    if contenido in textos_procesados:
                        continue
                    textos_procesados.add(contenido)

                    # ===== AUTOR =====
                    autor = "Desconocido"
                    try:
                        user_link = article.locator('a[href^="/"]').first
                        href = await user_link.get_attribute("href")
                        if href:
                            autor = href.replace("/", "")
                    except:
                        pass

                    post_id = generar_id_post(contenido)

                    # Guardar POST
                    self.datos.append({
                        "tipo": "POST",
                        "autor": autor,
                        "contenido": contenido[:500],
                        "tema_busqueda": tema,
                        "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "post_padre": post_id
                    })

                    contador += 1
                    logger.info(f"   OK {contador}/{self.posts_por_tema}. {contenido[:70]}...")
                    await self.delay_humano(0.3, 0.6)

                    # ===== CLICK AL TEXTO DEL POST PARA COMENTARIOS =====
                    if await tweet_text.count() > 0:
                        await tweet_text.first.click()
                        await self.delay_humano(2, 4)

                        comentarios = await self.extraer_comentarios(page, tema, post_id, limite=10)
                        self.datos.extend(comentarios)

                        await page.go_back()
                        await self.delay_humano(2, 4)

                except:
                    continue

        if contador < self.posts_por_tema:
            logger.warning(f"⚠️ No se alcanzó la cuota completa: {contador}/{self.posts_por_tema}. X no cargó más resultados.")
        else:
            logger.info(f"✅ Cuota completada: {contador}/{self.posts_por_tema}")

        logger.info(f"   Total extraído para '{tema}': {contador}\n")
        return contador

    # ================================
    # EJECUTAR EXTRACTOR
    # ================================
    async def ejecutar(self):
        logger.info("=" * 70)
        logger.info("Extractor Twitter/X iniciado")
        logger.info(f"Posts por tema: {self.posts_por_tema}")
        logger.info(f"Temas: {len(self.temas_buscar)}")
        logger.info("=" * 70)

        async with async_playwright() as p:
            max_intentos = 5
            intentos = 0
            browser = None
            
            while intentos < max_intentos and browser is None:
                try:
                    intentos += 1
                    logger.info(f"Intento de conexión #{intentos}...")
                    browser = await p.chromium.connect_over_cdp(f"http://localhost:{DEBUG_PORT}")
                    logger.info("✅ Conectado a Brave")
                except Exception as e:
                    if intentos < max_intentos:
                        logger.warning(f"⏳ Esperando conexión... ({intentos}/{max_intentos})")
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"❌ No se pudo conectar a Brave después de {max_intentos} intentos")
                        logger.error(f"Error: {e}")
                        return False

            pages = browser.contexts[0].pages
            if not pages:
                logger.error("❌ No hay pestañas abiertas en Brave")
                return False

            page = pages[0]
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Asegurarse de que estamos en X
            current_url = page.url
            if "x.com" not in current_url and "twitter.com" not in current_url:
                logger.info("📍 Navegando a X...")
                await page.goto("https://x.com", wait_until="domcontentloaded")
                await self.delay_humano(3, 5)

            total = 0
            for idx, tema in enumerate(self.temas_buscar, 1):
                logger.info("=" * 70)
                logger.info(f"TEMA {idx}/{len(self.temas_buscar)} → {tema}")
                logger.info("=" * 70)
                total += await self.extraer_posts_por_tema(page, tema)
                await self.delay_humano(5, 8)

            return total > 0

# ================================
# GUARDAR CSV
# ================================
def guardar_csv(datos, archivo="datos_extraidos/X.csv"):
    if not datos:
        logger.error("❌ No hay datos para guardar")
        return False

    # Crear directorio si no existe
    os.makedirs(os.path.dirname(archivo), exist_ok=True)

    with open(archivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["tipo", "autor", "contenido", "tema_busqueda", "fecha_extraccion", "post_padre"],
            quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerows(datos)

    logger.info("=" * 70)
    logger.info("✅ CSV generado correctamente")
    logger.info(f"📁 Archivo: {archivo}")
    logger.info(f"📊 Total registros: {len(datos)}")
    logger.info("=" * 70)
    return True

# ================================
# MAIN CONTROLADO POR ORQUESTADOR
# ================================
async def main(posts_por_tema, temas_buscar):
    # 1. Abrir Brave con debugging
    proceso_brave = abrir_brave_con_debugging()
    
    if proceso_brave is None:
        logger.error("❌ No se pudo iniciar Brave. Abortando...")
        return
    
    try:
        # 2. Ejecutar extractor
        extractor = ExtractorTwitterPosts(
            posts_por_tema=posts_por_tema,
            temas_buscar=temas_buscar
        )

        ok = await extractor.ejecutar()
        
        # 3. Guardar resultados
        if ok and extractor.datos:
            guardar_csv(extractor.datos)
        else:
            logger.error("❌ No se pudo completar la extracción")
    
    finally:
        logger.info("\n" + "=" * 70)
        logger.info("🔒 Cerrando Brave automáticamente...")
        try:
            if proceso_brave:
                proceso_brave.terminate()
                logger.info("✅ Brave cerrado")
        except Exception as e:
            logger.error(f"Error al cerrar Brave: {e}")


# ================================
# Punto de entrada si se ejecuta directamente
# ================================
if __name__ == "__main__":
    # Ejemplo de uso
    asyncio.run(main(
        posts_por_tema=10,
        temas_buscar=["nicolas muñoz"]
    ))