# main.py (Versión Refactorizada y Mejorada por Agente)

# Importamos las librerías necesarias
import argparse
import json
import logging
from typing import Dict, List, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
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


def configurar_driver() -> WebDriver:
    """Configura e inicia el navegador Chrome con Selenium en modo headless.
    
    Returns:
        WebDriver: La instancia del driver de Chrome configurado.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # Suprime logs irrelevantes de Selenium en la consola
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        return driver
    except Exception as e:
        logging.error(f"No se pudo inicializar ChromeDriverManager. ¿Hay conexión a internet? Error: {e}")
        raise

def iniciar_sesion(driver: WebDriver, wait: WebDriverWait, usuario: str, contrasena: str):
    """Navega a la página de login, espera a los elementos e inicia sesión.
    
    Args:
        driver: La instancia del driver de Selenium.
        wait: La instancia de WebDriverWait.
        usuario: El nombre de usuario para el login.
        contrasena: La contraseña para el login.
        
    Raises:
        TimeoutException: Si los campos de login no aparecen a tiempo.
        ValueError: Si el login falla (credenciales incorrectas).
    """
    logging.info("Accediendo a la página de login...")
    driver.get(URL_LOGIN)
    
    campo_usuario = wait.until(EC.visibility_of_element_located(LOGIN_USER_FIELD))
    campo_contrasena = driver.find_element(*LOGIN_PASS_FIELD)
    boton_login = driver.find_element(*LOGIN_BUTTON)

    logging.info("Introduciendo credenciales...")
    campo_usuario.send_keys(usuario)
    campo_contrasena.send_keys(contrasena)
    boton_login.click()

    # Verificación de login exitoso: si aparece un mensaje de error, las credenciales son incorrectas.
    try:
        wait.until(EC.visibility_of_element_located(LOGIN_ERROR_MESSAGE))
        raise ValueError("Login fallido. Usuario o contraseña incorrectos.")
    except TimeoutException:
        # Es el comportamiento esperado: no se encontró el mensaje de error, el login fue exitoso.
        logging.info("Login exitoso.")

def navegar_a_horarios(driver: WebDriver, wait: WebDriverWait):
    """Hace clic en el enlace para ir a la página de horarios.
    
    Args:
        driver: La instancia del driver de Selenium.
        wait: La instancia de WebDriverWait.
    """
    logging.info("Navegando a la sección de horarios...")
    link_horario = wait.until(EC.element_to_be_clickable(SCHEDULE_LINK))
    link_horario.click()

def extraer_datos_personales(driver: WebDriver, wait: WebDriverWait) -> Dict[str, str]:
    """Extrae los datos personales del estudiante de la tabla.
    
    Args:
        driver: La instancia del driver de Selenium.
        wait: La instancia de WebDriverWait.
        
    Returns:
        Un diccionario con la matrícula, nombre y apellido.
        
    Raises:
        NoSuchElementException: Si la tabla de datos personales no se encuentra.
        IndexError: Si la estructura de la tabla no es la esperada.
    """
    logging.info("Extrayendo datos personales del estudiante...")
    tabla_datos = wait.until(EC.visibility_of_element_located(PERSONAL_DATA_TABLE))
    html_tabla = tabla_datos.get_attribute('outerHTML')
    soup_tabla = BeautifulSoup(html_tabla, 'html.parser')
    
    filas = soup_tabla.find_all('tr')
    if len(filas) < 2:
        raise IndexError("La tabla de datos personales no tiene la estructura esperada (faltan filas).")
        
    celdas = filas[1].find_all('td')
    if len(celdas) < 3:
        raise IndexError("La tabla de datos personales no tiene la estructura esperada (faltan columnas).")
    
    datos_personales = {
        'matricola': celdas[0].get_text(strip=True),
        'cognome': celdas[1].get_text(strip=True),
        'nome': celdas[2].get_text(strip=True)
    }
    
    logging.info(f"Datos encontrados: Matrícula {datos_personales['matricola']}, {datos_personales['cognome']} {datos_personales['nome']}")
    return datos_personales

def extraer_datos_horario(driver: WebDriver) -> List[Dict[str, str]]:
    """Extrae la información de las tablas de horarios.
    
    Args:
        driver: La instancia del driver de Selenium.
        
    Returns:
        Una lista de diccionarios, donde cada uno representa un bloque de clase.
    """
    logging.info("Extrayendo datos del horario...")
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    horario_final = []
    
    contenedor_principal = soup.find('div', id=SCHEDULE_DIV_CONTAINER[1])
    if not contenedor_principal:
        logging.warning("No se encontró el contenedor principal del horario. Puede que no haya horario publicado.")
        return []

    titulos_semestre = contenedor_principal.find_all('h1')
    for titulo in titulos_semestre:
        nombre_semestre = titulo.get_text(strip=True)
        tabla = titulo.find_next_sibling('table')
        if not tabla: continue

        logging.info(f"--- Procesando: {nombre_semestre} ---")
        filas_cabecera = tabla.find('thead').find_all('tr')
        dias_semana = [th.get_text(strip=True) for th in filas_cabecera[0].find_all('th')[1:]]
        
        filas_horario = tabla.find_all('tr')[1:]
        for fila in filas_horario:
            celdas = fila.find_all(['th', 'td'])
            if not celdas: continue
            
            bloque_horario = celdas[0].get_text(strip=True)
            celdas_clases = celdas[1:]

            for i, celda_clase in enumerate(celdas_clases):
                if celda_clase.get_text(strip=True):
                    clase = {
                        'semestre': nombre_semestre,
                        'dia': dias_semana[i],
                        'bloque_horario': bloque_horario,
                        'info_clase': celda_clase.get_text(separator='\n', strip=True)
                    }
                    horario_final.append(clase)

    logging.info(f"Proceso completado. Se encontraron {len(horario_final)} bloques de clase en total.")
    return horario_final

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