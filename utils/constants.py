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
PORTAL_SELECTORS = {
    # Login
    'login': {
        'usuario': ("name", "userId"),
        'password': ("name", "pwd"),
        'boton_login': ("name", "login"),
        'error_message': ("xpath", "//*[contains(text(), 'ERRORE')]")
    },
    
    # Post-login
    'dashboard': {
        'bienvenida': ("xpath", "//*[contains(text(), 'Benvenuto')]"),
        'link_horario': ("link text", "Orario Settimanale")
    },
    
    # Datos personales
    'datos_personales': {
        'tabla_info': ("class name", "renderedtable11"),
        'nombre': ("xpath", "//td[contains(text(), 'Nome')]/following-sibling::td"),
        'apellido': ("xpath", "//td[contains(text(), 'Cognome')]/following-sibling::td"),
        'email': ("xpath", "//td[contains(text(), 'E-mail')]/following-sibling::td")
    },
    
    # Horarios
    'horarios': {
        'contenedor_principal': ("id", "UpdatePanel1"),
        'tabla_semestre_1': ("id", "gvOrario1"),
        'tabla_semestre_2': ("id", "gvOrario2"),
        'fila_clase': ("xpath", "//tr[contains(@class, 'gridrow')]"),
        'celda_materia': ("td", 1),
        'celda_profesor': ("td", 2),
        'celda_dia': ("td", 3),
        'celda_hora': ("td", 4),
        'celda_aula': ("td", 5)
    },
    
    # Materias
    'materias': {
        'tabla_materias': ("id", "gvMaterie"),
        'fila_materia': ("xpath", "//tr[contains(@class, 'gridrow')]")
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

# --- CONFIGURACIÓN DE FIREBASE ---
FIREBASE_COLLECTIONS = {
    'estudiantes': 'estudiantes',
    'horarios': 'horario',
    'materias': 'materias',
    'calificaciones': 'calificaciones',
    'admin': 'admin_users'
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

# --- CONFIGURACIÓN DE CELERY ---
CELERY_TASK_ROUTES = {
    'app.procesar_estudiante_async': {'queue': 'main'},
    'app.cleanup_old_data': {'queue': 'maintenance'}
}

CELERY_BEAT_SCHEDULE = {
    'cleanup-logs': {
        'task': 'app.cleanup_old_logs',
        'schedule': 86400.0,  # 24 horas
    },
}
HORARIO_TABLA_SEMESTRE_2 = ("id", "gvOrario2") # Ejemplo: Tabla del segundo semestre