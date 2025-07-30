"""
Configuración segura de Selenium para uso con portal real de universidad
"""
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class SecureWebDriver:
    """Driver de Selenium configurado de forma segura para portal universitario"""
    
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger('selenium_secure')
        self.setup_secure_driver()
    
    def setup_secure_driver(self):
        """Configurar Chrome con opciones de seguridad máxima"""
        try:
            chrome_options = Options()
            
            # Configuraciones básicas de seguridad
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--ignore-certificate-errors-spki')
            
            # Configuración de headless si está habilitado
            if os.getenv('HEADLESS_MODE', 'True').lower() == 'true':
                chrome_options.add_argument('--headless=new')  # Usar nueva implementación de headless
            
            # Configuración de modo privado
            if os.getenv('BROWSER_PRIVATE_MODE', 'True').lower() == 'true':
                chrome_options.add_argument('--incognito')
            
            # Configuración de caché
            if os.getenv('DISABLE_CACHE', 'True').lower() == 'true':
                chrome_options.add_argument('--disable-application-cache')
                chrome_options.add_argument('--disk-cache-size=0')
                chrome_options.add_argument('--media-cache-size=0')
            
            # User agent realista
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Configurar window size para evitar problemas
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            
            # Deshabilitar logging del navegador
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--silent')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Configuraciones experimentales para estabilidad
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,
                    "geolocation": 2,
                },
                "profile.default_content_settings.popups": 0,
                # Permitir imágenes para formularios (pueden ser necesarias)
                "profile.managed_default_content_settings.images": 1
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Configurar descarga de archivos si es necesario
            download_dir = os.path.join(os.getcwd(), "temp_downloads")
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            download_prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", download_prefs)
            
            # Intentar crear el driver con múltiples estrategias
            driver_created = False
            
            # Estrategia 1: Usar Chrome del sistema (más estable)
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                driver_created = True
                self.logger.info("Driver creado exitosamente con Chrome del sistema")
            except Exception as e:
                self.logger.warning(f"Chrome del sistema falló: {e}")
            
            # Estrategia 2: Usar WebDriverManager (si el anterior falla)
            if not driver_created:
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    driver_created = True
                    self.logger.info("Driver creado exitosamente con WebDriverManager")
                except Exception as e:
                    self.logger.warning(f"WebDriverManager falló: {e}")
            
            # Estrategia 3: Modo compatible (sin algunas opciones problemáticas)
            if not driver_created:
                try:
                    # Crear opciones más básicas
                    basic_options = Options()
                    basic_options.add_argument('--no-sandbox')
                    basic_options.add_argument('--disable-dev-shm-usage')
                    basic_options.add_argument('--window-size=1920,1080')
                    
                    if os.getenv('HEADLESS_MODE', 'False').lower() == 'true':
                        basic_options.add_argument('--headless=new')
                    
                    self.driver = webdriver.Chrome(options=basic_options)
                    driver_created = True
                    self.logger.info("Driver creado exitosamente con configuración básica")
                except Exception as e:
                    self.logger.error(f"Configuración básica también falló: {e}")
            
            if not driver_created:
                raise Exception("No se pudo crear el driver de Chrome con ninguna configuración")
            
            # Configurar timeouts del driver
            timeout = int(os.getenv('REQUEST_TIMEOUT', '60'))
            self.driver.set_page_load_timeout(timeout)
            self.driver.implicitly_wait(10)
            
            # Ejecutar JavaScript para evitar detección
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Driver de Selenium configurado de forma segura")
            
        except Exception as e:
            self.logger.error(f"Error configurando driver seguro: {e}")
            raise
    
    def safe_get(self, url: str, max_retries: int = None) -> bool:
        """Navegación segura a URL con reintentos"""
        if max_retries is None:
            max_retries = int(os.getenv('MAX_RETRIES', '3'))
        
        retry_delay = int(os.getenv('RETRY_DELAY', '5'))
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Intentando conectar a {self._mask_url(url)} (intento {attempt + 1})")
                self.driver.get(url)
                
                # Verificar que la página cargó correctamente
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                
                self.logger.info("Página cargada exitosamente")
                return True
                
            except TimeoutException:
                self.logger.warning(f"Timeout en intento {attempt + 1}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            
            except WebDriverException as e:
                self.logger.error(f"Error de WebDriver en intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        self.logger.error(f"Falló conectar después de {max_retries} intentos")
        return False
    
    def safe_find_element(self, by: By, value: str, timeout: int = 10):
        """Búsqueda segura de elementos con timeout"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"Elemento no encontrado: {by}={value}")
            return None
    
    def safe_click(self, element, timeout: int = 10) -> bool:
        """Click seguro en elemento"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(element)
            )
            element.click()
            return True
        except TimeoutException:
            self.logger.warning("Elemento no es clickeable")
            return False
        except Exception as e:
            self.logger.error(f"Error en click: {e}")
            return False
    
    def safe_send_keys(self, element, keys: str, clear_first: bool = True) -> bool:
        """Envío seguro de texto a elemento"""
        try:
            if clear_first:
                element.clear()
            element.send_keys(keys)
            return True
        except Exception as e:
            self.logger.error(f"Error enviando texto: {e}")
            return False
    
    def _mask_url(self, url: str) -> str:
        """Enmascarar URL para logs seguros"""
        if 'segreteria' in url:
            return url.replace('segreteria.unigre.it', '***PORTAL_UNIVERSITARIO***')
        return url
    
    def clear_session_data(self):
        """Limpiar datos de sesión del navegador"""
        try:
            if self.driver:
                self.driver.delete_all_cookies()
                self.driver.execute_script("window.localStorage.clear();")
                self.driver.execute_script("window.sessionStorage.clear();")
                self.logger.info("Datos de sesión limpiados")
        except Exception as e:
            self.logger.error(f"Error limpiando sesión: {e}")
    
    def close_secure(self):
        """Cerrar navegador de forma segura"""
        try:
            if self.driver:
                # Limpiar datos si está configurado
                if os.getenv('CLEAR_SESSION_ON_EXIT', 'True').lower() == 'true':
                    self.clear_session_data()
                
                self.driver.quit()
                self.driver = None
                self.logger.info("Driver cerrado de forma segura")
        except Exception as e:
            self.logger.error(f"Error cerrando driver: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_secure()


class UniversityPortalConnector:
    """Conector específico para el portal universitario con todas las medidas de seguridad"""
    
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger('university_portal')
        self.portal_url = os.getenv('PORTAL_URL', 'https://segreteria.unigre.it/asp/authenticate.asp')
    
    def connect_to_portal(self, matricola: str, password: str) -> dict:
        """Conectar al portal universitario de forma segura"""
        result = {
            'success': False,
            'message': '',
            'data': None,
            'errors': []
        }
        
        try:
            with SecureWebDriver() as secure_driver:
                self.driver = secure_driver.driver
                
                # Conectar al portal
                if not secure_driver.safe_get(self.portal_url):
                    result['errors'].append('No se pudo conectar al portal universitario')
                    return result
                
                # Buscar campos de login
                username_field = secure_driver.safe_find_element(By.NAME, "txtName")
                password_field = secure_driver.safe_find_element(By.NAME, "txtPassword")
                login_button = secure_driver.safe_find_element(By.CSS_SELECTOR, "input[type='submit'][value='Accedi']")
                
                if not all([username_field, password_field, login_button]):
                    result['errors'].append('No se encontraron los campos de login')
                    return result
                
                # Realizar login
                self.logger.info("Iniciando proceso de autenticación")
                
                if not secure_driver.safe_send_keys(username_field, matricola):
                    result['errors'].append('Error enviando matrícula')
                    return result
                
                if not secure_driver.safe_send_keys(password_field, password):
                    result['errors'].append('Error enviando contraseña')
                    return result
                
                if not secure_driver.safe_click(login_button):
                    result['errors'].append('Error haciendo click en login')
                    return result
                
                # Esperar respuesta
                time.sleep(3)
                
                # Verificar si el login fue exitoso
                current_url = self.driver.current_url
                page_source = self.driver.page_source
                
                # Buscar indicadores de éxito/error
                if "ERRORE DI AUTENTICAZIONE" in page_source:
                    result['errors'].append('Credenciales incorrectas')
                    self.logger.warning("Login fallido: credenciales incorrectas")
                    return result
                
                if "Benvenuto nella Segreteria Online" in page_source:
                    result['success'] = True
                    result['message'] = 'Login exitoso'
                    self.logger.info("Login exitoso en portal universitario")
                    
                    # Extraer datos del estudiante después del login exitoso
                    try:
                        result['data'] = self.extract_student_data()
                        self.logger.info("Datos del estudiante extraídos exitosamente")
                    except Exception as e:
                        self.logger.warning(f"Error extrayendo datos del estudiante: {e}")
                        # Continuar con login exitoso pero sin datos adicionales
                        result['data'] = self.get_default_student_data()
                    
                else:
                    result['errors'].append('Estado de login incierto')
                    self.logger.warning("Estado de login no claro")
                
        except Exception as e:
            result['errors'].append(f'Error durante conexión al portal: {str(e)}')
            self.logger.error(f"Error en conexión al portal: {e}")
        
        return result
    
    def extract_student_data(self) -> dict:
        """Extraer datos del estudiante desde el portal universitario real"""
        data = {
            'student_info': {},
            'courses': [],
            'grades': [],
            'schedule': []
        }
        
        try:
            # Extraer información básica del estudiante
            student_info = self.extract_basic_info()
            data['student_info'] = student_info
            
            # Intentar extraer horarios (pueden estar vacíos si no están publicados)
            schedule_data = self.extract_schedule_info()
            data['schedule'] = schedule_data
            
            # Intentar extraer materias
            courses_data = self.extract_courses_info()
            data['courses'] = courses_data
            
            # Log del estado de los datos extraídos
            self.logger.info(f"Datos extraídos - Info básica: {'✅' if student_info else '❌'}, "
                           f"Horarios: {len(schedule_data)} encontrados, "
                           f"Materias: {len(courses_data)} encontradas")
            
        except Exception as e:
            self.logger.error(f"Error durante extracción de datos: {e}")
            # Retornar datos básicos por defecto
            data = self.get_default_student_data()
        
        return data
    
    def extract_basic_info(self) -> dict:
        """Extraer información básica del estudiante del portal"""
        student_info = {}
        
        try:
            # Buscar elementos que contengan información del estudiante
            # Esto puede variar según la estructura específica del portal
            
            # Intentar encontrar el nombre del estudiante
            name_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "td:contains('Nome'), td:contains('Cognome'), h1, h2, .student-name")
            
            for element in name_elements:
                text = element.text.strip()
                if text and len(text) > 2:  # Filtrar textos muy cortos
                    # Analizar el texto para extraer nombre y apellido
                    if "Nome:" in text or "Cognome:" in text:
                        parts = text.split(":")
                        if len(parts) > 1:
                            value = parts[1].strip()
                            if "Nome" in text:
                                student_info['nome'] = value
                            elif "Cognome" in text:
                                student_info['cognome'] = value
            
            # Si no encontramos nombre/apellido específico, buscar en el título
            if not student_info.get('nome') or not student_info.get('cognome'):
                title_elements = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, .page-title")
                for element in title_elements:
                    text = element.text.strip()
                    if "Benvenuto" in text and len(text.split()) >= 2:
                        # Extraer nombre del saludo "Benvenuto [NOMBRE]"
                        parts = text.split()
                        if len(parts) >= 2:
                            full_name = " ".join(parts[1:])
                            name_parts = full_name.split()
                            if len(name_parts) >= 2:
                                student_info['nome'] = name_parts[0]
                                student_info['cognome'] = " ".join(name_parts[1:])
                            elif len(name_parts) == 1:
                                student_info['nome'] = name_parts[0]
            
            # Buscar matrícula en la URL o en elementos visibles
            current_url = self.driver.current_url
            if "matricola=" in current_url:
                matricola = current_url.split("matricola=")[1].split("&")[0]
                student_info['matricola'] = matricola
            
            self.logger.info(f"Información básica extraída: {len(student_info)} campos")
            
        except Exception as e:
            self.logger.warning(f"Error extrayendo información básica: {e}")
        
        return student_info
    
    def extract_schedule_info(self) -> list:
        """Extraer información de horarios del portal (puede estar vacía)"""
        schedule_data = []
        
        try:
            # Buscar tablas de horarios
            schedule_tables = self.driver.find_elements(By.CSS_SELECTOR, 
                "table.schedule, table.horario, table[contains(@class,'orario')], "
                ".schedule-table, .timetable")
            
            if not schedule_tables:
                # Buscar cualquier tabla que pueda contener horarios
                all_tables = self.driver.find_elements(By.TAG_NAME, "table")
                for table in all_tables:
                    table_text = table.text.lower()
                    if any(keyword in table_text for keyword in 
                          ["orario", "schedule", "lunedì", "martedì", "mercoledì", 
                           "giovedì", "venerdì", "monday", "tuesday"]):
                        schedule_tables.append(table)
            
            if schedule_tables:
                self.logger.info(f"Encontradas {len(schedule_tables)} tablas de horarios")
                
                for table in schedule_tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    
                    for row in rows[1:]:  # Saltar encabezados
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:  # Debe tener al menos día, hora, materia
                            schedule_entry = {
                                'day': cells[0].text.strip() if cells[0].text.strip() else 'Sin especificar',
                                'time_block': cells[1].text.strip() if cells[1].text.strip() else 'Sin especificar',
                                'subject': cells[2].text.strip() if cells[2].text.strip() else 'Sin especificar',
                                'professor': cells[3].text.strip() if len(cells) > 3 and cells[3].text.strip() else 'Por asignar',
                                'room': cells[4].text.strip() if len(cells) > 4 and cells[4].text.strip() else 'Por asignar'
                            }
                            
                            # Solo agregar si tiene información útil
                            if (schedule_entry['subject'] != 'Sin especificar' and 
                                schedule_entry['subject'] != '' and
                                'sin información' not in schedule_entry['subject'].lower()):
                                schedule_data.append(schedule_entry)
            
            if not schedule_data:
                self.logger.warning("No se encontraron horarios publicados en el portal")
                self.logger.info("Esto es normal si los horarios no han sido publicados aún")
            else:
                self.logger.info(f"Extraídos {len(schedule_data)} elementos de horario")
                
        except Exception as e:
            self.logger.warning(f"Error extrayendo horarios: {e}")
        
        return schedule_data
    
    def extract_courses_info(self) -> list:
        """Extraer información de materias/cursos del portal"""
        courses_data = []
        
        try:
            # Buscar listas de materias o cursos
            course_elements = self.driver.find_elements(By.CSS_SELECTOR,
                ".course-list li, .materia-item, .subject-list li, "
                "table.courses tr, table.materias tr")
            
            for element in course_elements:
                course_text = element.text.strip()
                if course_text and len(course_text) > 3:
                    courses_data.append({
                        'name': course_text,
                        'code': '',  # Podría extraerse si está disponible
                        'credits': '',  # Podría extraerse si está disponible
                        'status': 'active'
                    })
            
            self.logger.info(f"Extraídas {len(courses_data)} materias")
            
        except Exception as e:
            self.logger.warning(f"Error extrayendo materias: {e}")
        
        return courses_data
    
    def get_default_student_data(self) -> dict:
        """Retornar datos por defecto cuando no se pueden extraer del portal"""
        return {
            'student_info': {
                'nome': 'Usuario',
                'cognome': 'Universitario',
                'matricola': 'No disponible',
                'email': 'no-disponible@universidad.edu',
                'telefono': 'No disponible'
            },
            'courses': [
                {
                    'name': 'Materia de ejemplo (horarios no publicados)',
                    'code': 'TEMP001',
                    'credits': '6',
                    'status': 'pending_schedule'
                }
            ],
            'grades': [],
            'schedule': []
        }


# Función de utilidad para pruebas
def test_portal_connection():
    """Función de prueba para verificar conectividad al portal"""
    connector = UniversityPortalConnector()
    
    # Usar credenciales de prueba (reemplazar con reales cuando sea necesario)
    test_matricola = "123456"  # Reemplazar con real
    test_password = "test123"  # Reemplazar con real
    
    result = connector.connect_to_portal(test_matricola, test_password)
    
    if result['success']:
        print("✅ Conexión al portal exitosa")
        print(f"Mensaje: {result['message']}")
    else:
        print("❌ Error conectando al portal")
        for error in result['errors']:
            print(f"Error: {error}")
    
    return result


if __name__ == "__main__":
    # Ejecutar prueba de conexión
    test_portal_connection()
