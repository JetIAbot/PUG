# matchmaking.py (Versión Final con Algoritmo de Matchmaking y Portal Real)

# --- IMPORTACIONES ---
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
from portal_connector import UniversityPortalConnector
from demo_data_generator import DemoDataGenerator, obtener_datos_demo_rapido
import logging

# Cargar variables de entorno
load_dotenv()

# --- DICCIONARIOS Y CONSTANTES DE CONFIGURACIÓN ---
ORDEN_BLOQUES = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
FIREBASE_CREDS_PATH = "credenciales.json" 
BLOQUES_A_HORAS = {
    'I': '08:30 - 09:15', 'II': '09:30 - 10:15', 'III': '10:30 - 11:15',
    'IV': '11:30 - 12:15', 'V': '15:00 - 15:45', 'VI': '16:00 - 16:45',
    'VII': '17:00 - 17:45', 'VIII': '18:00 - 18:45', 'IX': '19:00 - 19:45',
    'X': '20:00 - 20:45'
}

def inicializar_firebase():
    """Inicializa la conexión con Firebase si aún no existe."""
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate(FIREBASE_CREDS_PATH)
            firebase_admin.initialize_app(cred)
            return firestore.client()
        except Exception as e:
            print(f"Error al inicializar Firebase: {e}")
            return None
    return firestore.client()

def extraer_datos_portal_real(matricola: str, password: str) -> dict:
    """Extraer datos del portal universitario real de forma segura"""
    logger = logging.getLogger('portal_extraction')
    
    # Verificar si está habilitado el uso del portal real
    if os.getenv('USE_REAL_PORTAL', 'False').lower() != 'true':
        logger.warning("Portal real no habilitado en configuración")
        return {
            'success': False,
            'message': 'Portal real no habilitado',
            'data': None
        }
    
    try:
        logger.info(f"Iniciando extracción de datos para matrícula: {matricola[:2]}****")
        
        # Crear conector al portal
        portal_connector = UniversityPortalConnector()
        
        # Conectar y extraer datos
        result = portal_connector.connect_to_portal(matricola, password)
        
        if result['success']:
            logger.info("Conexión al portal exitosa")
            
            # Procesar y estructurar los datos según formato esperado
            if result['data']:
                processed_data = procesar_datos_portal(result['data'])
                result['data'] = processed_data
                
                # Información adicional sobre el estado de los datos
                estado_horarios = processed_data.get('estado_horarios', 'no_disponible')
                if estado_horarios == 'ejemplo_demo':
                    result['message'] += ' (usando datos de ejemplo - horarios no publicados aún)'
                    logger.info("Datos procesados con horarios de ejemplo")
                elif estado_horarios == 'disponible':
                    result['message'] += ' (horarios reales extraídos)'
                    logger.info("Datos procesados con horarios reales")
                else:
                    result['message'] += ' (datos básicos extraídos)'
                    logger.info("Datos básicos procesados")
            else:
                # Si no hay datos, crear estructura básica con datos de ejemplo realistas
                logger.warning("No se pudieron extraer datos específicos, generando datos de demostración")
                datos_demo = obtener_datos_demo_rapido(matricola)
                
                # Usar los datos del perfil extraído si están disponibles
                if result.get('data') and result['data'].get('student_info'):
                    student_info = result['data']['student_info']
                    datos_demo['perfil'].update({
                        'nome': student_info.get('nome', datos_demo['perfil']['nome']),
                        'cognome': student_info.get('cognome', datos_demo['perfil']['cognome']),
                        'matricola': matricola,
                        'email': student_info.get('email', f'{matricola}@unigre.it')
                    })
                
                result['data'] = datos_demo
                result['message'] += ' (usando datos de demostración realistas - horarios no publicados)'
        else:
            logger.error(f"Error extrayendo datos: {result['errors']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error durante extracción del portal: {e}")
        return {
            'success': False,
            'message': f'Error técnico: {str(e)}',
            'data': None,
            'errors': [str(e)]
        }

def procesar_datos_portal(raw_data: dict) -> dict:
    """Procesar datos del portal para formato estándar"""
    processed = {
        'perfil': {
            'nome': '',
            'cognome': '',
            'matricola': '',
            'email': '',
            'telefono': ''
        },
        'horario': [],
        'materias': [],
        'calificaciones': [],
        'estado_horarios': 'no_disponible'  # Nuevo campo para rastrear el estado
    }
    
    # Procesar información del estudiante
    if 'student_info' in raw_data:
        student_info = raw_data['student_info']
        processed['perfil'].update({
            'nome': student_info.get('nome', 'Usuario'),
            'cognome': student_info.get('cognome', 'Universitario'),
            'matricola': student_info.get('matricola', 'No disponible'),
            'email': student_info.get('email', 'no-disponible@universidad.edu'),
            'telefono': student_info.get('telefono', 'No disponible')
        })
    
    # Procesar horario
    if 'schedule' in raw_data and raw_data['schedule']:
        processed['horario'] = convertir_horario_portal(raw_data['schedule'])
        processed['estado_horarios'] = 'disponible'
        logging.getLogger('matchmaking').info(f"Horarios procesados: {len(processed['horario'])} clases")
    else:
        # Crear horario de ejemplo para demostración cuando no hay horarios reales
        processed['horario'] = generar_horario_ejemplo()
        processed['estado_horarios'] = 'ejemplo_demo'
        logging.getLogger('matchmaking').warning("Horarios no disponibles - usando datos de ejemplo para demostración")
    
    # Procesar materias
    if 'courses' in raw_data and raw_data['courses']:
        processed['materias'] = raw_data['courses']
    else:
        # Agregar materias de ejemplo basadas en el horario de ejemplo
        processed['materias'] = generar_materias_ejemplo()
    
    # Procesar calificaciones
    if 'grades' in raw_data:
        processed['calificaciones'] = raw_data['grades']
    
    return processed

def generar_horario_ejemplo() -> list:
    """Generar horario de ejemplo para demostración cuando no hay horarios reales"""
    # Usar el generador mejorado
    generator = DemoDataGenerator()
    horario_ejemplo = generator.generar_horario_demo(num_materias=5)
    
    logging.getLogger('matchmaking').info(f"Generado horario de ejemplo con {len(horario_ejemplo)} clases usando DemoDataGenerator")
    return horario_ejemplo

def generar_materias_ejemplo() -> list:
    """Generar materias de ejemplo para demostración"""
    # Usar el generador mejorado
    generator = DemoDataGenerator()
    materias_ejemplo = generator.generar_materias_demo(num_materias=5)
    
    logging.getLogger('matchmaking').info(f"Generadas {len(materias_ejemplo)} materias de ejemplo usando DemoDataGenerator")
    return materias_ejemplo

def convertir_horario_portal(schedule_data: list) -> list:
    """Convertir horario del portal al formato interno"""
    horario_convertido = []
    
    for clase in schedule_data:
        # Mapear según la estructura específica del portal
        clase_convertida = {
            'materia': clase.get('subject', ''),
            'profesor': clase.get('professor', ''),
            'dia': clase.get('day', ''),
            'bloque': clase.get('time_block', ''),
            'aula': clase.get('room', '')
        }
        horario_convertido.append(clase_convertida)
    
    return horario_convertido

def obtener_datos_de_firestore(db: firestore.client):
    """Obtiene los datos de todos los estudiantes y sus horarios desde Firestore."""
    print("Conectando a Firestore para obtener los datos de los estudiantes...")
    datos_estudiantes = {}
    try:
        estudiantes_ref = db.collection('estudiantes')
        for estudiante_doc in estudiantes_ref.stream():
            matricola = estudiante_doc.id
            datos_perfil = estudiante_doc.to_dict()
            
            # Verificación de datos básicos para evitar errores
            if not datos_perfil or 'nome' not in datos_perfil:
                print(f"Advertencia: El estudiante con matrícula {matricola} no tiene datos de perfil y será omitido.")
                continue

            datos_estudiantes[matricola] = {
                "nome": datos_perfil.get('nome', ''),
                "cognome": datos_perfil.get('cognome', ''),
                "horario": []
            }
            
            horario_ref = estudiante_doc.reference.collection('horario')
            for clase_doc in horario_ref.stream():
                datos_estudiantes[matricola]['horario'].append(clase_doc.to_dict())
                
        print(f"Se encontraron datos de {len(datos_estudiantes)} estudiante(s).")
        return datos_estudiantes
    except Exception as e:
        print(f"Error al obtener datos de Firestore: {e}")
        return {}

def aplanar_horarios(datos_estudiantes):
    """
    Procesa los horarios brutos para obtener la primera hora de entrada y la última de salida.
    """
    print("Procesando y aplanando horarios...")
    horarios_aplanados = {}
    for matricola, info in datos_estudiantes.items():
        horario_diario = {}
        for clase in info.get('horario', []):
            # Verificación de datos para evitar errores
            dia = clase.get('dia')
            bloque = clase.get('hora') # Corregido para coincidir con el scraper
            if not dia or not bloque:
                continue

            # --- CORRECCIÓN DE INDEXACIÓN ---
            # Se verifica si el bloque existe en ORDEN_BLOQUES antes de usarlo.
            if bloque not in ORDEN_BLOQUES:
                print(f"Advertencia: Bloque '{bloque}' desconocido para el estudiante {matricola}. Será omitido.")
                continue

            if dia not in horario_diario:
                horario_diario[dia] = []
            horario_diario[dia].append(bloque)

        horario_final_estudiante = {}
        for dia, bloques in horario_diario.items():
            bloques_ordenados = sorted(bloques, key=lambda b: ORDEN_BLOQUES.index(b))
            if bloques_ordenados:
                horario_final_estudiante[dia] = {"entrada": bloques_ordenados[0], "salida": bloques_ordenados[-1]}
        
        horarios_aplanados[matricola] = {
            "nome_completo": f"{info.get('nome', '')} {info.get('cognome', '')}".strip(),
            "horario_simple": horario_final_estudiante
        }
    return horarios_aplanados

def encontrar_coincidencias(horarios_aplanados):
    """
    Recibe los horarios aplanados y encuentra las coincidencias de viaje.
    """
    print("Buscando coincidencias de viaje...")
    indice_ida = {}
    indice_vuelta = {}

    # 1. Llenar los índices de ida y vuelta
    for matricola, data in horarios_aplanados.items():
        nombre = data['nome_completo']
        for dia, horas in data['horario_simple'].items():
            # Índice de IDA
            llave_ida = f"{dia}_{horas['entrada']}"
            if llave_ida not in indice_ida:
                indice_ida[llave_ida] = []
            indice_ida[llave_ida].append(nombre)

            # Índice de VUELTA
            llave_vuelta = f"{dia}_{horas['salida']}"
            if llave_vuelta not in indice_vuelta:
                indice_vuelta[llave_vuelta] = []
            indice_vuelta[llave_vuelta].append(nombre)

    # 2. Filtrar para encontrar los grupos reales (más de 1 persona)
    grupos_ida = {k: v for k, v in indice_ida.items() if len(v) > 1}
    grupos_vuelta = {k: v for k, v in indice_vuelta.items() if len(v) > 1}

    return {"ida": grupos_ida, "vuelta": grupos_vuelta}

def formatear_grupos_como_string(grupos_encontrados):
    """Formatea los grupos de viaje encontrados en un string para mostrar en la web."""
    output = ["="*40, "      GRUPOS DE VIAJE COMPATIBLES", "="*40]

    # Formatear viajes de IDA
    output.append("\n--- VIAJES DE IDA (Llegar a la universidad) ---\n")
    if not grupos_encontrados['ida']:
        output.append("No se encontraron coincidencias para viajes de ida.")
    else:
        for llave, personas in sorted(grupos_encontrados['ida'].items()):
            dia, bloque = llave.split('_')
            hora = BLOQUES_A_HORAS.get(bloque, bloque)
            output.append(f"Para llegar el {dia} a las {hora}:")
            output.append(f"  - Grupo compatible: {', '.join(personas)}\n")

    # Formatear viajes de VUELTA
    output.append("\n--- VIAJES DE VUELTA (Salir de la universidad) ---\n")
    if not grupos_encontrados['vuelta']:
        output.append("No se encontraron coincidencias para viajes de vuelta.")
    else:
        for llave, personas in sorted(grupos_encontrados['vuelta'].items()):
            dia, bloque = llave.split('_')
            hora = BLOQUES_A_HORAS.get(bloque, bloque)
            output.append(f"Para salir el {dia} a las {hora}:")
            output.append(f"  - Grupo compatible: {', '.join(personas)}\n")
    
    return "\n".join(output)

def realizar_matchmaking():
    """Función principal que orquesta y devuelve los resultados como string."""
    db = inicializar_firebase()
    if not db:
        return "Error: No se pudo conectar a la base de datos."

    datos_brutos = obtener_datos_de_firestore(db)
    if not datos_brutos:
        return "No se encontraron datos de estudiantes en Firestore."

    horarios_listos = aplanar_horarios(datos_brutos)
    grupos = encontrar_coincidencias(horarios_listos)
    return formatear_grupos_como_string(grupos)

if __name__ == '__main__':
    # La ejecución directa ahora usa la nueva función principal
    resultado_string = realizar_matchmaking()
    print(resultado_string)