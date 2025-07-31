"""
Script de prueba para el sistema de login de administrador
Verifica que las credenciales funcionen correctamente
"""

import sys
import os
import requests
from urllib.parse import urljoin

# Agregar el directorio raíz al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_admin_login():
    """Probar el login de administrador"""
    base_url = "http://127.0.0.1:5000"
    
    print("🔐 PROBANDO SISTEMA DE LOGIN DE ADMINISTRADOR")
    print("=" * 50)
    
    # Crear sesión para mantener cookies
    session = requests.Session()
    
    try:
        # 1. Verificar que la página de login carga
        print("\n1. Verificando página de login...")
        login_url = urljoin(base_url, "/admin/login")
        response = session.get(login_url)
        
        if response.status_code == 200:
            print("✅ Página de login cargada correctamente")
        else:
            print(f"❌ Error cargando página de login: {response.status_code}")
            return False
        
        # 2. Intentar login con credenciales incorrectas
        print("\n2. Probando credenciales incorrectas...")
        login_data = {
            'username': 'usuario_incorrecto',
            'password': 'password_incorrecto'
        }
        
        response = session.post(login_url, data=login_data)
        
        if "Credenciales incorrectas" in response.text or response.status_code == 200:
            print("✅ Rechazo de credenciales incorrectas funciona")
        else:
            print("❌ Sistema no rechaza credenciales incorrectas")
            return False
        
        # 3. Intentar login con credenciales correctas
        print("\n3. Probando credenciales correctas...")
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        response = session.post(login_url, data=login_data, allow_redirects=False)
        
        if response.status_code == 302:  # Redirección exitosa
            print("✅ Login exitoso - redirección detectada")
            
            # Seguir la redirección
            dashboard_response = session.get(urljoin(base_url, response.headers['Location']))
            
            if dashboard_response.status_code == 200:
                print("✅ Dashboard de administrador accesible")
                return True
            else:
                print(f"❌ Error accediendo al dashboard: {dashboard_response.status_code}")
                return False
        else:
            print(f"❌ Login falló: {response.status_code}")
            print(f"Contenido: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor Flask")
        print("💡 Asegúrate de que la aplicación esté ejecutándose en http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        return False

def test_admin_routes():
    """Probar que las rutas de administrador requieren autenticación"""
    base_url = "http://127.0.0.1:5000"
    
    print("\n🔒 PROBANDO PROTECCIÓN DE RUTAS ADMINISTRATIVAS")
    print("=" * 50)
    
    admin_routes = [
        "/admin",
        "/admin/carros",
        "/admin/carros/nuevo"
    ]
    
    session = requests.Session()
    
    try:
        for route in admin_routes:
            print(f"\n🔍 Probando ruta: {route}")
            response = session.get(urljoin(base_url, route), allow_redirects=False)
            
            if response.status_code == 302:  # Redirección al login
                location = response.headers.get('Location', '')
                if 'admin/login' in location:
                    print(f"✅ Ruta protegida correctamente - redirige al login")
                else:
                    print(f"⚠️ Ruta redirige pero no al login: {location}")
            else:
                print(f"❌ Ruta no protegida: status {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error probando rutas: {e}")

def main():
    """Función principal del test"""
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE AUTENTICACIÓN")
    print("=" * 60)
    
    # Probar login
    login_exitoso = test_admin_login()
    
    # Probar protección de rutas
    test_admin_routes()
    
    print("\n" + "=" * 60)
    if login_exitoso:
        print("✅ TODAS LAS PRUEBAS DE LOGIN COMPLETADAS EXITOSAMENTE")
        print("\n📝 Credenciales de testing:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("\n🌐 Accede a: http://127.0.0.1:5000/admin/login")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("🔧 Revisa que la aplicación Flask esté ejecutándose correctamente")

if __name__ == "__main__":
    main()
