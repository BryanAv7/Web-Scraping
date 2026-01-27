"""
====================================
EXTRACTOR LINKEDIN
====================================
"""

import asyncio
import csv
import random
import logging
import hashlib
from datetime import datetime
from urllib.parse import quote
from playwright.async_api import async_playwright

# --------------------------------------------------
# LOG
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --------------------------------------------------
# NORMALIZACIÓN DE TEXTO
# --------------------------------------------------
def normalizar_texto(texto: str) -> str:
    texto = texto.lower()
    texto = texto.replace("\n", " ")
    texto = " ".join(texto.split())
    return texto


def hash_texto(texto: str) -> str:
    return hashlib.md5(texto.encode("utf-8")).hexdigest()


# --------------------------------------------------
# CLASE PRINCIPAL
# --------------------------------------------------
class ExtractorLinkedInPosts:

    def __init__(self, posts_por_tema=20, temas_buscar=None):
        self.posts_por_tema = posts_por_tema
        self.temas_buscar = temas_buscar or []
        self.datos = []
        self.hashes_vistos = set()   # deduplicación REAL

    async def delay(self, a=1.2, b=2.5):
        await asyncio.sleep(random.uniform(a, b))

    async def scroll_real(self, page):
        await page.evaluate("""
            () => {
                window.scrollBy({
                    top: window.innerHeight * 0.8,
                    left: 0,
                    behavior: 'smooth'
                });
            }
        """)

    async def obtener_posts(self, page):
        selectores = [
            'div[class*="update-components-update-v2"]',
            'div[class*="feed-shared-update-v2"]',
            '[role="article"]',
            'article'
        ]

        for sel in selectores:
            try:
                posts = await page.locator(sel).all()
                if posts:
                    return posts
            except:
                pass

        return []

    async def extraer_posts_por_tema(self, page, tema):
        logger.info("=" * 60)
        logger.info(f"TEMA: {tema}")
        logger.info(f"OBJETIVO: {self.posts_por_tema}")
        logger.info("=" * 60)

        url = f"https://www.linkedin.com/search/results/content/?keywords={quote(tema)}"
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await self.delay(4, 6)

        contador = 0
        intentos_sin_nuevos = 0
        max_intentos = 12

        while contador < self.posts_por_tema:

            posts = await self.obtener_posts(page)
            nuevos = 0

            for post in posts:
                if contador >= self.posts_por_tema:
                    break

                try:
                    texto = await post.text_content(timeout=2000)
                    if not texto:
                        continue

                    texto = texto.strip()
                    if len(texto) < 100:
                        continue

                    texto_norm = normalizar_texto(texto)
                    texto_hash = hash_texto(texto_norm)

                    if texto_hash in self.hashes_vistos:
                        continue

                    self.hashes_vistos.add(texto_hash)

                    registro = {
                        "tema_busqueda": tema,
                        "contenido": texto[:1200],
                        "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "fuente": "LinkedIn"
                    }

                    self.datos.append(registro)
                    contador += 1
                    nuevos += 1

                    logger.info(f"✓ Post {contador}/{self.posts_por_tema}")

                except:
                    pass

            if nuevos == 0:
                intentos_sin_nuevos += 1
                logger.warning(f"Sin nuevos ({intentos_sin_nuevos}/{max_intentos})")
            else:
                intentos_sin_nuevos = 0

            if intentos_sin_nuevos >= max_intentos:
                logger.error("LinkedIn dejó de entregar contenido nuevo.")
                break

            await self.scroll_real(page)
            await self.delay(2, 3)

        logger.info(f"FIN tema '{tema}': {contador} posts reales")
        return contador

    async def ejecutar(self):
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp("http://localhost:9223")
            except:
                logger.error("No se pudo conectar a Edge (9223)")
                return False

            context = browser.contexts[0]
            page = context.pages[0]
            await page.set_viewport_size({"width": 1920, "height": 1080})

            total = 0
            for tema in self.temas_buscar:
                total += await self.extraer_posts_por_tema(page, tema)
                await self.delay(4, 6)

            logger.info(f"TOTAL GENERAL: {total}")
            return True


# --------------------------------------------------
# CSV
# --------------------------------------------------
def guardar_csv(datos, archivo="datos_extraidos/linkedin.csv"):
    if not datos:
        logger.error("No hay datos para guardar.")
        return

    campos = ["tema_busqueda", "contenido", "fecha_extraccion", "fuente"]

    with open(archivo, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(datos)

    logger.info(f"CSV generado: {archivo}")
    logger.info(f"Total registros únicos: {len(datos)}")


# --------------------------------------------------
# MAIN
# --------------------------------------------------
async def main(posts_por_tema=20, temas_buscar=None):
    logger.info("=" * 60)
    logger.info("EXTRACTOR LINKEDIN")
    logger.info("=" * 60)


    posts_por_tema = posts_por_tema * 3
    #logger.info(f"Posts solicitados por el orquestador: {posts_por_tema}")
    #logger.info(f"Posts reales a buscar (x3): {posts_real}")
    
    extractor = ExtractorLinkedInPosts(
        posts_por_tema=posts_por_tema,
        temas_buscar=temas_buscar
    )

    ok = await extractor.ejecutar()

    if ok:
        guardar_csv(extractor.datos)
        logger.info("Proceso finalizado correctamente")
    else:
        logger.error("Proceso falló")


if __name__ == "__main__":
    temas = [
        "nicolas maduro capturado",
    ]

    asyncio.run(
        main(
            posts_por_tema=20,
            temas_buscar=temas
        )
    )
