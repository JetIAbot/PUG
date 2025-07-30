import logging
import logging.handlers
import json
import os
import hashlib
import re
from datetime import datetime
from typing import Dict, Any

class SecurityLogger:
    """Logger especializado para eventos de seguridad con protección de datos sensibles"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.mask_credentials = os.getenv('MASK_CREDENTIALS', 'True').lower() == 'true'
        self.log_sensitive_data = os.getenv('LOG_SENSITIVE_DATA', 'False').lower() == 'true'
        self.ensure_log_directory()
        self.setup_loggers()
    
    def ensure_log_directory(self):
        """Crear directorio de logs si no existe"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _mask_sensitive_data(self, data: Any) -> Any:
        """Enmascarar datos sensibles antes de hacer log"""
        if not self.mask_credentials:
            return data
            
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if key.lower() in ['password', 'contrasena', 'passwd', 'pwd', 'secret', 'token']:
                    masked_data[key] = "***MASKED***"
                elif key.lower() in ['matricola', 'username', 'user_id'] and isinstance(value, str):
                    # Enmascarar parcialmente la matrícula (mostrar solo primeros 2 dígitos)
                    masked_data[key] = value[:2] + "****" if len(value) > 2 else "****"
                else:
                    masked_data[key] = self._mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, str):
            # Buscar y enmascarar patrones que parezcan credenciales
            patterns = [
                (r'\b\d{6,8}\b', lambda m: m.group()[:2] + "****"),  # Matrículas
                (r'password[=:]\s*\S+', 'password=***MASKED***'),
                (r'contrasena[=:]\s*\S+', 'contrasena=***MASKED***'),
            ]
            for pattern, replacement in patterns:
                if callable(replacement):
                    data = re.sub(pattern, replacement, data, flags=re.IGNORECASE)
                else:
                    data = re.sub(pattern, replacement, data, flags=re.IGNORECASE)
        return data
    
    def setup_loggers(self):
        """Configurar diferentes loggers para diferentes tipos de eventos"""
        
        # Logger general de la aplicación
        self.app_logger = self._create_logger(
            'app', 
            os.path.join(self.log_dir, 'app.log'),
            logging.INFO
        )
        
        # Logger específico de seguridad
        self.security_logger = self._create_logger(
            'security',
            os.path.join(self.log_dir, 'security.log'),
            logging.WARNING
        )
        
        # Logger de errores críticos
        self.error_logger = self._create_logger(
            'errors',
            os.path.join(self.log_dir, 'errors.log'),
            logging.ERROR
        )
        
        # Logger de auditoría
        self.audit_logger = self._create_logger(
            'audit',
            os.path.join(self.log_dir, 'audit.log'),
            logging.INFO
        )
    
    def _create_logger(self, name: str, filename: str, level: int) -> logging.Logger:
        """Crear logger con configuración específica"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # Evitar duplicar handlers
        if logger.handlers:
            return logger
        
        # Handler para archivo con rotación
        file_handler = logging.handlers.RotatingFileHandler(
            filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        
        # Formatter JSON para mejor parsing
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], 
                          user_id: str = None, ip_address: str = None):
        """Registrar evento de seguridad con enmascaramiento de datos sensibles"""
        event_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': self._mask_sensitive_data(user_id) if user_id else None,
            'ip_address': ip_address,
            'details': self._mask_sensitive_data(details)
        }
        
        self.security_logger.warning(json.dumps(event_data))
    
    def log_login_attempt(self, matricola: str, success: bool, 
                         ip_address: str, user_agent: str = None):
        """Registrar intento de login con datos enmascarados"""
        self.log_security_event(
            'login_attempt',
            {
                'matricola': self._mask_sensitive_data(matricola) if self.mask_credentials else matricola,
                'success': success,
                'user_agent': user_agent
            },
            matricola,
            ip_address
        )
    
    def log_data_extraction(self, matricola: str, success: bool, 
                           duration: float = None, error: str = None):
        """Registrar extracción de datos"""
        details = {
            'success': success,
            'duration_seconds': duration
        }
        
        if error:
            details['error'] = error
        
        self.log_security_event(
            'data_extraction',
            details,
            matricola
        )
    
    def log_admin_action(self, admin_id: str, action: str, 
                        target: str = None, details: Dict = None):
        """Registrar acción de administrador"""
        event_details = {
            'action': action,
            'target': target
        }
        
        if details:
            event_details.update(details)
        
        self.log_security_event(
            'admin_action',
            event_details,
            admin_id
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Registrar error con contexto"""
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        
        self.error_logger.error(json.dumps(error_data))

# Instancia global del logger
security_logger = SecurityLogger()
