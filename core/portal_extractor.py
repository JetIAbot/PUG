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
            
            # Configuraciones del driver
            driver_options = [
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-blink-features=AutomationControlled',
            ]
            
            for option in driver_options:
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
                EC.presence_of_element_located((By.NAME, "txtName"))
            )
            matricola_field.clear()
            matricola_field.send_keys(matricola)
            
            # Campo de contraseña
            password_field = driver.find_element(By.NAME, "txtPassword")
            password_field.clear()
            password_field.send_keys(password)
            
            # Botón de login
            login_button = driver.find_element(
                By.XPATH, "//input[@type='submit' and @value='Accedi']"
            )
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
            'grades': [],
            'semestre_activo': None,  # 1 o 2, según cuál tenga datos
            'semestres_detectados': {},  # {1: N_bloques, 2: N_bloques}
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
            
            sem_activo = extracted_data.get('semestre_activo')
            sem_label = f"semestre {sem_activo}" if sem_activo else "ninguno"
            self.logger.info(
                f"Datos extraídos - Info básica: "
                f"{'OK' if extracted_data['student_info'] else 'NO'}, "
                f"Horarios: {len(extracted_data['schedule'])} encontrados, "
                f"Materias: {len(extracted_data['courses'])} encontradas, "
                f"Semestre activo: {sem_label}"
            )
            
            return {
                'success': True,
                'message': f'Datos extraídos ({sem_label} activo)',
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
        """Extraer información básica del estudiante desde GridView1"""
        try:
            self.logger.info("Extrayendo información básica")
            sel = PORTAL_SELECTORS['datos_personales']

            tabla = driver.find_element(By.ID, "GridView1")
            filas = tabla.find_elements(By.TAG_NAME, "tr")
            if len(filas) >= 2:
                celdas = filas[1].find_elements(By.TAG_NAME, "td")
                data['student_info'] = {
                    'matricola': celdas[0].text.strip() if len(celdas) > 0 else '',
                    'cognome': celdas[1].text.strip() if len(celdas) > 1 else '',
                    'nome': celdas[2].text.strip() if len(celdas) > 2 else '',
                }
                self.logger.info(
                    f"Info extraída: {data['student_info']['cognome']} "
                    f"{data['student_info']['nome']}"
                )
            else:
                self.logger.warning("GridView1 no tiene filas de datos")

        except NoSuchElementException:
            self.logger.warning("GridView1 no encontrado en la página")
        except Exception as e:
            self.logger.warning(f"Error extrayendo información básica: {e}")
    
    def _extract_schedule(self, driver: webdriver.Chrome, data: dict):
        """
        Extraer horario de clases desde la página orariopers.aspx
        
        Navega a "Orario Settimanale" (postback ASP.NET), luego parsea
        las tablas dentro de div#orario1sem. Ambos semestres están en
        tablas <table align="center"> sin ID, precedidas por <h1>.
        
        Formato de celda con datos:
            <b>CÓDIGO</b><br>NOMBRE_CURSO<br><br>PROFESOR<br><br>Aula: SALA  Piano: PISO<br>
        """
        from selenium.webdriver.support.expected_conditions import staleness_of
        try:
            self.logger.info("Navegando a horarios")

            # Buscar link "Orario Settimanale" y hacer click (produce postback)
            wait = WebDriverWait(driver, 20)
            link = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Orario Settimanale"))
            )
            old_body = driver.find_element(By.TAG_NAME, "body")
            link.click()

            # Esperar que el postback reemplace la página
            WebDriverWait(driver, 20).until(staleness_of(old_body))
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(1)
            self.logger.info(f"Página de horarios cargada: {driver.current_url}")

            # Buscar el contenedor de horarios
            contenedor = driver.find_element(By.ID, "orario1sem")

            # Obtener todas las tablas y títulos H1 dentro del contenedor
            elementos = contenedor.find_elements(
                By.XPATH, ".//h1 | .//table[@align='center']"
            )

            semestre_actual = None
            for elem in elementos:
                tag = elem.tag_name.lower()
                if tag == "h1":
                    texto = elem.text.strip().lower()
                    if "primo" in texto:
                        semestre_actual = 1
                    elif "secondo" in texto:
                        semestre_actual = 2
                elif tag == "table" and semestre_actual is not None:
                    self._parse_schedule_table(elem, semestre_actual, data)

            # Determinar semestre activo: el que tiene datos publicados
            conteo = {}
            for bloque in data['schedule']:
                sem = bloque['semestre']
                conteo[sem] = conteo.get(sem, 0) + 1
            data['semestres_detectados'] = conteo

            if conteo:
                # El semestre activo es el que tiene más bloques con clase
                data['semestre_activo'] = max(conteo, key=conteo.get)
                self.logger.info(
                    f"Semestre activo: {data['semestre_activo']} "
                    f"({conteo} bloques por semestre)"
                )
            else:
                self.logger.warning("Ningún semestre tiene datos publicados")

            self.logger.info(f"Horarios extraídos: {len(data['schedule'])} bloques")

        except TimeoutException:
            self.logger.warning("Timeout navegando a horarios")
        except NoSuchElementException as e:
            self.logger.warning(f"Elemento no encontrado en horarios: {e}")
        except Exception as e:
            self.logger.warning(f"Error extrayendo horarios: {e}")

    def _parse_schedule_table(self, table_elem, semestre: int, data: dict):
        """
        Parsear una tabla de horario semanal.
        
        Estructura:
            thead fila 0: [Ora/Giorno, Lunedì, Martedì, Mercoledì, Giovedì, Venerdì]
            thead filas 1+: [slot_romano, celda_lun, celda_mar, celda_mie, celda_jue, celda_vie]
        """
        from utils.constants import DIAS_SEMANA, BLOQUES_A_HORAS
        filas = table_elem.find_elements(By.XPATH, ".//thead/tr | .//tbody/tr")

        for fila in filas:
            celdas = fila.find_elements(By.TAG_NAME, "td")
            encabezado = fila.find_elements(By.TAG_NAME, "th")

            if not encabezado or not celdas:
                continue

            bloque = encabezado[0].text.strip()
            if bloque not in BLOQUES_A_HORAS:
                continue

            for idx, celda in enumerate(celdas):
                texto = celda.text.strip()
                if not texto:
                    continue
                if idx >= len(DIAS_SEMANA):
                    break

                dia = DIAS_SEMANA[idx]
                curso_info = self._parse_cell_content(celda, bloque, dia, semestre)
                if curso_info:
                    data['schedule'].append(curso_info)

    @staticmethod
    def _parse_cell_content(celda, bloque: str, dia: str, semestre: int) -> Optional[dict]:
        """
        Parsear el contenido de una celda de horario.
        
        HTML típico:
            <b>TP1011              </b><br>
            PATROLOGIA<br><br>
            R.P. Prof. CAROLA Joseph<br><br>
            Aula: C208                  Piano : 2<br>
        """
        try:
            bold = celda.find_elements(By.TAG_NAME, "b")
            codigo = bold[0].text.strip() if bold else ""

            # Obtener texto completo y dividir por líneas reales
            inner = celda.get_attribute("innerHTML")
            # Separar por <br> tags
            import re
            partes = [p.strip() for p in re.split(r'<br\s*/?>', inner) if p.strip()]

            # Quitar la parte del código (ya está en el tag <b>)
            # partes típicas: ["<b>TP1011</b>", "PATROLOGIA", "", "R.P. Prof. CAROLA Joseph", "", "Aula: C208  Piano : 2"]
            nombre = ""
            profesor = ""
            aula = ""

            # Filtrar tags HTML y strings vacíos
            limpias = []
            for p in partes:
                limpia = re.sub(r'<[^>]+>', '', p).strip()
                if limpia:
                    limpias.append(limpia)

            # limpias: ["TP1011", "PATROLOGIA", "R.P. Prof. CAROLA Joseph", "Aula: C208 Piano : 2"]
            if len(limpias) >= 2:
                nombre = limpias[1]
            if len(limpias) >= 3:
                profesor = limpias[2]
            if len(limpias) >= 4:
                aula = limpias[3]

            return {
                'semestre': semestre,
                'bloque': bloque,
                'dia': dia,
                'codigo': codigo,
                'materia': nombre,
                'profesor': profesor,
                'aula': aula,
            }
        except Exception:
            return None
    
    def _extract_courses(self, driver: webdriver.Chrome, data: dict):
        """Construir lista de materias únicas a partir del horario extraído"""
        try:
            self.logger.info("Construyendo lista de materias desde horario")
            cursos_vistos = {}
            for bloque in data.get('schedule', []):
                codigo = bloque.get('codigo', '')
                if codigo and codigo not in cursos_vistos:
                    cursos_vistos[codigo] = {
                        'codigo': codigo,
                        'nombre': bloque.get('materia', ''),
                        'profesor': bloque.get('profesor', ''),
                        'semestre': bloque.get('semestre', 0),
                    }
            data['courses'] = list(cursos_vistos.values())
            self.logger.info(f"Materias únicas encontradas: {len(data['courses'])}")
        except Exception as e:
            self.logger.warning(f"Error construyendo lista de materias: {e}")
    
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
