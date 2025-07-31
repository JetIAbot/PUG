"""
Script de prueba simple para el sistema de login de administrador
"""

import sys
import os
import requests
from urllib.parse import urljoin

def test_admin_login_simple():
    """Probar el login de administrador"""
    base_url = "http://127.0.0.1:5000"
    
    print("PROBANDO SISTEMA DE LOGIN DE ADMINISTRADOR")
    print("=" * 50)
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    try:
        # 1. Verificar que la página de login carga
        print("\n1. Verificando pagina de login...")
        login_url = urljoin(base_url, "/admin/login")
        response = session.get(login_url)
        
        if response.status_code == 200:
            print("OK - Pagina de login cargada correctamente")
        else:
            print(f"ERROR - Error cargando pagina de login: {response.status_code}")
            return False
        
        # 2. Intentar login con credenciales correctas
        print("\n2. Probando credenciales correctas...")
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = session.post(login_url, data=login_data, allow_redirects=False)
        
        if response.status_code == 302:  # Redirección exitosa
            print("OK - Login exitoso - redireccion detectada")
            
            # Seguir la redirección
            dashboard_response = session.get(urljoin(base_url, response.headers['Location']))
            
            if dashboard_response.status_code == 200:
                print("OK - Dashboard de administrador accesible")
                return True
            else:
                print(f"ERROR - Error accediendo al dashboard: {dashboard_response.status_code}")
                return False
        else:
            print(f"ERROR - Login fallo: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("ERROR - No se puede conectar al servidor Flask")
        print("SOLUCION - Asegurate de que la aplicacion este ejecutandose en http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"ERROR - Error durante las pruebas: {e}")
        return False

def main():
    """Función principal del test"""
    print("INICIANDO PRUEBAS DEL SISTEMA DE AUTENTICACION")
    print("=" * 60)
    
    # Probar login
    login_exitoso = test_admin_login_simple()
    
    print("\n" + "=" * 60)
    if login_exitoso:
        print("EXITO - TODAS LAS PRUEBAS DE LOGIN COMPLETADAS")
        print("\nCredenciales de testing:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("\nAccede a: http://127.0.0.1:5000/admin/login")
    else:
        print("ERROR - ALGUNAS PRUEBAS FALLARON")
        print("Revisa que la aplicacion Flask este ejecutandose correctamente")

if __name__ == "__main__":
    main()
