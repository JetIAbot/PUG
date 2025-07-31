"""
Script para verificar las correcciones de interfaz
"""

import requests
from bs4 import BeautifulSoup

def test_student_page():
    """Verificar que la página de estudiantes se vea correctamente"""
    print("Verificando página de estudiantes...")
    
    try:
        response = requests.get("http://127.0.0.1:5000/")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verificar título
            title = soup.find('h1', class_='brand-title')
            if title:
                print("✅ Título encontrado en página de estudiantes")
            else:
                print("❌ Título no encontrado en página de estudiantes")
            
            # Verificar alerta informativa
            alert = soup.find('div', class_='alert alert-primary')
            if alert:
                print("✅ Alerta informativa agregada correctamente")
            else:
                print("⚠️ Alerta informativa no encontrada")
                
        else:
            print(f"❌ Error cargando página: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_admin_page():
    """Verificar que el panel de admin se vea correctamente"""
    print("\nVerificando panel de administrador...")
    
    session = requests.Session()
    
    try:
        # Hacer login
        login_data = {'username': 'admin', 'password': 'admin123'}
        login_response = session.post("http://127.0.0.1:5000/admin/login", data=login_data, allow_redirects=False)
        
        if login_response.status_code == 302:
            # Obtener página de admin
            admin_response = session.get("http://127.0.0.1:5000/admin")
            
            if admin_response.status_code == 200:
                soup = BeautifulSoup(admin_response.text, 'html.parser')
                
                # Verificar mensaje de bienvenida
                user_info = soup.find('div', class_='user-info')
                if user_info:
                    bienvenida_text = user_info.get_text()
                    if "Bienvenido" in bienvenida_text and "()" not in bienvenida_text:
                        print("✅ Mensaje de bienvenida corregido correctamente")
                    else:
                        print("❌ Mensaje de bienvenida aún tiene problemas")
                        print(f"Texto encontrado: {bienvenida_text.strip()}")
                else:
                    print("❌ Elemento user-info no encontrado")
            else:
                print(f"❌ Error accediendo al admin: {admin_response.status_code}")
        else:
            print("❌ Error en login")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("🔍 VERIFICANDO CORRECCIONES DE INTERFAZ")
    print("=" * 50)
    
    test_student_page()
    test_admin_page()
    
    print("\n" + "=" * 50)
    print("✅ Verificación completada")
    print("\n🌐 Prueba manual:")
    print("- Página estudiantes: http://127.0.0.1:5000/")
    print("- Página admin: http://127.0.0.1:5000/admin/login")

if __name__ == "__main__":
    main()
