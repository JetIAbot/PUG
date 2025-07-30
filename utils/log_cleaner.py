"""
Sistema de limpieza automática de logs para proteger datos sensibles
"""
import os
import time
import glob
from datetime import datetime, timedelta
import logging

class LogCleaner:
    """Limpiador automático de logs para proteger datos sensibles"""
    
    def __init__(self, log_dir: str = "logs", retention_days: int = 7):
        self.log_dir = log_dir
        self.retention_days = retention_days
        self.logger = logging.getLogger('log_cleaner')
    
    def clean_old_logs(self):
        """Limpiar logs antiguos basado en el tiempo de retención"""
        try:
            cutoff_time = time.time() - (self.retention_days * 24 * 60 * 60)
            
            log_files = glob.glob(os.path.join(self.log_dir, "*.log*"))
            
            for log_file in log_files:
                file_time = os.path.getctime(log_file)
                if file_time < cutoff_time:
                    self._secure_delete(log_file)
                    self.logger.info(f"Log eliminado por política de retención: {log_file}")
                    
        except Exception as e:
            self.logger.error(f"Error durante limpieza de logs: {e}")
    
    def _secure_delete(self, file_path: str):
        """Eliminación segura de archivos sobrescribiendo el contenido"""
        try:
            # Obtener tamaño del archivo
            file_size = os.path.getsize(file_path)
            
            # Sobrescribir con datos aleatorios
            with open(file_path, 'r+b') as file:
                file.write(os.urandom(file_size))
                file.flush()
                os.fsync(file.fileno())
            
            # Eliminar el archivo
            os.remove(file_path)
            
        except Exception as e:
            self.logger.error(f"Error en eliminación segura de {file_path}: {e}")
    
    def emergency_cleanup(self):
        """Limpieza de emergencia: eliminar todos los logs inmediatamente"""
        try:
            log_files = glob.glob(os.path.join(self.log_dir, "*.log*"))
            
            for log_file in log_files:
                self._secure_delete(log_file)
                
            self.logger.info("Limpieza de emergencia completada")
            
        except Exception as e:
            self.logger.error(f"Error durante limpieza de emergencia: {e}")
    
    def mask_existing_logs(self):
        """Enmascarar datos sensibles en logs existentes"""
        try:
            log_files = glob.glob(os.path.join(self.log_dir, "*.log"))
            
            for log_file in log_files:
                self._mask_file_content(log_file)
                
        except Exception as e:
            self.logger.error(f"Error durante enmascaramiento de logs: {e}")
    
    def _mask_file_content(self, file_path: str):
        """Enmascarar contenido sensible en un archivo de log"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Patrones para enmascarar
            import re
            
            # Enmascarar matrículas (6-8 dígitos)
            content = re.sub(r'"matricola":\s*"(\d{2})\d{4,6}"', r'"matricola": "\1****"', content)
            
            # Enmascarar contraseñas
            content = re.sub(r'"password":\s*"[^"]*"', r'"password": "***MASKED***"', content)
            content = re.sub(r'"contrasena":\s*"[^"]*"', r'"contrasena": "***MASKED***"', content)
            
            # Enmascarar user_id si es matrícula
            content = re.sub(r'"user_id":\s*"(\d{2})\d{4,6}"', r'"user_id": "\1****"', content)
            
            # Escribir contenido enmascarado
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)
                
            self.logger.info(f"Contenido enmascarado en: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error enmascarando {file_path}: {e}")


def setup_automatic_cleanup():
    """Configurar limpieza automática según configuración del entorno"""
    retention_days = int(os.getenv('LOG_RETENTION_DAYS', '7'))
    cleaner = LogCleaner(retention_days=retention_days)
    
    # Limpiar logs antiguos
    cleaner.clean_old_logs()
    
    # Si está habilitado el enmascaramiento, procesar logs existentes
    if os.getenv('MASK_CREDENTIALS', 'True').lower() == 'true':
        cleaner.mask_existing_logs()
    
    return cleaner


if __name__ == "__main__":
    # Ejecutar limpieza manual
    cleaner = setup_automatic_cleanup()
    print("Limpieza de logs completada")
