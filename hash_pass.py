import getpass
from werkzeug.security import generate_password_hash

def create_password_hash():
    """
    Herramienta de utilidad para crear un hash de contraseña seguro para los administradores.
    Pide una contraseña de forma segura, la confirma y muestra el hash resultante.
    """
    print("--- Generador de Hash de Contraseña para Administradores ---")
    
    # getpass.getpass oculta la entrada del usuario para mayor seguridad
    password = getpass.getpass("Introduce la contraseña para el nuevo administrador: ")
    password_confirm = getpass.getpass("Confirma la contraseña: ")

    if not password or not password_confirm:
        print("\nError: La contraseña no puede estar vacía.")
        return

    if password != password_confirm:
        print("\nError: Las contraseñas no coinciden. Inténtalo de nuevo.")
        return

    # Genera el hash usando un método seguro que incluye un salt aleatorio.
    hashed_password = generate_password_hash(password)

    print("\n¡Hash generado con éxito!")
    print("Copia la siguiente línea y pégala en el campo 'password_hash' del usuario en Firestore:")
    print("-" * 60)
    print(hashed_password)
    print("-" * 60)

if __name__ == '__main__':
    create_password_hash()