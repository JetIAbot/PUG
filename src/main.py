# main.py (Versión Refactorizada y Mejorada por Agente)

# Importamos las librerías necesarias
import argparse
import json
import logging
import os
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Importamos las constantes centralizadas. Esta es la única fuente de selectores.
from . import constants

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN DE LOGGING ---
# Reemplazamos print() por un sistema de logging más robusto
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- FUNCIONES DE PROCESAMIENTO PARA PORTAL REAL ---

def procesar_datos_extraidos(datos_portal: dict, matricola: str) -> dict:
    """Procesar datos extraídos del portal real y ejecutar matchmaking"""
    try:
        logger = logging.getLogger('main_processing')
        logger.info(f"Procesando datos extraídos para matrícula: {matricola[:2]}****")
        
        # Importar funciones de matchmaking
        from matchmaking import inicializar_firebase, realizar_matchmaking, guardar_en_firebase
        
        # Inicializar Firebase
        db = inicializar_firebase()
        if not db:
            return {
                'success': False,
                'message': 'Error conectando a Firebase',
                'errors': ['No se pudo conectar a la base de datos']
            }
        
        # Guardar datos del estudiante en Firebase
        datos_estudiante = {
            'perfil': datos_portal.get('perfil', {}),
            'horario': datos_portal.get('horario', []),
            'materias': datos_portal.get('materias', []),
            'calificaciones': datos_portal.get('calificaciones', []),
            'fecha_actualizacion': json.dumps(datetime.now(), default=str)
        }
        
        # Guardar en Firebase
        resultado_guardado = guardar_en_firebase(db, matricola, datos_estudiante)
        if not resultado_guardado['success']:
            return resultado_guardado
        
        # Realizar matchmaking
        resultado_matchmaking = realizar_matchmaking(db, matricola)
        
        return {
            'success': True,
            'message': 'Datos procesados y matchmaking completado',
            'data': {
                'estudiante': datos_estudiante['perfil'],
                'matchmaking': resultado_matchmaking,
                'estadisticas': {
                    'horarios_guardados': len(datos_estudiante['horario']),
                    'materias_encontradas': len(datos_estudiante['materias']),
                    'coincidencias_encontradas': len(resultado_matchmaking.get('coincidencias', []))
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error procesando datos: {e}")
        return {
            'success': False,
            'message': f'Error durante procesamiento: {str(e)}',
            'errors': [str(e)]
        }

# --- FUNCIONES DE EXTRACCIÓN ---

def extraer_datos_personales(driver: webdriver.Chrome) -> Dict[str, str]:
    """
    Busca la tabla de datos personales, la parsea y extrae la información.
    """
    logging.info("Extrayendo datos personales...")
    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located(constants.DATOS_TABLA_INFO_PERSONAL))
        
        tabla_html = driver.find_element(*constants.DATOS_TABLA_INFO_PERSONAL).get_attribute('outerHTML')
        soup = BeautifulSoup(tabla_html, 'html.parser')
        
        fila_datos = soup.find_all('tr')[1]
        celdas = fila_datos.find_all('td')
        
        # CORRECCIÓN 1: Ahora esperamos 4 columnas en lugar de 3.
        if len(celdas) < 4:
            raise IndexError("La tabla de datos personales no tiene la estructura esperada (se esperaban 4 columnas).")
            
        # CORRECCIÓN 2: Añadimos el nuevo campo 'data_nascita' desde la cuarta celda.
        datos = {
            'matricola': celdas[0].get_text(strip=True),
            'cognome': celdas[1].get_text(strip=True),
            'nome': celdas[2].get_text(strip=True),
            'data_nascita': celdas[3].get_text(strip=True)
        }
        logging.info(f"Datos personales extraídos: {datos['matricola']}, Nacimiento: {datos['data_nascita']}")
        return datos
        
    except Exception as e:
        logging.error(f"No se pudieron extraer los datos personales: {e}")
        raise ValueError("La tabla de datos personales no se encontró o tiene un formato inesperado.")

def extraer_datos_horario(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    """
    Busca el contenedor del horario, lo parsea y extrae todas las clases.
    """
    logging.info("Extrayendo datos del horario...")
    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located(constants.HORARIO_CONTENEDOR_PRINCIPAL))
        
        contenedor_html = driver.find_element(*constants.HORARIO_CONTENEDOR_PRINCIPAL).get_attribute('outerHTML')
        soup = BeautifulSoup(contenedor_html, 'html.parser')
        
        horario_final = []
        dias_semana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
        
        tablas_horario = soup.find_all('table')
        if not tablas_horario:
            logging.warning("No se encontraron tablas de horario en la página.")
            return []

        for tabla in tablas_horario:
            filas = tabla.find_all('tr')
            if not filas: continue

            # Itera sobre las filas de datos (saltando el encabezado de los días)
            for fila in filas[1:]:
                celdas = fila.find_all(['th', 'td'])
                if not celdas: continue
                
                # La primera celda es la hora (ej: 'I', 'II', etc.)
                bloque_horario = celdas[0].get_text(strip=True)
                
                # Itera sobre las celdas de las clases (saltando la celda de la hora)
                for i, celda_clase in enumerate(celdas[1:]):
                    info_clase = celda_clase.get_text(strip=True)
                    # Si la celda no está vacía, hemos encontrado una clase
                    if info_clase:
                        horario_final.append({
                            "dia": dias_semana[i],
                            "hora": bloque_horario,
                            "info_clase": info_clase
                        })
        
        logging.info(f"Se encontraron {len(horario_final)} bloques de clase.")
        return horario_final

    except Exception as e:
        logging.error(f"No se pudieron extraer los datos del horario: {e}")
        raise ValueError("El contenedor del horario no se encontró o tiene un formato inesperado.")

# --- FUNCIÓN PRINCIPAL DE SCRAPING ---

def realizar_scraping(usuario: str, contrasena: str) -> Dict:
    """
    Flujo completo y unificado de scraping: login, extracción de datos y navegación.
    Esta es la única función que la aplicación (vía Celery) debe llamar.
    """
    # --- RE-ADAPTACIÓN PARA WINDOWS ---
    # Eliminamos las opciones específicas de Linux (--no-sandbox, etc.).
    # Dejamos la opción --headless comentada por si quieres hacer pruebas sin ver el navegador.
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") 
    
    # Usamos webdriver-manager para gestionar automáticamente el chromedriver.exe en Windows.
    # Esto evita tener que descargar el driver manualmente.
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    wait = WebDriverWait(driver, 15)

    try:
        logging.info(f"Accediendo al portal: {constants.URL_PORTAL_UNIVERSIDAD}")
        driver.get(constants.URL_PORTAL_UNIVERSIDAD)

        # --- Login ---
        wait.until(EC.visibility_of_element_located(constants.LOGIN_CAMPO_USUARIO)).send_keys(usuario)
        wait.until(EC.visibility_of_element_located(constants.LOGIN_CAMPO_CONTRASENA)).send_keys(contrasena)
        wait.until(EC.element_to_be_clickable(constants.LOGIN_BOTON_ENTRAR)).click()

        # --- Verificación Post-Login ---
        try:
            error_wait = WebDriverWait(driver, 5)
            error_wait.until(EC.visibility_of_element_located(constants.LOGIN_ERROR_MESSAGE))
            raise ValueError("Credenciales incorrectas. Por favor, verifica tu usuario y contraseña.")
        except TimeoutException:
            logging.info("No se encontró mensaje de error, verificando login exitoso...")
            pass

        wait.until(EC.visibility_of_element_located(constants.POST_LOGIN_ELEMENTO_BIENVENIDA))
        logging.info("Login exitoso.")

        # --- Extracción de Datos ---
        datos_personales = extraer_datos_personales(driver)
        
        logging.info("Navegando a la página del horario...")
        wait.until(EC.element_to_be_clickable(constants.NAV_LINK_HORARIO)).click()
        
        # CORRECCIÓN: El nombre correcto de la función es 'extraer_datos_horario'.
        horario = extraer_datos_horario(driver)

        return {"datos_personales": datos_personales, "horario": horario}

    except Exception as e:
        logging.error(f"Error durante el proceso de scraping: {e}")
        driver.save_screenshot('error_screenshot.png')
        raise e
    finally:
        driver.quit()

def extraer_horario(driver: WebDriver) -> List[Dict[str, any]]:
    """
    Extrae los horarios de las tablas de ambos semestres.
    Está diseñado para manejar correctamente celdas vacías y tablas inexistentes.
    """
    logging.info("Iniciando extracción de horarios...")
    horario_completo = []
    
    # Mapeo de selectores de tabla a número de semestre
    tablas_semestres = {
        1: constants.HORARIO_TABLA_SEMESTRE_1,
        2: constants.HORARIO_TABLA_SEMESTRE_2
    }

    for semestre, selector_tabla in tablas_semestres.items():
        try:
            logging.info(f"Buscando tabla para el semestre {semestre}...")
            # Espera a que la tabla esté presente, pero con un tiempo de espera corto.
            # Si no la encuentra, no es un error, simplemente no hay tabla.
            WebDriverWait(driver, 5).until(EC.presence_of_element_located(selector_tabla))
            tabla_html = driver.find_element(*selector_tabla).get_attribute('outerHTML')
            soup = BeautifulSoup(tabla_html, 'html.parser')
            
            filas = soup.find_all('tr')
            
            # La primera fila contiene los nombres de los días, la omitimos (índice 0)
            if len(filas) < 2:
                logging.warning(f"La tabla del semestre {semestre} no contiene filas de datos.")
                continue

            # La segunda fila (índice 1) contiene las horas, la extraemos
            horas_columnas = [th.get_text(strip=True) for th in filas[1].find_all('th') if th.get_text(strip=True)]

            # Iteramos sobre el resto de las filas (a partir del índice 2), que son los días
            for fila in filas[2:]:
                celdas = fila.find_all('td')
                # La primera celda es el nombre del día
                dia_semana = celdas[0].get_text(strip=True)
                
                # Iteramos sobre las celdas de las clases (a partir del índice 1)
                for i, celda_clase in enumerate(celdas[1:]):
                    # MANEJO DE CELDAS VACÍAS: Si la celda no tiene texto, la ignoramos.
                    materia = celda_clase.get_text(strip=True)
                    if materia:
                        # CORRECCIÓN DE INDEXACIÓN: Asegurarse de que el índice 'i' es válido.
                        if i < len(horas_columnas):
                            horario_completo.append({
                                "semestre": semestre,
                                "dia": dia_semana,
                                "hora": horas_columnas[i],
                                "materia": materia
                            })
                            logging.info(f"Clase encontrada: Sem {semestre}, {dia_semana} a las {horas_columnas[i]} - {materia}")
                        else:
                            logging.warning(f"Se encontró una materia ('{materia}') pero no hay una columna de hora correspondiente en el índice {i}. Se omitirá.")

        except TimeoutException:
            # Esto es normal si la universidad aún no ha publicado la tabla para un semestre.
            logging.info(f"No se encontró la tabla de horarios para el semestre {semestre}. Se omitirá.")
        except Exception as e:
            logging.error(f"Ocurrió un error inesperado al procesar el semestre {semestre}: {e}")

    return horario_completo

# CORRECCIÓN 2: Se ha simplificado drásticamente esta función para eliminar el error.
def run_scraping_task(usuario: str, contrasena: str) -> str:
    """
    Función principal que orquesta todo el proceso de scraping.
    Llama a la función de scraping y devuelve el resultado en formato JSON.
    """
    try:
        # Llama a la función principal que hace todo el trabajo y devuelve el resultado.
        resultado_completo = realizar_scraping(usuario, contrasena)
        
        # Convierte el diccionario de resultado a una cadena JSON.
        return json.dumps(resultado_completo, indent=4)
    
    except Exception as e:
        # En caso de cualquier error durante el scraping, retorna un JSON de error.
        logging.error(f"La tarea de scraping falló con el error: {e}")
        return json.dumps({"error": str(e)})
    
# --- PUNTO DE ENTRADA PARA PRUEBAS LOCALES ---
if __name__ == '__main__':
    """
    Permite ejecutar el script desde la línea de comandos para pruebas rápidas,
    usando la misma lógica que la aplicación web.
    Ejemplo: python -m src.main --usuario TU_USUARIO --contrasena TU_CONTRASENA
    """
    parser = argparse.ArgumentParser(description="Extrae el horario de un estudiante.")
    parser.add_argument('--usuario', required=True, help='Usuario del portal.')
    parser.add_argument('--contrasena', required=True, help='Contraseña del portal.')
    args = parser.parse_args()

    try:
        resultado = realizar_scraping(args.usuario, args.contrasena)
        print(json.dumps(resultado, indent=4))
    except Exception as e:
        # Imprime un JSON de error si el scraping falla
        print(json.dumps({"error": str(e)}))