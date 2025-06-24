# main.py (Versión Refactorizada y Mejorada)

# Importamos las librerías necesarias
import os
import firebase_admin
from firebase_admin import credentials, firestore
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# --- CONSTANTES DE CONFIGURACIÓN Y LOCALIZADORES ---
# Mover los localizadores aquí hace que el código sea más fácil de mantener.
URL_LOGIN = "https://segreteria.unigre.it/asp/authenticate.asp"
USUARIO = os.getenv("USUARIO_UNIGRE")
CONTRASENA = os.getenv("CONTRASENA_UNIGRE")
FIREBASE_CREDS_PATH = "credenciales.json"

# Localizadores de Selenium
LOGIN_USER_FIELD = (By.NAME, 'txtName')
LOGIN_PASS_FIELD = (By.NAME, 'txtPassword')
LOGIN_BUTTON = (By.CLASS_NAME, 'verdanaCorpo12B_2')
SCHEDULE_LINK = (By.LINK_TEXT, 'Orario Settimanale')
PERSONAL_DATA_TABLE = (By.ID, 'GridView1')
SCHEDULE_DIV_CONTAINER = (By.ID, 'orario1sem')
# XPath para esperar a que cualquier celda del horario tenga texto
SCHEDULE_DATA_CELL = (By.XPATH, "//div[@id='orario1sem']//td[normalize-space(.)]")


def configurar_driver() -> WebDriver:
    """Configura e inicia el navegador Chrome con Selenium en modo headless."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# --- MEJORA: Las funciones ahora son más limpias, sin time.sleep() ---
def iniciar_sesion(driver: WebDriver, wait: WebDriverWait, usuario: str, contrasena: str):
    """Navega a la página de login, espera a los elementos e inicia sesión."""
    print("Accediendo a la página de login...")
    driver.get(URL_LOGIN)
    
    # Espera a que el campo de usuario sea visible antes de interactuar
    campo_usuario = wait.until(EC.visibility_of_element_located(LOGIN_USER_FIELD))
    campo_contrasena = driver.find_element(*LOGIN_PASS_FIELD) # El asterisco desempaqueta la tupla
    boton_login = driver.find_element(*LOGIN_BUTTON)

    print("Introduciendo credenciales...")
    campo_usuario.send_keys(usuario)
    campo_contrasena.send_keys(contrasena)
    
    print("Haciendo clic en el botón de login...")
    boton_login.click()

def navegar_a_horarios(driver: WebDriver):
    """Hace clic en el enlace para ir a la página de horarios."""
    # Esta función ahora es más simple, solo hace clic. La espera se maneja fuera.
    print("Navegando a la sección de horarios...")
    driver.find_element(*SCHEDULE_LINK).click()

def extraer_datos_personales(driver: WebDriver) -> Optional[Dict[str, str]]:
    """Extrae los datos personales del estudiante de la tabla GridView1."""
    print("Extrayendo datos personales del estudiante...")
    try:
        tabla_datos = driver.find_element(*PERSONAL_DATA_TABLE)
        html_tabla = tabla_datos.get_attribute('outerHTML')
        soup_tabla = BeautifulSoup(html_tabla, 'html.parser')
        
        fila_datos = soup_tabla.find_all('tr')[1]
        celdas = fila_datos.find_all('td')
        
        datos_personales = {
            'matricola': celdas[0].get_text(strip=True),
            'cognome': celdas[1].get_text(strip=True),
            'nome': celdas[2].get_text(strip=True)
        }
        
        print(f"Datos encontrados: Matrícula {datos_personales['matricola']}, {datos_personales['cognome']} {datos_personales['nome']}")
        return datos_personales
    except Exception as e:
        print(f"Error al extraer los datos personales: {e}")
        return None

def extraer_datos_horario(driver: WebDriver) -> List[Dict[str, str]]:
    """Extrae la información de las tablas de horarios en formato calendario."""
    print("Extrayendo datos del horario...")
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    horario_final = []
    
    contenedor_principal = soup.find('div', id=SCHEDULE_DIV_CONTAINER[1])
    if not contenedor_principal:
        print("Advertencia: No se encontró el contenedor principal del horario.")
        return []

    titulos_semestre = contenedor_principal.find_all('h1')
    for titulo in titulos_semestre:
        nombre_semestre = titulo.get_text(strip=True)
        tabla = titulo.find_next_sibling('table')
        if not tabla: continue

        print(f"--- Procesando: {nombre_semestre} ---")
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

    print(f"Proceso completado. Se encontraron {len(horario_final)} bloques de clase en total.")
    return horario_final

def actualizar_estudiante_y_horario_en_firestore(db: firestore.client, datos_personales: Dict[str, str], horario_data: List[Dict[str, str]]):
    """Crea/actualiza los datos de un estudiante y su horario en Firestore."""
    matricola = datos_personales['matricola']
    print(f"Actualizando perfil del estudiante con matrícula '{matricola}' en Firestore...")

    estudiante_ref = db.collection('estudiantes').document(matricola)
    perfil_data = {'cognome': datos_personales['cognome'], 'nome': datos_personales['nome']}
    estudiante_ref.set(perfil_data, merge=True)
    print("Datos del perfil (nombre, apellido) guardados/actualizados.")

    if horario_data:
        print("Horario con datos detectado. Procediendo a guardarlo...")
        horario_ref = estudiante_ref.collection('horario')
        for doc in horario_ref.stream():
            doc.reference.delete()
        for clase in horario_data:
            horario_ref.add(clase)
        print(f"¡Horario guardado con éxito para la matrícula '{matricola}'!")
    else:
        print("El horario extraído está vacío. No se realizarán cambios en el horario de Firestore.")


# --- FLUJO PRINCIPAL DE EJECUCIÓN ---
if __name__ == '__main__':
    print("Iniciando script de PUG...")
    # 1. INICIALIZACIÓN DE SERVICIOS
    cred = credentials.Certificate(FIREBASE_CREDS_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    driver = configurar_driver()
    # MEJORA: Definimos un solo WebDriverWait para reutilizarlo
    wait = WebDriverWait(driver, 20) # Aumentamos a 20 segundos para más robustez

    try:
        # 2. LOGIN Y NAVEGACIÓN
        iniciar_sesion(driver, wait, USUARIO, CONTRASENA)
        
        # MEJORA: Esperamos explícitamente al enlace del horario después del login
        print("Login exitoso, esperando a la página de bienvenida...")
        wait.until(EC.visibility_of_element_located(SCHEDULE_LINK))
        
        navegar_a_horarios(driver)
        
        # MEJORA: Esperamos explícitamente a la tabla de datos personales
        print("Página de horarios cargada, esperando datos personales...")
        wait.until(EC.visibility_of_element_located(PERSONAL_DATA_TABLE))
        
        # 3. EXTRACCIÓN DE DATOS
        datos_personales = extraer_datos_personales(driver)
        if not datos_personales:
            raise Exception("No se pudieron obtener los datos personales, el script no puede continuar.")

        try:
            # Intentamos esperar por los datos del horario, pero no fallamos si no aparecen
            wait.until(EC.presence_of_element_located(SCHEDULE_DATA_CELL))
        except Exception:
            print("No se encontraron datos en la tabla de horarios (esperado durante las vacaciones).")
        
        horario_extraido = extraer_datos_horario(driver)
        
        # 4. GUARDAR EN FIREBASE
        actualizar_estudiante_y_horario_en_firestore(db, datos_personales, horario_extraido)

    except Exception as e:
        print(f"\nOcurrió un error general en el script: {e}")
        driver.save_screenshot('error_screenshot.png')
        print("Se ha guardado una captura de pantalla del error como 'error_screenshot.png'.")

    finally:
        print("\nCerrando el navegador.")
        driver.quit()