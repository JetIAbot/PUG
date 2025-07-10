# matchmaking.py (Versión Final con Algoritmo de Matchmaking)

# --- IMPORTACIONES ---
import firebase_admin
from firebase_admin import credentials, firestore

# --- DICCIONARIOS Y CONSTANTES DE CONFIGURACIÓN ---
ORDEN_BLOQUES = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']
# Se asume que credenciales.json está en el mismo directorio
FIREBASE_CREDS_PATH = "credenciales.json" 

# Mapeo de bloques a horas (ajustar si es necesario)
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
        except FileNotFoundError:
            # La ruta ahora debe considerar que el script se ejecuta desde la raíz del proyecto
            print(f"Error: El archivo de credenciales '{FIREBASE_CREDS_PATH}' no fue encontrado. Asegúrate de que esté en la raíz del proyecto.")
            return None
        except Exception as e:
            print(f"Error al inicializar Firebase: {e}")
            return None
    return firestore.client()

def obtener_datos_de_firestore(db: firestore.client):
    """
    Obtiene los datos de todos los estudiantes y sus horarios desde Firestore.
    """
    print("Conectando a Firestore para obtener los datos de los estudiantes...")
    datos_estudiantes = {}
    estudiantes_ref = db.collection('estudiantes')
    
    for estudiante_doc in estudiantes_ref.stream():
        matricola = estudiante_doc.id
        datos_perfil = estudiante_doc.to_dict()
        
        datos_estudiantes[matricola] = {
            "nome": datos_perfil.get('nome', ''),
            "cognome": datos_perfil.get('cognome', ''),
            "horario": []
        }
        
        # Obtenemos el horario de la subcolección
        horario_ref = estudiante_doc.reference.collection('horario')
        for clase_doc in horario_ref.stream():
            datos_estudiantes[matricola]['horario'].append(clase_doc.to_dict())
            
    print(f"Se encontraron datos de {len(datos_estudiantes)} estudiante(s).")
    return datos_estudiantes

def obtener_datos_de_prueba():
    # ... (Esta función no cambia, la dejamos como está)
    print("Cargando datos de prueba (mock data)...")
    datos = {
        "172934": {"nome": "Jose", "cognome": "Giraldo", "horario": [{'dia': 'Lunedì', 'bloque_horario': 'II', 'info_clase': 'Teologia Fondamentale'}, {'dia': 'Lunedì', 'bloque_horario': 'III', 'info_clase': 'Teologia Fondamentale'}, {'dia': 'Martedì', 'bloque_horario': 'IV', 'info_clase': 'Antropologia'}, {'dia': 'Mercoledì', 'bloque_horario': 'V', 'info_clase': 'Sacra Scrittura'}]},
        "183345": {"nome": "Maria", "cognome": "Rossi", "horario": [{'dia': 'Lunedì', 'bloque_horario': 'II', 'info_clase': 'Diritto Canonico'}, {'dia': 'Mercoledì', 'bloque_horario': 'V', 'info_clase': 'Patrologia'}, {'dia': 'Mercoledì', 'bloque_horario': 'VI', 'info_clase': 'Patrologia'}]},
        "194456": {"nome": "Luca", "cognome": "Bianchi", "horario": [{'dia': 'Martedì', 'bloque_horario': 'IV', 'info_clase': 'Filosofia'}, {'dia': 'Mercoledì', 'bloque_horario': 'IV', 'info_clase': 'Storia della Chiesa'}, {'dia': 'Mercoledì', 'bloque_horario': 'VI', 'info_clase': 'Storia della Chiesa'}, {'dia': 'Venerdì', 'bloque_horario': 'III', 'info_clase': 'Lingua Latina'}]},
        "205567": {"nome": "Sofia", "cognome": "Verdi", "horario": [{'dia': 'Giovedì', 'bloque_horario': 'I', 'info_clase': 'Arte Sacra'}, {'dia': 'Venerdì', 'bloque_horario': 'IV', 'info_clase': 'Musica Gregoriana'}]}
    }
    return datos

def aplanar_horarios(datos_estudiantes):
    # ... (Esta función no cambia, la dejamos como está)
    print("Procesando y aplanando horarios...")
    horarios_aplanados = {}
    for matricola, info in datos_estudiantes.items():
        horario_diario = {}
        for clase in info['horario']:
            dia = clase['dia']
            if dia not in horario_diario: horario_diario[dia] = []
            horario_diario[dia].append(clase['bloque_horario'])
        horario_final_estudiante = {}
        for dia, bloques in horario_diario.items():
            bloques_ordenados = sorted(bloques, key=lambda b: ORDEN_BLOQUES.index(b))
            if bloques_ordenados:
                horario_final_estudiante[dia] = {"entrada": bloques_ordenados[0], "salida": bloques_ordenados[-1]}
        horarios_aplanados[matricola] = {"nome_completo": f"{info['nome']} {info['cognome']}", "horario_simple": horario_final_estudiante}
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
        horario = data['horario_simple']
        
        for dia, horas in horario.items():
            # Clave para ida: (dia, bloque_entrada)
            clave_ida = (dia, horas['entrada'])
            if clave_ida not in indice_ida:
                indice_ida[clave_ida] = []
            indice_ida[clave_ida].append(f"{nombre} ({matricola})")

            # Clave para vuelta: (dia, bloque_salida)
            clave_vuelta = (dia, horas['salida'])
            if clave_vuelta not in indice_vuelta:
                indice_vuelta[clave_vuelta] = []
            indice_vuelta[clave_vuelta].append(f"{nombre} ({matricola})")

    # 2. Construir los grupos a partir de los índices
    grupos_ida = {f"{dia} a las {BLOQUES_A_HORAS[bloque]}": personas for (dia, bloque), personas in indice_ida.items() if len(personas) > 1}
    grupos_vuelta = {f"{dia} a las {BLOQUES_A_HORAS[bloque]}": personas for (dia, bloque), personas in indice_vuelta.items() if len(personas) > 1}
    
    print("Coincidencias encontradas.")
    return grupos_ida, grupos_vuelta

def formatear_resultados(grupos_ida, grupos_vuelta):
    """
    Formatea los grupos encontrados en un string legible para el administrador.
    """
    print("Formateando resultados...")
    output = "--- GRUPOS DE IDA (HACIA LA UNIVERSIDAD) ---\n"
    if not grupos_ida:
        output += "No se encontraron grupos para el viaje de ida.\n"
    else:
        for horario, personas in sorted(grupos_ida.items()):
            output += f"\n[+] Horario: {horario}\n"
            output += "    Miembros: " + ", ".join(personas) + "\n"

    output += "\n--- GRUPOS DE VUELTA (DESDE LA UNIVERSIDAD) ---\n"
    if not grupos_vuelta:
        output += "No se encontraron grupos para el viaje de vuelta.\n"
    else:
        for horario, personas in sorted(grupos_vuelta.items()):
            output += f"\n[+] Horario: {horario}\n"
            output += "    Miembros: " + ", ".join(personas) + "\n"
            
    return output

def run_matchmaking_logic():
    """
    Función principal que orquesta todo el proceso de matchmaking.
    Esta función será llamada desde app.py.
    """
    db = inicializar_firebase()
    if not db:
        return "Error: No se pudo inicializar la conexión con Firebase."

    # Descomentar para usar datos reales de Firestore
    datos_estudiantes = obtener_datos_de_firestore(db)
    
    # Comentar o eliminar si se usan datos de Firestore
    # datos_estudiantes = obtener_datos_de_prueba()

    if not datos_estudiantes:
        return "No se encontraron datos de estudiantes para procesar."

    horarios_aplanados = aplanar_horarios(datos_estudiantes)
    grupos_ida, grupos_vuelta = encontrar_coincidencias(horarios_aplanados)
    resultado_final = formatear_resultados(grupos_ida, grupos_vuelta)
    
    print(resultado_final) # Imprime en la consola del servidor para depuración
    return resultado_final # Devuelve el string para la interfaz web

if __name__ == '__main__':
    """
    Este bloque permite que el script siga siendo ejecutable de forma independiente
    para pruebas o depuración.
    """
    run_matchmaking_logic()