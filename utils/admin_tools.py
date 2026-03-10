"""
AdminTools - Herramientas administrativas para PUG
Utilidades para gestión de administradores y mantenimiento del sistema
"""

import getpass
import logging
from werkzeug.security import generate_password_hash
from typing import Optional

logger = logging.getLogger(__name__)

class AdminPasswordManager:
    """Gestor de contraseñas para administradores"""
    
    @staticmethod
    def create_password_hash(password: Optional[str] = None) -> Optional[str]:
        """
        Crear un hash de contraseña seguro para administradores
        
        Args:
            password: Contraseña opcional (si no se proporciona, se solicita)
            
        Returns:
            str: Hash de contraseña o None si hay error
        """
        try:
            if not password:
                print("--- Generador de Hash de Contraseña para Administradores ---")
                password = getpass.getpass("Introduce la contraseña para el nuevo administrador: ")
                password_confirm = getpass.getpass("Confirma la contraseña: ")

                if not password or not password_confirm:
                    print("\n❌ Error: La contraseña no puede estar vacía.")
                    return None

                if password != password_confirm:
                    print("\n❌ Error: Las contraseñas no coinciden. Inténtalo de nuevo.")
                    return None

            # Generar hash seguro
            hashed_password = generate_password_hash(password)

            if not password:  # Solo mostrar si se solicitó interactivamente
                print("\n✅ ¡Hash generado con éxito!")
                print("Copia la siguiente línea y pégala en el campo 'password_hash' del usuario en Firestore:")
                print("-" * 80)
                print(hashed_password)
                print("-" * 80)

            logger.info("Hash de contraseña generado exitosamente")
            return hashed_password

        except Exception as e:
            logger.error(f"Error generando hash de contraseña: {e}")
            print(f"\n❌ Error generando hash: {e}")
            return None
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, list[str]]:
        """
        Validar la fortaleza de una contraseña
        
        Args:
            password: Contraseña a validar
            
        Returns:
            tuple: (es_válida, lista_de_errores)
        """
        errors = []
        
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres")
        
        if not any(c.isupper() for c in password):
            errors.append("La contraseña debe tener al menos una letra mayúscula")
        
        if not any(c.islower() for c in password):
            errors.append("La contraseña debe tener al menos una letra minúscula")
        
        if not any(c.isdigit() for c in password):
            errors.append("La contraseña debe tener al menos un número")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("La contraseña debe tener al menos un carácter especial")
        
        return len(errors) == 0, errors

class SystemMaintenance:
    """Herramientas de mantenimiento del sistema"""
    
    @staticmethod
    def cleanup_old_logs(days: int = 7) -> bool:
        """
        Limpiar logs antiguos del sistema
        
        Args:
            days: Días de antigüedad para considerar logs como antiguos
            
        Returns:
            bool: True si la limpieza fue exitosa
        """
        try:
            from .log_cleaner import LogCleaner
            cleaner = LogCleaner()
            return cleaner.clean_logs_older_than(days)
        except Exception as e:
            logger.error(f"Error limpiando logs: {e}")
            return False
    
    @staticmethod
    def verify_storage_connection() -> bool:
        """
        Verificar el acceso al almacenamiento local (datos/)
        
        Returns:
            bool: True si es accesible
        """
        try:
            from core.obsidian_manager import ObsidianManager
            storage = ObsidianManager()
            return storage.test_connection()
        except Exception as e:
            logger.error(f"Error verificando almacenamiento: {e}")
            return False

def main():
    """Función principal para uso desde línea de comandos"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "password":
            AdminPasswordManager.create_password_hash()
        elif command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            if SystemMaintenance.cleanup_old_logs(days):
                print(f"✅ Logs anteriores a {days} días limpiados exitosamente")
            else:
                print("❌ Error limpiando logs")
        elif command == "test-storage":
            if SystemMaintenance.verify_storage_connection():
                print("✅ Almacenamiento local accesible")
            else:
                print("❌ Error accediendo al almacenamiento")
        else:
            print("Comandos disponibles:")
            print("  password     - Generar hash de contraseña")
            print("  cleanup [días] - Limpiar logs antiguos")
            print("  test-storage - Verificar almacenamiento local")
    else:
        # Comportamiento por defecto: generar contraseña
        AdminPasswordManager.create_password_hash()

if __name__ == '__main__':
    main()
