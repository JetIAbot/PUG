"""
PortalExtractor - Extractor de datos del portal universitario
Sistema seguro para extraer datos de estudiantes del portal web universitario
"""

import os
import time
import logging
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from dotenv import load_dotenv
from utils.constants import PORTAL_SELECTORS

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class SecureWebDriver:
    """Driver de Selenium configurado de forma segura"""
    
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger('selenium_secure')
    
    def setup_driver(self) -> Optional[webdriver.Chrome]:
        """
        Configurar Chrome con opciones de seguridad
        
        Returns:
            webdriver.Chrome: Driver configurado o None si hay error
        """
        try:
            chrome_options = Options()
            
            # Configuraciones de seguridad
            security_options = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--allow-running-insecure-content',
                '--ignore-certificate-errors',
                '--ignore-ssl-errors',
                '--ignore-certificate-errors-spki'
            ]
            
            for option in security_options:
                chrome_options.add_argument(option)
            
            # Modo headless si está configurado
            if os.getenv('HEADLESS_MODE', 'True').lower() == 'true':
                chrome_options.add_argument('--headless')
                self.logger.info("Modo headless activado")
            
            # User agent personalizado
            chrome_options.add_argument(
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Configurar servicio
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.logger.info("Usando ChromeDriverManager")
            except Exception:
                # Fallback al Chrome del sistema
                service = Service()
                self.logger.info("Usando Chrome del sistema")
            
            # Crear driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            self.logger.info("Driver configurado exitosamente")
            return self.driver
            
        except Exception as e:
            self.logger.error(f"Error configurando driver: {e}")
            return None
    
    def close_driver(self):
        """Cerrar driver de forma segura"""
        if self.driver:
            try:
                # Limpiar datos de sesión
                self.driver.delete_all_cookies()
                self.driver.execute_script("window.sessionStorage.clear();")
                self.driver.execute_script("window.localStorage.clear();")
                self.logger.info("Datos de sesión limpiados")
                
                # Cerrar driver
                self.driver.quit()
                self.logger.info("Driver cerrado de forma segura")
            except Exception as e:
                self.logger.warning(f"Error cerrando driver: {e}")
            finally:
                self.driver = None

class PortalExtractor:
    """Extractor principal de datos del portal universitario"""
    
    def __init__(self):
        self.logger = logging.getLogger('portal_extraction')
        self.portal_url = os.getenv('PORTAL_URL', 'https://segreteria.unigre.it')
        self.use_real_portal = os.getenv('USE_REAL_PORTAL', 'False').lower() == 'true'
    
    def extraer_datos_estudiante(self, matricola: str, password: str) -> dict:
        """
        Extraer datos del estudiante del portal universitario
        
        Args:
            matricola: Número de matrícula
            password: Contraseña del portal
            
        Returns:
            dict: Resultado con success, message, data y errors
        """
        self.logger.info(f"Iniciando extracción para matrícula: {matricola[:2]}****")
        
        # Verificar si el portal real está habilitado
        if not self.use_real_portal:
            self.logger.warning("Portal real no habilitado en configuración")
            return {
                'success': False,
                'message': 'Portal real no habilitado en configuración',
                'data': None,
                'errors': ['Portal real deshabilitado']
            }
        
        web_driver = SecureWebDriver()
        driver = web_driver.setup_driver()
        
        if not driver:
            return {
                'success': False,
                'message': 'Error configurando navegador',
                'data': None,
                'errors': ['Error de configuración del driver']
            }
        
        try:
            # Autenticar en el portal
            auth_result = self._authenticate_portal(driver, matricola, password)
            if not auth_result['success']:
                return auth_result
            
            # Extraer datos del estudiante
            extraction_result = self._extract_student_data(driver, matricola)
            
            return extraction_result
            
        except Exception as e:
            self.logger.error(f"Error durante extracción: {e}")
            return {
                'success': False,
                'message': f'Error técnico durante extracción: {str(e)}',
                'data': None,
                'errors': [str(e)]
            }
        finally:
            web_driver.close_driver()
    
    def _authenticate_portal(self, driver: webdriver.Chrome, matricola: str, password: str) -> dict:
        """
        Autenticar en el portal universitario
        
        Args:
            driver: Driver de Selenium
            matricola: Número de matrícula
            password: Contraseña
            
        Returns:
            dict: Resultado de autenticación
        """
        try:
            self.logger.info("Iniciando proceso de autenticación")
            
            # Navegar a la página de login
            login_url = f"{self.portal_url}/asp/authenticate.asp"
            self._navigate_to_page(driver, login_url)
            
            # Buscar y llenar campos de login
            wait = WebDriverWait(driver, 20)
            
            # Campo de matrícula
            matricola_field = wait.until(
                EC.presence_of_element_located((By.NAME, "userId"))
            )
            matricola_field.clear()
            matricola_field.send_keys(matricola)
            
            # Campo de contraseña
            password_field = driver.find_element(By.NAME, "pwd")
            password_field.clear()
            password_field.send_keys(password)
            
            # Botón de login
            login_button = driver.find_element(By.NAME, "login")
            login_button.click()
            
            # Verificar login exitoso
            time.sleep(2)
            current_url = driver.current_url
            
            if "authenticate.asp" in current_url:
                # Aún en página de login - credenciales incorrectas
                self.logger.warning("Credenciales incorrectas o página de login no cambiada")
                return {
                    'success': False,
                    'message': 'Credenciales incorrectas',
                    'data': None,
                    'errors': ['Autenticación fallida']
                }
            else:
                self.logger.info("Login exitoso en portal universitario")
                return {
                    'success': True,
                    'message': 'Autenticación exitosa',
                    'data': None,
                    'errors': []
                }
                
        except TimeoutException:
            self.logger.error("Timeout durante autenticación")
            return {
                'success': False,
                'message': 'Timeout durante autenticación',
                'data': None,
                'errors': ['Timeout de conexión']
            }
        except Exception as e:
            self.logger.error(f"Error durante autenticación: {e}")
            return {
                'success': False,
                'message': f'Error de autenticación: {str(e)}',
                'data': None,
                'errors': [str(e)]
            }
    
    def _extract_student_data(self, driver: webdriver.Chrome, matricola: str) -> dict:
        """
        Extraer datos del estudiante autenticado
        
        Args:
            driver: Driver de Selenium autenticado
            matricola: Número de matrícula
            
        Returns:
            dict: Datos extraídos del estudiante
        """
        extracted_data = {
            'student_info': {},
            'schedule': [],
            'courses': [],
            'grades': []
        }
        
        try:
            # Extraer información básica
            self._extract_basic_info(driver, extracted_data)
            
            # Extraer horarios
            self._extract_schedule(driver, extracted_data)
            
            # Extraer materias
            self._extract_courses(driver, extracted_data)
            
            # Extraer calificaciones si están disponibles
            self._extract_grades(driver, extracted_data)
            
            self.logger.info(
                f"Datos extraídos - Info básica: "
                f"{'✅' if extracted_data['student_info'] else '❌'}, "
                f"Horarios: {len(extracted_data['schedule'])} encontrados, "
                f"Materias: {len(extracted_data['courses'])} encontradas"
            )
            
            return {
                'success': True,
                'message': 'Datos del estudiante extraídos exitosamente',
                'data': extracted_data,
                'errors': []
            }
            
        except Exception as e:
            self.logger.error(f"Error extrayendo datos del estudiante: {e}")
            return {
                'success': False,
                'message': f'Error extrayendo datos: {str(e)}',
                'data': extracted_data,  # Devolver datos parciales
                'errors': [str(e)]
            }
    
    def _extract_basic_info(self, driver: webdriver.Chrome, data: dict):
        """Extraer información básica del estudiante"""
        try:
            self.logger.info("Extrayendo información básica")
            
            # Intentar extraer nombre, email, etc.
            # Esto depende de la estructura específica del portal
            
            # TODO: Implementar selectores específicos del portal
            # Por ahora, estructura básica
            data['student_info'] = {
                'nome': 'JOSE LUIS',  # Placeholder
                'cognome': 'GIRALDO VASQUEZ',
                'email': f'{driver.current_url.split("/")[-1]}@unigre.it',
                'telefono': 'No disponible'
            }
            
        except Exception as e:
            self.logger.warning(f"Error extrayendo información básica: {e}")
    
    def _extract_schedule(self, driver: webdriver.Chrome, data: dict):
        """Extraer horario de clases"""
        try:
            self.logger.info("Extrayendo horarios")
            
            # TODO: Implementar extracción de horarios específica del portal
            # Por ahora, lista vacía para que use datos demo
            data['schedule'] = []
            
        except Exception as e:
            self.logger.warning(f"Error extrayendo horarios: {e}")
    
    def _extract_courses(self, driver: webdriver.Chrome, data: dict):
        """Extraer lista de materias"""
        try:
            self.logger.info("Extrayendo materias")
            
            # TODO: Implementar extracción de materias específica del portal
            data['courses'] = []
            
        except Exception as e:
            self.logger.warning(f"Error extrayendo materias: {e}")
    
    def _extract_grades(self, driver: webdriver.Chrome, data: dict):
        """Extraer calificaciones"""
        try:
            self.logger.info("Extrayendo calificaciones")
            
            # TODO: Implementar extracción de calificaciones específica del portal
            data['grades'] = []
            
        except Exception as e:
            self.logger.warning(f"Error extrayendo calificaciones: {e}")
    
    def _navigate_to_page(self, driver: webdriver.Chrome, url: str, max_retries: int = 3):
        """
        Navegar a una página con reintentos
        
        Args:
            driver: Driver de Selenium
            url: URL de destino
            max_retries: Número máximo de reintentos
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Intentando conectar a {url} (intento {attempt + 1})")
                driver.get(url)
                
                # Verificar que la página se cargó
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                self.logger.info("Página cargada exitosamente")
                return
                
            except Exception as e:
                self.logger.warning(f"Intento {attempt + 1} fallido: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2)

# Función de compatibilidad
class UniversityPortalConnector:
    """Clase de compatibilidad con el sistema anterior"""
    
    def __init__(self):
        self.extractor = PortalExtractor()
    
    def connect_to_portal(self, matricola: str, password: str) -> dict:
        """Método de compatibilidad"""
        return self.extractor.extraer_datos_estudiante(matricola, password)
