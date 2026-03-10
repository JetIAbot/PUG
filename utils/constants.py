"""
Constants - Constantes centralizadas para PUG
Todas las configuraciones, selectores y constantes del sistema
"""

# --- CONFIGURACIÓN DE HORARIOS UNIVERSITARIOS ---
ORDEN_BLOQUES = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X']

BLOQUES_A_HORAS = {
    'I': '08:30 - 09:15', 
    'II': '09:30 - 10:15', 
    'III': '10:30 - 11:15',
    'IV': '11:30 - 12:15', 
    'V': '15:00 - 15:45', 
    'VI': '16:00 - 16:45',
    'VII': '17:00 - 17:45', 
    'VIII': '18:00 - 18:45', 
    'IX': '19:00 - 19:45',
    'X': '20:00 - 20:45'
}

DIAS_SEMANA = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato']

# --- URLS DEL PORTAL UNIVERSITARIO ---
URL_PORTAL_UNIVERSIDAD = "https://segreteria.unigre.it/asp/authenticate.asp"
URL_BASE_PORTAL = "https://segreteria.unigre.it"

# --- SELECTORES DE SELENIUM PARA PORTAL ---
# Verificado contra HTML real capturado el 2025-07-09
PORTAL_SELECTORS = {
    # Login — https://segreteria.unigre.it/asp/authenticate.asp
    'login': {
        'usuario': ("name", "txtName"),
        'password': ("name", "txtPassword"),
        'boton_login': ("xpath", "//input[@type='submit' and @value='Accedi']"),
        'error_message': ("xpath", "//*[contains(text(), 'ERRORE')]")
    },

    # Post-login — página con links de navegación
    'dashboard': {
        'bienvenida': ("xpath", "//*[contains(text(), 'Benvenuto')]"),
        'link_horario': ("link text", "Orario Settimanale")
    },

    # Información del estudiante — tabla GridView1 en orariopers.aspx
    'datos_personales': {
        'tabla_info': ("id", "GridView1"),
        'matricola': ("xpath", "//table[@id='GridView1']//tr[2]/td[1]"),
        'apellido': ("xpath", "//table[@id='GridView1']//tr[2]/td[2]"),
        'nombre': ("xpath", "//table[@id='GridView1']//tr[2]/td[3]")
    },

    # Horarios — div#orario1sem contiene ambos semestres como tablas sin ID
    # Página: https://segreteria.unigre.it/framework/orariopers/orariopers.aspx
    # Estructura: UpdatePanel1 > orario1sem > [H1 "Primo Semestre", table, H1 "Secondo Semestre", table]
    'horarios': {
        'contenedor_principal': ("id", "UpdatePanel1"),
        'contenedor_horarios': ("id", "orario1sem"),
        'titulo_semestre': ("xpath", "//div[@id='orario1sem']//h1"),
        'tablas_horario': ("xpath", "//div[@id='orario1sem']/table[@align='center']"),
        'boton_volver': ("id", "Button1")
    }
}

# --- CONFIGURACIÓN DE SISTEMA ---
MAX_RETRY_ATTEMPTS = 3
TIMEOUT_SELENIUM = 30
TIMEOUT_PAGE_LOAD = 20

# --- CONFIGURACIÓN DE LOGS ---
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

LOG_FORMATS = {
    'detailed': '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]',
    'simple': '%(asctime)s - %(levelname)s - %(message)s',
    'security': '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
}

# --- COLECCIONES DE DATOS ---
DATOS_COLLECTIONS = {
    'estudiantes': 'estudiantes',
    'carros': 'carros',
    'viajes': 'viajes',
    'listas_diarias': 'listas_diarias',
}

# --- MENSAJES DEL SISTEMA ---
MESSAGES = {
    'success': {
        'data_saved': 'Datos guardados exitosamente',
        'login_success': 'Login exitoso',
        'logout_success': 'Sesión cerrada exitosamente'
    },
    'error': {
        'connection_failed': 'Error de conexión',
        'invalid_credentials': 'Credenciales incorrectas',
        'data_not_found': 'Datos no encontrados',
        'system_error': 'Error del sistema'
    },
    'info': {
        'processing': 'Procesando datos...',
        'demo_mode': 'Usando datos de demostración',
        'real_data': 'Datos reales extraídos'
    }
}

# --- CONFIGURACIÓN DE DEMO ---
DEMO_NAMES = {
    'nombres': [
        'Marco', 'Giuseppe', 'Antonio', 'Francesco', 'Alessandro',
        'Andrea', 'Matteo', 'Lorenzo', 'Davide', 'Federico',
        'Giulia', 'Francesca', 'Chiara', 'Sara', 'Martina',
        'Alessia', 'Elena', 'Anna', 'Giorgia', 'Valentina'
    ],
    'apellidos': [
        'Rossi', 'Bianchi', 'Ferrari', 'Romano', 'Colombo',
        'Ricci', 'Marino', 'Greco', 'Bruno', 'Gallo',
        'Conti', 'De Luca', 'Mancini', 'Costa', 'Giordano'
    ]
}

DEMO_MATERIAS = [
    'Matematica I', 'Fisica I', 'Chimica Generale', 'Inglese I',
    'Informatica I', 'Filosofia', 'Storia Contemporanea', 'Economia',
    'Diritto', 'Psicologia', 'Sociologia', 'Letteratura Italiana',
    'Geografia', 'Biologia', 'Statistica'
]

DEMO_PROFESSORI = [
    'Prof. Alberti', 'Prof. Benedetti', 'Prof. Caruso', 'Prof. D\'Angelo',
    'Prof. Esposito', 'Prof. Fontana', 'Prof. Gentile', 'Prof. Leone',
    'Prof. Moretti', 'Prof. Ricci', 'Prof. Santoro', 'Prof. Vitale'
]

DEMO_AULAS = [
    'Aula Magna', 'Aula A1', 'Aula A2', 'Aula B1', 'Aula B2',
    'Lab. Informatica', 'Lab. Fisica', 'Lab. Chimica', 'Sala Seminari',
    'Aula Multimediale'
]

# --- VALIDACIÓN DE FORMULARIOS ---
VALIDATION_RULES = {
    'matricola': {
        'required': True,
        'min_length': 5,
        'max_length': 10,
        'pattern': r'^\d+$'
    },
    'password': {
        'required': True,
        'min_length': 6,
        'max_length': 50
    },
    'email': {
        'pattern': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    }
}

HORARIO_TABLA_SEMESTRE_2 = ("id", "gvOrario2") # Ejemplo: Tabla del segundo semestre