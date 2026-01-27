"""
test_orquestador.py - Prueba de integración
"""

import asyncio
import webscraping_extractores.extraerFb as fb
import webscraping_extractores.extraerReddit as rd

def test_facebook():
    """Test de Facebook"""
    print("\n" + "="*60)
    print("🔵 TESTEANDO FACEBOOK")
    print("="*60 + "\n")
    
    fb.main(
        temas_buscar=["Precio de las ram 2026"],
        posts_por_tema=3
    )

async def test_reddit():
    """Test de Reddit (async)"""
    print("\n" + "="*60)
    print("🔴 TESTEANDO REDDIT")
    print("="*60 + "\n")
    
    await rd.main(
        temas_buscar=["Precio de las ram 2026"],
        posts_por_tema=3,
        modo_interactivo=False  # False para no pedir ENTER
    )

def main():
    """Orquestador principal"""
    
    # 1. Facebook primero (sync)
    test_facebook()
    
    # 2. Reddit después (async)
    asyncio.run(test_reddit())
    
    print("\n" + "="*60)
    print("✅ TESTS COMPLETADOS")
    print("="*60)

if __name__ == "__main__":
    main()