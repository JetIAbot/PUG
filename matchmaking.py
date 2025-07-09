# matchmaking.py (Versión Final con Algoritmo de Matchmaking)

# --- DICCIONARIOS Y CONSTANTES DE CONFIGURACIÓN ---
BLOQUES_A_HORAS = {
    'I': '08:30 - 09:15', 'II': '09:30 - 10:15', 'III': '10:30 - 11:15',
    'IV': '11:30 - 12:15', 'V': '15:00 - 15:45', 'VI': '16:00 - 16:45',
    'VII': '17:00 - 17:45', 'VIII': '18:00 - 18:45', 'IX': '19:00 - 19:45',
    'X': '20:00 - 20:45'
}
ORDEN_BLOQUES = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

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

if __name__ == '__main__':
    # 1. Obtener los datos (por ahora, de nuestra función de prueba)
    datos_brutos = obtener_datos_de_prueba()
    
    # 2. Procesar los horarios a un formato simple
    horarios_listos_para_comparar = aplanar_horarios(datos_brutos)
    
    # 3. Encontrar las coincidencias
    grupos_de_viaje = encontrar_coincidencias(horarios_listos_para_comparar)
    
    # 4. Imprimir los resultados de forma clara
    imprimir_grupos(grupos_de_viaje)