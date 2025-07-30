"""
Script de prueba para verificar la conexión al portal real de la universidad
"""
import sys
import os
from dotenv import load_dotenv

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from portal_connector import test_portal_connection, UniversityPortalConnector

def main():
    """Función principal de prueba"""
    print("🌐 PRUEBA DE CONEXIÓN AL PORTAL UNIVERSITARIO REAL")
    print("=" * 60)
    
    # Cargar configuración
    load_dotenv()
    
    # Verificar configuración
    use_real_portal = os.getenv('USE_REAL_PORTAL', 'False').lower() == 'true'
    portal_url = os.getenv('PORTAL_URL', 'No configurada')
    
    print(f"Portal real habilitado: {'✅ SÍ' if use_real_portal else '❌ NO'}")
    print(f"URL del portal: {portal_url}")
    print()
    
    if not use_real_portal:
        print("⚠️  Portal real no está habilitado en configuración")
        print("Para habilitar, asegúrate de que USE_REAL_PORTAL=True en .env")
        return
    
    # Solicitar credenciales
    print("📝 INGRESA TUS CREDENCIALES REALES:")
    print("⚠️  Recuerda que tienes autorización y responsabilidad para usar datos reales")
    
    matricola = input("Matrícula: ").strip()
    password = input("Contraseña: ").strip()
    
    if not matricola or not password:
        print("❌ Credenciales vacías. Cancelando prueba.")
        return
    
    # Ejecutar prueba
    print("\n🔄 Iniciando conexión al portal...")
    print("⏳ Esto puede tomar varios segundos...")
    
    try:
        connector = UniversityPortalConnector()
        resultado = connector.connect_to_portal(matricola, password)
        
        print("\n" + "=" * 60)
        if resultado['success']:
            print("🎉 CONEXIÓN EXITOSA")
            print(f"✅ {resultado['message']}")
            
            if resultado['data']:
                print("\n📊 Datos extraídos:")
                data = resultado['data']
                
                if 'student_info' in data:
                    info = data['student_info']
                    print(f"   👤 Estudiante: {info.get('nome', 'N/A')} {info.get('cognome', 'N/A')}")
                    print(f"   🎓 Matrícula: {info.get('matricola', 'N/A')}")
                
                if 'schedule' in data:
                    horarios = data['schedule']
                    print(f"   📅 Clases encontradas: {len(horarios)}")
                
                if 'courses' in data:
                    materias = data['courses']
                    print(f"   📚 Materias: {len(materias)}")
            
            print("\n✅ La aplicación está lista para usar datos reales")
            
        else:
            print("❌ ERROR EN LA CONEXIÓN")
            print(f"💥 {resultado['message']}")
            
            if resultado.get('errors'):
                print("\n🐛 Errores detallados:")
                for error in resultado['errors']:
                    print(f"   - {error}")
            
            print("\n💡 Sugerencias:")
            print("   - Verificar que las credenciales sean correctas")
            print("   - Comprobar la conexión a internet")
            print("   - Verificar que el portal esté disponible")
            
    except Exception as e:
        print(f"\n💥 ERROR TÉCNICO: {e}")
        print("🔧 Revisar configuración de Selenium y Chrome")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
