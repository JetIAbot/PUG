# matchmaking.py (versión con traducción de horas)

# ... (importaciones que podríamos necesitar en el futuro) ...

# --- DICCIONARIOS Y CONSTANTES DE CONFIGURACIÓN ---

# MEJORA: Diccionario para traducir los bloques a horas legibles
BLOQUES_A_HORAS = {
    'I': '08:30 - 09:15',
    'II': '09:30 - 10:15',
    'III': '10:30 - 11:15',
    'IV': '11:30 - 12:15',
    'V': '15:00 - 15:45',
    'VI': '16:00 - 16:45',
    'VII': '17:00 - 17:45',
    'VIII': '18:00 - 18:45',
    # Asumimos los siguientes por si aparecen en los datos
    'IX': '19:00 - 19:45', 
    'X': '20:00 - 20:45'
}

# Lista para mantener el orden cronológico correcto de los bloques
ORDEN_BLOQUES = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

def obtener_datos_de_prueba():
    """
    Esta función simula la lectura de datos desde Firestore.
    Devuelve datos de prueba para trabajar sin conexión.
    """
    print("Cargando datos de prueba (mock data)...")
    # (El contenido de esta función es idéntico al anterior)
    datos = {
        "172934": {
            "nome": "Jose", "cognome": "Giraldo", "horario": [
                {'dia': 'Lunedì', 'bloque_horario': 'II', 'info_clase': 'Teologia Fondamentale'},
                {'dia': 'Lunedì', 'bloque_horario': 'III', 'info_clase': 'Teologia Fondamentale'},
                {'dia': 'Martedì', 'bloque_horario': 'IV', 'info_clase': 'Antropologia'},
                {'dia': 'Mercoledì', 'bloque_horario': 'V', 'info_clase': 'Sacra Scrittura'},
            ]
        },
        "183345": {
            "nome": "Maria", "cognome": "Rossi", "horario": [
                {'dia': 'Lunedì', 'bloque_horario': 'II', 'info_clase': 'Diritto Canonico'},
                {'dia': 'Mercoledì', 'bloque_horario': 'V', 'info_clase': 'Patrologia'},
                {'dia': 'Mercoledì', 'bloque_horario': 'VI', 'info_clase': 'Patrologia'},
            ]
        },
        "194456": {
            "nome": "Luca", "cognome": "Bianchi", "horario": [
                {'dia': 'Martedì', 'bloque_horario': 'IV', 'info_clase': 'Filosofia'},
                {'dia': 'Mercoledì', 'bloque_horario': 'IV', 'info_clase': 'Storia della Chiesa'},
                {'dia': 'Mercoledì', 'bloque_horario': 'VI', 'info_clase': 'Storia della Chiesa'},
                {'dia': 'Venerdì', 'bloque_horario': 'III', 'info_clase': 'Lingua Latina'},
            ]
        },
        "205567": {
            "nome": "Sofia", "cognome": "Verdi", "horario": [
                {'dia': 'Giovedì', 'bloque_horario': 'I', 'info_clase': 'Arte Sacra'},
                {'dia': 'Venerdì', 'bloque_horario': 'IV', 'info_clase': 'Musica Gregoriana'},
            ]
        }
    }
    return datos

def aplanar_horarios(datos_estudiantes):
    """
    Toma los datos brutos de los estudiantes y transforma sus horarios
    en un formato simple de entrada/salida por día.
    """
    print("Procesando y aplanando horarios...")
    horarios_aplanados = {}
    
    for matricola, info in datos_estudiantes.items():
        horario_diario = {}
        for clase in info['horario']:
            dia = clase['dia']
            if dia not in horario_diario:
                horario_diario[dia] = []
            horario_diario[dia].append(clase['bloque_horario'])
        
        horario_final_estudiante = {}
        for dia, bloques in horario_diario.items():
            bloques_ordenados = sorted(bloques, key=lambda b: ORDEN_BLOQUES.index(b))
            if bloques_ordenados:
                horario_final_estudiante[dia] = {
                    "entrada": bloques_ordenados[0],
                    "salida": bloques_ordenados[-1]
                }
        
        horarios_aplanados[matricola] = {
            "nome_completo": f"{info['nome']} {info['cognome']}",
            "horario_simple": horario_final_estudiante
        }
        
    return horarios_aplanados

def encontrar_coincidencias(horarios_aplanados):
    """
    Recibe los horarios aplanados y encuentra las coincidencias
    de viaje de ida y vuelta.
    """
    print("Buscando coincidencias de viaje...")
    
    # Por ahora, solo imprimimos los datos procesados para verificar con el nuevo formato de hora
    for matricola, data in horarios_aplanados.items():
        print(f"\nMatrícula: {matricola} ({data['nome_completo']})")
        if data['horario_simple']:
            for dia, horas in data['horario_simple'].items():
                # --- MEJORA: Usamos el diccionario para mostrar la hora real ---
                hora_entrada_legible = BLOQUES_A_HORAS.get(horas['entrada'], horas['entrada'])
                hora_salida_legible = BLOQUES_A_HORAS.get(horas['salida'], horas['salida'])
                print(f"  {dia}: Entrada a las {hora_entrada_legible}, Salida a las {hora_salida_legible}")
        else:
            print("  Sin horario registrado.")

    # Devolveremos una estructura con los grupos encontrados
    return "Función de matchmaking aún no implementada."


if __name__ == '__main__':
    # 1. Obtener los datos (por ahora, de nuestra función de prueba)
    datos_brutos = obtener_datos_de_prueba()
    
    # 2. Procesar los horarios a un formato simple
    horarios_listos_para_comparar = aplanar_horarios(datos_brutos)
    
    # 3. Encontrar y mostrar las coincidencias
    grupos_de_viaje = encontrar_coincidencias(horarios_listos_para_comparar)