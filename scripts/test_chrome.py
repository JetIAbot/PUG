"""
Script de diagnóstico para verificar la configuración de Chrome/ChromeDriver
"""
import sys
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def test_chrome_installation():
    """Verificar instalación y configuración de Chrome"""
    print("🔍 DIAGNÓSTICO DE CHROME Y CHROMEDRIVER")
    print("=" * 50)
    
    # Test 1: Chrome básico
    print("1. Probando Chrome básico...")
    try:
        options = Options()
        options.add_argument('--version')
        driver = webdriver.Chrome(options=options)
        print("   ✅ Chrome básico funciona")
        driver.quit()
    except Exception as e:
        print(f"   ❌ Chrome básico falló: {e}")
    
    # Test 2: Chrome con WebDriverManager
    print("\n2. Probando Chrome con WebDriverManager...")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        service = Service(ChromeDriverManager().install())
        options = Options()
        options.add_argument('--headless=new')
        driver = webdriver.Chrome(service=service, options=options)
        print("   ✅ Chrome con WebDriverManager funciona")
        driver.quit()
    except Exception as e:
        print(f"   ❌ Chrome con WebDriverManager falló: {e}")
    
    # Test 3: Chrome sin headless
    print("\n3. Probando Chrome sin headless...")
    try:
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        driver = webdriver.Chrome(options=options)
        print("   ✅ Chrome sin headless funciona")
        
        # Probar navegación básica
        driver.get("https://www.google.com")
        if "Google" in driver.title:
            print("   ✅ Navegación básica funciona")
        
        driver.quit()
    except Exception as e:
        print(f"   ❌ Chrome sin headless falló: {e}")
    
    # Test 4: Conectividad al portal
    print("\n4. Probando conectividad al portal...")
    try:
        import requests
        response = requests.get("https://segreteria.unigre.it/asp/authenticate.asp", timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Portal accesible (Status: {response.status_code})")
        else:
            print(f"   ⚠️  Portal responde pero con status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error conectando al portal: {e}")
    
    # Test 5: Configuración final recomendada
    print("\n5. Probando configuración final recomendada...")
    try:
        options = Options()
        # Configuración mínima estable
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # Usar WebDriverManager si está disponible
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        except:
            driver = webdriver.Chrome(options=options)
        
        # Probar navegación al portal
        driver.get("https://segreteria.unigre.it/asp/authenticate.asp")
        
        if "unigre" in driver.current_url.lower():
            print("   ✅ Configuración final funciona perfectamente")
            print(f"   📄 Título de la página: {driver.title}")
        else:
            print("   ⚠️  Configuración funciona pero página inesperada")
        
        driver.quit()
        
    except Exception as e:
        print(f"   ❌ Configuración final falló: {e}")
    
    print("\n" + "=" * 50)
    print("RECOMENDACIONES:")
    print("- Si todos los tests fallaron: Instalar Chrome")
    print("- Si solo headless falla: Usar HEADLESS_MODE=False")
    print("- Si WebDriverManager falla: Usar Chrome del sistema")
    print("- Si portal no es accesible: Verificar conexión")

if __name__ == "__main__":
    test_chrome_installation()
