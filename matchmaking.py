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
            print(f"Error: El archivo de credenciales '{FIREBASE_CREDS_PATH}' no fue encontrado.")
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

def imprimir_grupos(grupos_encontrados):
    """Formatea e imprime los grupos de viaje encontrados."""
    print("\n" + "="*40)
    print("      GRUPOS DE VIAJE COMPATIBLES")
    print("="*40)

    # Imprimir viajes de IDA
    print("\n--- VIAJES DE IDA (Llegar a la universidad) ---\n")
    if not grupos_encontrados['ida']:
        print("No se encontraron coincidencias para viajes de ida.")
    else:
        for llave, personas in grupos_encontrados['ida'].items():
            dia, bloque = llave.split('_')
            hora = BLOQUES_A_HORAS.get(bloque, bloque)
            print(f"Para llegar el {dia} a las {hora}:")
            print(f"  - Grupo compatible: {', '.join(personas)}\n")

    # Imprimir viajes de VUELTA
    print("\n--- VIAJES DE VUELTA (Salir de la universidad) ---\n")
    if not grupos_encontrados['vuelta']:
        print("No se encontraron coincidencias para viajes de vuelta.")
    else:
        for llave, personas in grupos_encontrados['vuelta'].items():
            dia, bloque = llave.split('_')
            hora = BLOQUES_A_HORAS.get(bloque, bloque)
            print(f"Para salir el {dia} a las {hora}:")
            print(f"  - Grupo compatible: {', '.join(personas)}\n")

def main():
    """Función principal que orquesta el proceso de matchmaking."""
    db = inicializar_firebase()
    if not db:
        print("El script no puede continuar sin una conexión a la base de datos.")
        return

    datos_brutos = obtener_datos_de_firestore(db)
    
    if not datos_brutos:
        print("No se encontraron datos de estudiantes en Firestore. El script no puede continuar.")
        return

    horarios_listos_para_comparar = aplanar_horarios(datos_brutos)
    grupos_de_viaje = encontrar_coincidencias(horarios_listos_para_comparar)
    imprimir_grupos(grupos_de_viaje)

if __name__ == '__main__':
    main()