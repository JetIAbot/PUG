"""
Configuración centralizada para PUG (Portal University Grouper)
Sistema de agrupación de estudiantes universitarios para viajes compartidos
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    """Configuración base"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'credenciales.json')
    
    # Portal Universitario
    USE_REAL_PORTAL = os.getenv('USE_REAL_PORTAL', 'False').lower() == 'true'
    PORTAL_URL = os.getenv('PORTAL_URL', 'https://segreteria.unigre.it')
    
    # Celery (para tareas asíncronas)
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    AUTO_CLEANUP = os.getenv('AUTO_CLEANUP', 'True').lower() == 'true'
    LOG_MAX_DAYS = int(os.getenv('LOG_MAX_DAYS', '7'))
    
    # Seguridad
    SESSION_TIMEOUT = int(os.getenv('SESSION_TIMEOUT', '3600'))  # 1 hora
    MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '3'))
    
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
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
