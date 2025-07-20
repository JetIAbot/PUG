# main.py (Versión Refactorizada y Mejorada por Agente)

# Importamos las librerías necesarias
import argparse
import json
import logging
from typing import Dict, List, Optional
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN DE LOGGING ---
# Reemplazamos print() por un sistema de logging más robusto
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONSTANTES DE CONFIGURACIÓN Y LOCALIZADORES ---
URL_LOGIN = "https://segreteria.unigre.it/asp/authenticate.asp"

# Localizadores de Selenium
LOGIN_USER_FIELD = (By.NAME, 'txtName')
LOGIN_PASS_FIELD = (By.NAME, 'txtPassword')
LOGIN_BUTTON = (By.CLASS_NAME, 'verdanaCorpo12B_2')
LOGIN_ERROR_MESSAGE = (By.XPATH, "//font[contains(text(), 'errato')]") # Para detectar login fallido
SCHEDULE_LINK = (By.LINK_TEXT, 'Orario Settimanale')
PERSONAL_DATA_TABLE = (By.ID, 'GridView1')
SCHEDULE_DIV_CONTAINER = (By.ID, 'orario1sem')


def realizar_scraping(usuario, contrasena):
    """
    Realiza el web scraping en el portal de la universidad.
    Devuelve un diccionario con los datos o lanza una excepción si falla.
    """
    URL_PORTAL = "https://segreteria.unigre.it/asp/authenticate.asp" # Asegúrate de que esta es la URL que ya verificaste

    options = webdriver.ChromeOptions()
    
    # --- CAMBIO DE DEPURACIÓN: COMENTA LA LÍNEA HEADLESS ---
    # options.add_argument("--headless") 
    # ----------------------------------------------------

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    
    try:
        # --- PRUEBA DE CONTROL ---
        print("PASO DE DEPURACIÓN: Intentando acceder a https://www.google.com")
        driver.get("https://www.google.com")
        time.sleep(2) # Espera 2 segundos para que veas la página
        print("PASO DE DEPURACIÓN: Acceso a Google exitoso.")
        # -------------------------

        print(f"PASO DE DEPURACIÓN: Intentando acceder a {URL_PORTAL}")
        driver.get(URL_PORTAL)
        print("PASO DE DEPURACIÓN: Acceso al portal exitoso.")

        # Lógica de login
        driver.find_element(By.ID, "mat").send_keys(usuario)
        driver.find_element(By.ID, "pin").send_keys(contrasena)
        driver.find_element(By.ID, "login").click()
        
        WebDriverWait(driver, 10).until(EC.url_contains("home.aspx"))

        # Verificar si el login fue exitoso
        if "login.aspx" in driver.current_url:
            raise ValueError("Credenciales de usuario incorrectas o login fallido.")

        # Extraer datos personales
        driver.get("https://www.issrapug.it/ssp/dati_anagrafici.aspx")
        time.sleep(2)
        
        nome = driver.find_element(By.ID, "nome").get_attribute('value')
        cognome = driver.find_element(By.ID, "cognome").get_attribute('value')
        
        datos_personales = {
            "matricola": usuario,
            "nome": nome,
            "cognome": cognome
        }

        # Extraer horario
        driver.get("https://www.issrapug.it/ssp/orario.aspx")
        time.sleep(2)
        
        horario = []
        try:
            tabla_horario = driver.find_element(By.ID, "orario")
            filas = tabla_horario.find_elements(By.TAG_NAME, "tr")[1:]
            for fila in filas:
                celdas = fila.find_elements(By.TAG_NAME, "td")
                if len(celdas) == 3:
                    horario.append({
                        "dia": celdas[0].text,
                        "bloque_horario": celdas[1].text,
                        "info_clase": celdas[2].text
                    })
        except:
            # Es normal no encontrar la tabla si no hay horario publicado
            pass

        return {
            "datos_personales": datos_personales,
            "horario": horario,
            "error": None
        }
    except Exception as e:
        print(f"ERROR DETALLADO EN SCRAPING: {e}")
        raise e
    finally:
        print("PASO DE DEPURACIÓN: Cerrando el driver de Selenium.")
        time.sleep(5) # Pausa de 5 segundos para que puedas ver la ventana final antes de que se cierre
        driver.quit()

# --- FLUJO PRINCIPAL DE EJECUCIÓN ---
def main():
    """Función principal que orquesta el proceso de scraping."""
    parser = argparse.ArgumentParser(description="Extrae el horario de un estudiante de la PUG.")
    parser.add_argument('--usuario', required=True, help='Usuario del portal de la universidad.')
    parser.add_argument('--contrasena', required=True, help='Contraseña del portal.')
    args = parser.parse_args()

    driver = None
    datos_finales = {}

    try:
        driver = configurar_driver()
        wait = WebDriverWait(driver, 15) # Reducido a 15s, suficiente para la mayoría de casos
        
        iniciar_sesion(driver, wait, args.usuario, args.contrasena)
        navegar_a_horarios(driver, wait)
        
        datos_personales = extraer_datos_personales(driver, wait)
        horario_extraido = extraer_datos_horario(driver)
        
        datos_finales = {
            "datos_personales": datos_personales,
            "horario": horario_extraido
        }

    except (TimeoutException, NoSuchElementException) as e:
        error_msg = f"No se pudo encontrar un elemento en la página. Puede que la web haya cambiado o esté en mantenimiento. Detalles: {e.__class__.__name__}"
        logging.error(error_msg)
        datos_finales["error"] = error_msg
    except ValueError as e: # Captura el error de login incorrecto
        logging.error(str(e))
        datos_finales["error"] = str(e)
    except Exception as e:
        error_msg = f"Ha ocurrido un error inesperado: {e.__class__.__name__} - {e}"
        logging.error(error_msg)
        datos_finales["error"] = error_msg
    finally:
        if driver:
            driver.quit()
        # Imprimimos el resultado final como un string JSON para que Flask lo capture.
        print(json.dumps(datos_finales, indent=4))

if __name__ == '__main__':
    main()