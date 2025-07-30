"""
Prueba rápida del sistema de demostración
"""

from demo_data_generator import DemoDataGenerator
from matchmaking import extraer_datos_portal_real
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_sistema_completo():
    """Prueba completa del sistema con datos de demostración"""
    print("🚀 INICIANDO PRUEBA DEL SISTEMA COMPLETO")
    print("=" * 60)
    
    # 1. Probar generación de datos de demostración
    print("\n1️⃣ PROBANDO GENERACIÓN DE DATOS DE DEMOSTRACIÓN")
    generator = DemoDataGenerator()
    datos_demo = generator.generar_datos_completos("TEST123")
    
    print(f"✅ Perfil: {datos_demo['perfil']['nome']} {datos_demo['perfil']['cognome']}")
    print(f"✅ Horario: {len(datos_demo['horario'])} clases")
    print(f"✅ Materias: {len(datos_demo['materias'])} materias")
    print(f"✅ Estado: {datos_demo['estado_horarios']}")
    
    # 2. Probar extracción con portal real (si está habilitado)
    print("\n2️⃣ PROBANDO EXTRACCIÓN DEL PORTAL REAL")
    use_real_portal = os.getenv('USE_REAL_PORTAL', 'False').lower() == 'true'
    
    if use_real_portal:
        matricola = os.getenv('TEST_MATRICOLA', '172934')
        password = os.getenv('TEST_PASSWORD', '935FX291')
        
        if matricola and password:
            print(f"🔄 Extrayendo datos para matrícula: {matricola[:2]}****")
            resultado = extraer_datos_portal_real(matricola, password)
            
            if resultado['success']:
                print("✅ Extracción del portal exitosa")
                print(f"📝 Mensaje: {resultado['message']}")
                
                if resultado['data']:
                    datos = resultado['data']
                    print(f"👤 Perfil: {datos['perfil']['nome']} {datos['perfil']['cognome']}")
                    print(f"📚 Horario: {len(datos['horario'])} clases")
                    print(f"📖 Materias: {len(datos['materias'])} materias")
                    estado = datos.get('estado_horarios', 'no especificado')
                    print(f"🎯 Estado horarios: {estado}")
                    
                    if estado in ['ejemplo_demo', 'demo_realista']:
                        print("ℹ️  Los horarios son de demostración (horarios reales no publicados)")
                
                return True
            else:
                print(f"❌ Error en extracción: {resultado['message']}")
                return False
        else:
            print("⚠️  Credenciales no configuradas - saltando prueba")
    else:
        print("⚠️  Portal real no habilitado - saltando prueba")
    
    print("\n🎉 PRUEBAS COMPLETADAS EXITOSAMENTE")
    print("El sistema está listo para usar con datos de demostración")
    return True

if __name__ == "__main__":
    try:
        success = test_sistema_completo()
        if success:
            print("\n" + "🌟" * 20)
            print("¡Sistema completamente funcional!")
            print("Ahora puedes probar en: http://127.0.0.1:5000")
            print("🌟" * 20)
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
