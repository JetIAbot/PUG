"""
Archivo para centralizar todas las constantes y configuraciones del proyecto.
"""

# --- URLS ---
# ¡ÚLTIMO PASO! Reemplaza esto con la URL real y completa del portal.
URL_PORTAL_UNIVERSIDAD = "https://segreteria.unigre.it/asp/authenticate.asp" 

# --- SELECTORES DE SELENIUM ---

# Página de Login (Completado)
LOGIN_CAMPO_USUARIO = ("name", "txtName")
LOGIN_CAMPO_CONTRASENA = ("name", "txtPassword")
LOGIN_BOTON_ENTRAR = ("css selector", "input[type='submit'][value='Accedi']")
LOGIN_ERROR_MESSAGE = ("xpath", "//*[contains(text(), 'ERRORE DI AUTENTICAZIONE')]")

# Página Post-Login (Completado)
POST_LOGIN_ELEMENTO_BIENVENIDA = ("xpath", "//*[contains(text(), 'Benvenuto nella Segreteria Online')]")

# Selectores de Navegación (Completado)
NAV_LINK_HORARIO = ("link text", "Orario Settimanale")

# Selectores de Contenido Final (Completado)
DATOS_TABLA_INFO_PERSONAL = ("class name", "renderedtable11")
HORARIO_CONTENEDOR_PRINCIPAL = ("id", "UpdatePanel1")

# --- ¡NUEVO! Selectores para las tablas de horarios de los dos semestres ---
# Estos selectores asumen que las tablas se pueden identificar por un ID o un selector CSS único.
# Estos son ejemplos y podrían necesitar ajuste fino una vez que los horarios se publiquen.
HORARIO_TABLA_SEMESTRE_1 = ("id", "gvOrario1") # Ejemplo: Tabla del primer semestre
HORARIO_TABLA_SEMESTRE_2 = ("id", "gvOrario2") # Ejemplo: Tabla del segundo semestre