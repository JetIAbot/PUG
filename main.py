# Importamos las librerías necesarias
import os
import time
import firebase_admin
from firebase_admin import credentials, firestore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN INICIAL ---
# DEBES RELLENAR ESTAS VARIABLES CON LOS DATOS REALES
URL_LOGIN = "https://segreteria.unigre.it/asp/authenticate.asp"
# ¡NUNCA dejes las credenciales escritas directamente en el código en una versión final!
# Para esta prueba, puedes ponerlas aquí. Luego te enseñaré un método más seguro.
USUARIO = os.getenv("USUARIO_UNIGRE")
CONTRASENA = os.getenv("CONTRASENA_UNIGRE")


def configurar_driver():
    """Configura e inicia el navegador Chrome con Selenium."""
    options = webdriver.ChromeOptions()
    # Descomenta la siguiente línea para que el navegador se ejecute en segundo plano (sin ventana)
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    # Instala y configura el driver de Chrome automáticamente
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def iniciar_sesion(driver, usuario, contrasena):
    """Navega a la página de login e inicia sesión."""
    print("Accediendo a la página de login...")
    driver.get(URL_LOGIN)
    time.sleep(3) # Espera 3 segundos para que la página cargue completamente

    try:
        # --- ¡ACCIÓN REQUERIDA! ---
        # Usa "Inspeccionar Elemento" en tu navegador para encontrar los IDs o Nombres
        # de los campos de usuario y contraseña.
        campo_usuario = driver.find_element(By.NAME, 'txtName') # Cambia 'id_del_campo_usuario'
        campo_contrasena = driver.find_element(By.NAME, 'txtPassword') # Cambia 'id_del_campo_contrasena'
        boton_login = driver.find_element(By.CLASS_NAME, 'verdanaCorpo12B_2') # O busca por ID, Class, etc.

        print("Introduciendo credenciales...")
        campo_usuario.send_keys(usuario)
        campo_contrasena.send_keys(contrasena)
        
        print("Haciendo clic en el botón de login...")
        boton_login.click()
        time.sleep(5) # Espera a que la página de bienvenida cargue
        print("Login exitoso.")
        return True
    except Exception as e:
        print(f"Error durante el login: {e}")
        return False

def navegar_a_horarios(driver):
    """Navega desde la página principal hasta la sección de horarios."""
    print("Navegando a la sección de horarios...")
    try:
        # --- ¡ACCIÓN REQUERIDA! ---
        # Después de iniciar sesión, busca el enlace o botón que lleva a los horarios.
        # Puede ser por el texto del enlace, su ID, etc.
        enlace_horarios = driver.find_element(By.LINK_TEXT, 'Orario Settimanale') # Cambia 'Mi Horario' por el texto real
        enlace_horarios.click()
        time.sleep(5) # Espera a que la página de horarios cargue
        print("Página de horarios cargada.")
    except Exception as e:
        print(f"No se pudo encontrar el enlace a los horarios: {e}")

def extraer_datos_personales(driver):
    """
    Extrae los datos personales del estudiante (matrícula, apellido, nombre)
    de la tabla con id 'GridView1'.
    """
    print("Extrayendo datos personales del estudiante...")
    try:
        # Buscamos la tabla por su ID único
        tabla_datos = driver.find_element(By.ID, 'GridView1')
        
        # El HTML de esa tabla específica
        html_tabla = tabla_datos.get_attribute('outerHTML')
        soup_tabla = BeautifulSoup(html_tabla, 'html.parser')
        
        # Los datos están en la segunda fila <tr>. La primera es la cabecera.
        fila_datos = soup_tabla.find_all('tr')[1]
        celdas = fila_datos.find_all('td')
        
        # Extraemos el texto de cada celda según su posición
        matricola = celdas[0].get_text(strip=True)
        cognome = celdas[1].get_text(strip=True)
        nome = celdas[2].get_text(strip=True)
        
        datos_personales = {
            'matricola': matricola,
            'cognome': cognome,
            'nome': nome
        }
        
        print(f"Datos encontrados: Matrícula {matricola}, {cognome} {nome}")
        return datos_personales

    except Exception as e:
        print(f"Error al extraer los datos personales: {e}")
        # Es crucial que estos datos se encuentren, si no, devolvemos None
        return None

def extraer_datos_horario(driver):
    """
    Extrae la información de las tablas de horarios (formato calendario)
    para el primer y segundo semestre.
    """
    print("Extrayendo datos del horario...")
    
    # Obtenemos el código HTML de la página actual, ya renderizado por el navegador
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    horario_final = []
    
    # Buscamos el contenedor principal que tiene ambas tablas
    contenedor_principal = soup.find('div', id='orario1sem')
    if not contenedor_principal:
        print("Error: No se encontró el contenedor principal con id 'orario1sem'.")
        return []

    # Buscamos todos los títulos h1 para identificar cada semestre
    titulos_semestre = contenedor_principal.find_all('h1')

    for titulo in titulos_semestre:
        nombre_semestre = titulo.get_text(strip=True)
        # La tabla del horario es el siguiente elemento "hermano" después del h1
        tabla = titulo.find_next_sibling('table')
        
        if not tabla:
            print(f"No se encontró una tabla después del título '{nombre_semestre}'")
            continue

        print(f"--- Procesando: {nombre_semestre} ---")
        
        # 1. Extraer los nombres de los días de la semana de la cabecera
        filas_cabecera = tabla.find('thead').find_all('tr')
        dias_semana = []
        # Los días están en la primera fila de la cabecera
        for th in filas_cabecera[0].find_all('th')[1:]: # Saltamos el primer 'th' (Ora/Giorno)
            dias_semana.append(th.get_text(strip=True))

        # 2. Iterar sobre las filas de datos (los bloques horarios)
        # El HTML usa 'thead' para cada fila, así que buscamos todas las filas 'tr' dentro de la tabla
        filas_horario = tabla.find_all('tr')[1:] # Saltamos la fila de cabecera de los días

        for fila in filas_horario:
            celdas = fila.find_all(['th', 'td']) # Obtenemos tanto la cabecera de la hora como las celdas de datos
            if not celdas:
                continue

            # La primera celda es el bloque horario (I, II, III...)
            bloque_horario = celdas[0].get_text(strip=True)
            
            # Las celdas restantes son las clases
            celdas_clases = celdas[1:]

            # 3. Iterar sobre cada celda de clase en la fila
            for i, celda_clase in enumerate(celdas_clases):
                # Si la celda tiene texto, significa que hay una clase
                if celda_clase.get_text(strip=True):
                    info_clase = celda_clase.get_text(separator='\n', strip=True) # Usamos separador por si hay saltos de línea
                    dia_correspondiente = dias_semana[i] # Mapeamos la celda al día usando el índice

                    clase = {
                        'semestre': nombre_semestre,
                        'dia': dia_correspondiente,
                        'bloque_horario': bloque_horario,
                        'info_clase': info_clase
                    }
                    horario_final.append(clase)

    print(f"Proceso completado. Se encontraron {len(horario_final)} bloques de clase en total.")
    return horario_final

# ... (aquí van todas tus funciones: configurar_driver, iniciar_sesion, etc.) ...

def actualizar_estudiante_y_horario_en_firestore(db, datos_personales, horario_data):
    """
    Crea o actualiza los datos de un estudiante en Firestore usando la matrícula como ID.
    Luego, si el horario no está vacío, borra el antiguo y guarda el nuevo.
    """
    matricola = datos_personales['matricola']
    print(f"Actualizando perfil del estudiante con matrícula '{matricola}' en Firestore...")

    # 1. ACTUALIZAR DATOS PERSONALES (SIEMPRE)
    # Referencia al documento del estudiante usando su matrícula como ID único.
    estudiante_ref = db.collection('estudiantes').document(matricola)
    
    # Preparamos los datos del perfil sin la matrícula (ya que es el ID)
    perfil_data = {
        'cognome': datos_personales['cognome'],
        'nome': datos_personales['nome']
    }
    
    # Usamos set con merge=True. Esto crea el documento si no existe,
    # o actualiza solo los campos 'cognome' y 'nome' sin borrar otros datos (como el horario).
    estudiante_ref.set(perfil_data, merge=True)
    print("Datos del perfil (nombre, apellido) guardados/actualizados.")

    # 2. ACTUALIZAR HORARIO (SOLO SI NO ESTÁ VACÍO)
    if horario_data:
        print("Horario con datos detectado. Procediendo a guardarlo...")
        horario_ref = estudiante_ref.collection('horario')
        
        # Borramos el horario antiguo para evitar duplicados
        docs = horario_ref.stream()
        for doc in docs:
            doc.reference.delete()
        
        # Añadimos las nuevas clases
        for clase in horario_data:
            horario_ref.add(clase)
        
        print(f"¡Horario guardado con éxito para la matrícula '{matricola}'!")
    else:
        # Si horario_data está vacío, simplemente informamos y no hacemos nada con el horario.
        print("El horario extraído está vacío. No se realizarán cambios en el horario de Firestore.")


# --- FUNCIÓN PRINCIPAL QUE EJECUTA TODO (VERSIÓN FINAL CON DATOS PERSONALES) ---
if __name__ == '__main__':
    # 1. INICIALIZACIÓN DE FIREBASE
    cred = credentials.Certificate("credenciales.json") 
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    # 2. PROCESO DE SCRAPING
    driver = configurar_driver()
    try:
        if iniciar_sesion(driver, USUARIO, CONTRASENA):
            navegar_a_horarios(driver)
            
            # 3. EXTRACCIÓN DE DATOS (AMBAS PARTES)
            datos_personales = extraer_datos_personales(driver)
            
            # Si no se pueden extraer los datos personales, no podemos continuar.
            if not datos_personales:
                raise Exception("No se pudieron obtener los datos personales, el script no puede continuar.")

            # Esperamos a que el horario se cargue (si es que hay)
            try:
                wait = WebDriverWait(driver, 5) # Reducimos la espera a 5 segs para esta prueba
                wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//div[@id='orario1sem']//td[normalize-space(.)]")
                ))
            except Exception as e:
                print("No se encontraron datos en la tabla de horarios (esperado durante las vacaciones).")
            
            # Extraemos el horario (devolverá una lista vacía si no hay nada)
            horario_extraido = extraer_datos_horario(driver)
            
            # 4. GUARDAR EN FIREBASE CON LA NUEVA LÓGICA
            actualizar_estudiante_y_horario_en_firestore(db, datos_personales, horario_extraido)

    except Exception as e:
        print(f"\nOcurrió un error general en el script: {e}")

    finally:
        print("\nCerrando el navegador.")
        driver.quit()