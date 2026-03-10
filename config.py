"""
Configuración centralizada para PUG (Portal University Grouper)
Sistema CLI de agrupación de estudiantes universitarios para viajes compartidos
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base"""
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Almacenamiento local (Obsidian-style markdown DB)
    DATOS_PATH = os.getenv('DATOS_PATH', 'datos')
    
    # Portal Universitario
    USE_REAL_PORTAL = os.getenv('USE_REAL_PORTAL', 'False').lower() == 'true'
    PORTAL_URL = os.getenv('PORTAL_URL', 'https://segreteria.unigre.it')
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'True').lower() == 'true'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    AUTO_CLEANUP = os.getenv('AUTO_CLEANUP', 'True').lower() == 'true'
    LOG_MAX_DAYS = int(os.getenv('LOG_MAX_DAYS', '7'))
    
    # Seguridad
    MASK_CREDENTIALS = os.getenv('MASK_CREDENTIALS', 'True').lower() == 'true'
    LOG_SENSITIVE_DATA = os.getenv('LOG_SENSITIVE_DATA', 'False').lower() == 'true'
    
    # Demo/Desarrollo
    DEMO_MODE = os.getenv('DEMO_MODE', 'True').lower() == 'true'

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    DEMO_MODE = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    DEMO_MODE = False

class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    DEBUG = True

# Configuración por defecto basada en el entorno
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Obtener configuración según el entorno"""
    env = os.getenv('APP_ENV', 'development')
    return config.get(env, config['default'])
