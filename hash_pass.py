from werkzeug.security import generate_password_hash
import argparse

def hash_password(password):
    """Genera un hash para la contraseña proporcionada."""
    return generate_password_hash(password)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Genera un hash de contraseña seguro para almacenar en la base de datos.')
    parser.add_argument('password', help='La contraseña para la que se generará el hash.')
    
    args = parser.parse_args()
    
    hashed_password = hash_password(args.password)
    print("Copia y pega el siguiente hash en el campo 'password_hash' de tu usuario en Firestore:")
    print(hashed_password)
