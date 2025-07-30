"""
Script de prueba para el sistema completo con datos de demostración
"""

import os
import sys

# Agregar el directorio src al path para importaciones
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dotenv import load_dotenv
from demo_data_generator import DemoDataGenerator, crear_datos_demo_firebase
from matchmaking import inicializar_firebase, realizar_matchmaking, extraer_datos_portal_real
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_demo_data_generation():
    """Probar la generación de datos de demostración"""
    print("\n=== PRUEBA 1: GENERACIÓN DE DATOS DE DEMOSTRACIÓN ===")
    
    generator = DemoDataGenerator()
    
    # Generar datos para un estudiante
    datos_estudiante = generator.generar_datos_completos("TEST123")
    
    print(f"✅ Perfil generado: {datos_estudiante['perfil']['nome']} {datos_estudiante['perfil']['cognome']}")
    print(f"✅ Horario: {len(datos_estudiante['horario'])} clases")
    print(f"✅ Materias: {len(datos_estudiante['materias'])} materias")
    print(f"✅ Estado: {datos_estudiante['estado_horarios']}")
    
    return True

def test_firebase_demo_data():
    """Probar la creación de datos demo en Firebase"""
    print("\n=== PRUEBA 2: DATOS DEMO EN FIREBASE ===")
    
    try:
        db = inicializar_firebase()
        if not db:
            print("❌ No se pudo conectar a Firebase")
            return False
        
        # Crear algunos estudiantes de demostración
        success = crear_datos_demo_firebase(db, num_estudiantes=3)
        
        if success:
            print("✅ Datos de demostración creados en Firebase")
        else:
            print("❌ Error creando datos demo en Firebase")
            
        return success
        
    except Exception as e:
        print(f"❌ Error en prueba Firebase: {e}")
        return False

def test_matchmaking_with_demo():
    """Probar el algoritmo de matchmaking con datos demo"""
    print("\n=== PRUEBA 3: MATCHMAKING CON DATOS DEMO ===")
    
    try:
        # Ejecutar matchmaking
        resultado = realizar_matchmaking()
        
        if "Error:" in resultado:
            print(f"❌ Error en matchmaking: {resultado}")
            return False
        
        print("✅ Matchmaking ejecutado exitosamente")
        print("\n--- RESULTADOS DEL MATCHMAKING ---")
        print(resultado)
        return True
        
    except Exception as e:
        print(f"❌ Error en matchmaking: {e}")
        return False

def test_portal_extraction_demo():
    """Probar la extracción con el portal real usando datos demo"""
    print("\n=== PRUEBA 4: EXTRACCIÓN DEL PORTAL (MODO DEMO) ===")
    
    # Verificar configuración
    load_dotenv()
    use_real_portal = os.getenv('USE_REAL_PORTAL', 'False').lower() == 'true'
    
    if not use_real_portal:
        print("⚠️  Portal real no habilitado - saltando prueba")
        return True
    
    try:
        # Usar credenciales reales (deben estar en .env)
        test_matricola = os.getenv('TEST_MATRICOLA', '172934')
        test_password = os.getenv('TEST_PASSWORD', '935FX291')
        
        if not test_matricola or not test_password:
            print("⚠️  Credenciales de prueba no configuradas - saltando prueba")
            return True
        
        print(f"🔄 Probando extracción para matrícula: {test_matricola[:2]}****")
        
        resultado = extraer_datos_portal_real(test_matricola, test_password)
        
        if resultado['success']:
            print("✅ Extracción del portal exitosa")
            print(f"📝 Mensaje: {resultado['message']}")
            
            if resultado['data']:
                datos = resultado['data']
                print(f"👤 Perfil: {datos['perfil']['nome']} {datos['perfil']['cognome']}")
                print(f"📚 Horario: {len(datos['horario'])} clases")
                print(f"📖 Materias: {len(datos['materias'])} materias")
                print(f"🎯 Estado horarios: {datos.get('estado_horarios', 'no especificado')}")
                
                if datos.get('estado_horarios') == 'ejemplo_demo':
                    print("ℹ️  Los horarios mostrados son de demostración (horarios reales no publicados)")
            
            return True
        else:
            print(f"❌ Error en extracción: {resultado['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de extracción: {e}")
        return False

def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA COMPLETO")
    print("=" * 60)
    
    tests = [
        ("Generación de datos demo", test_demo_data_generation),
        ("Firebase con datos demo", test_firebase_demo_data),
        ("Matchmaking con datos demo", test_matchmaking_with_demo),
        ("Extracción del portal (modo demo)", test_portal_extraction_demo)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error crítico en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado final: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema está listo para usar con datos de demostración.")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar logs para más detalles.")
    
    return passed == total

if __name__ == "__main__":
    # Cargar variables de entorno
    load_dotenv()
    
    # Ejecutar todas las pruebas
    success = run_all_tests()
    
    if success:
        print("\n" + "🌟" * 20)
        print("El sistema está completamente funcional y listo para demostración")
        print("Puedes acceder a http://127.0.0.1:5000 para probar la interfaz web")
        print("🌟" * 20)
    else:
        print("\n" + "⚠️ " * 20)
        print("Hay algunos problemas que necesitan ser resueltos")
        print("⚠️ " * 20)
