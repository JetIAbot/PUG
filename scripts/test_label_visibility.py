"""
Script para verificar la visibilidad de labels en las interfaces
"""

import requests
from bs4 import BeautifulSoup

def test_student_labels():
    """Verificar que los labels de estudiantes sean visibles"""
    print("Verificando labels en página de estudiantes...")
    
    try:
        response = requests.get("http://127.0.0.1:5000/")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verificar label de matrícula
            matricula_label = soup.find('label', {'for': 'matricola'})
            if matricula_label and 'Número de Matrícula' in matricula_label.get_text():
                print("✅ Label 'Número de Matrícula' encontrado")
            else:
                print("❌ Label 'Número de Matrícula' no encontrado")
            
            # Verificar label de contraseña
            password_label = soup.find('label', {'for': 'password'})
            if password_label and 'Contraseña' in password_label.get_text():
                print("✅ Label 'Contraseña' encontrado")
            else:
                print("❌ Label 'Contraseña' no encontrado")
                
            # Verificar CSS personalizado
            if 'form-label' in response.text and 'color: #2c3e50' in response.text:
                print("✅ CSS personalizado para labels aplicado")
            else:
                print("⚠️ CSS personalizado no detectado")
                
        else:
            print(f"❌ Error cargando página: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_admin_labels():
    """Verificar que los labels de admin sean visibles"""
    print("\nVerificando labels en página de administrador...")
    
    try:
        response = requests.get("http://127.0.0.1:5000/admin/login")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Verificar label de usuario
            username_label = soup.find('label', {'for': 'username'})
            if username_label and 'Usuario Administrador' in username_label.get_text():
                print("✅ Label 'Usuario Administrador' encontrado")
            else:
                print("❌ Label 'Usuario Administrador' no encontrado")
            
            # Verificar label de contraseña
            password_label = soup.find('label', {'for': 'password'})
            if password_label and 'Contraseña de Administrador' in password_label.get_text():
                print("✅ Label 'Contraseña de Administrador' encontrado")
            else:
                print("❌ Label 'Contraseña de Administrador' no encontrado")
                
            # Verificar CSS personalizado
            if 'form-label' in response.text and 'color: #2c3e50' in response.text:
                print("✅ CSS personalizado para labels aplicado")
            else:
                print("⚠️ CSS personalizado no detectado")
                
        else:
            print(f"❌ Error cargando página: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_css_styles():
    """Verificar que el archivo CSS tenga los estilos correctos"""
    print("\nVerificando archivo CSS...")
    
    try:
        response = requests.get("http://127.0.0.1:5000/static/css/validation.css")
        if response.status_code == 200:
            css_content = response.text
            
            if '.form-label' in css_content:
                print("✅ Clase .form-label encontrada en CSS")
            else:
                print("❌ Clase .form-label no encontrada en CSS")
                
            if 'color: #2c3e50' in css_content:
                print("✅ Color mejorado aplicado en CSS")
            else:
                print("❌ Color mejorado no encontrado en CSS")
                
            if 'font-weight: 600' in css_content or 'font-weight: 700' in css_content:
                print("✅ Font-weight aplicado en CSS")
            else:
                print("❌ Font-weight no encontrado en CSS")
                
        else:
            print(f"❌ Error cargando CSS: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("🔍 VERIFICANDO VISIBILIDAD DE LABELS")
    print("=" * 50)
    
    test_student_labels()
    test_admin_labels()
    test_css_styles()
    
    print("\n" + "=" * 50)
    print("✅ Verificación completada")
    print("\n🌐 Prueba manual:")
    print("- Página estudiantes: http://127.0.0.1:5000/")
    print("- Página admin: http://127.0.0.1:5000/admin/login")
    print("\n💡 Los labels ahora deberían ser:")
    print("- Color más oscuro (#2c3e50)")
    print("- Font-weight más fuerte (700)")
    print("- Tamaño ligeramente mayor (1.1rem)")
    print("- Con sombra de texto sutil")

if __name__ == "__main__":
    main()
