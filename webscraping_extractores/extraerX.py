"""
====================================
EXTRACTOR DE POSTS TWITTER/X
SOLO POSTS + COMENTARIOS – CONTROLADO POR ORQUESTADOR
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

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Palabras clave estrictas 
PALABRAS_CLAVE = [
    "maduro",
    "capturado",
    "arrestado",
    "detenido",
    "preso",
    "eeuu",
    "estados unidos",
    "dea",
    "militar",
    "urgente",
    "última hora",
]

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
                    texto_lower = contenido.lower()

                    if not any(p in texto_lower for p in PALABRAS_CLAVE):
                        continue

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
            try:
                browser = await p.chromium.connect_over_cdp("http://localhost:9222")
                logger.info("OK Conectado a Brave")
            except:
                logger.error("No se pudo conectar a Brave en puerto 9222")
                return False

            pages = browser.contexts[0].pages
            if not pages:
                logger.error("No hay pestañas abiertas en Brave")
                return False

            page = pages[0]
            await page.set_viewport_size({"width": 1920, "height": 1080})

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
        logger.error("No hay datos para guardar")
        return False

    with open(archivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["tipo", "autor", "contenido", "tema_busqueda", "fecha_extraccion", "post_padre"],
            quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        writer.writerows(datos)

    logger.info("=" * 70)
    logger.info("CSV generado correctamente")
    logger.info(f"Archivo: {archivo}")
    logger.info(f"Total registros: {len(datos)}")
    logger.info("=" * 70)
    return True

# ================================
# MAIN CONTROLADO POR ORQUESTADOR
# ================================
async def main(posts_por_tema, temas_buscar):
    extractor = ExtractorTwitterPosts(
        posts_por_tema=posts_por_tema,
        temas_buscar=temas_buscar
    )

    ok = await extractor.ejecutar()
    if ok and extractor.datos:
        guardar_csv(extractor.datos)
    else:
        logger.error("No se pudo completar la extracción")
