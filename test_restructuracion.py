"""
Test para verificar la restructuración del proyecto PUG
Valida que todos los módulos y funciones sean accesibles
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_estructura_archivos():
    """Verificar que la nueva estructura de archivos existe"""
    print("1. Verificando estructura de archivos...")
    
    archivos_necesarios = [
        'config.py',
        'app.py',
        'core/__init__.py',
        'core/student_scheduler.py',
        'core/portal_extractor.py',
        'core/demo_generator.py',
        'core/firebase_manager.py',
        'core/data_processor.py',
        'utils/__init__.py',
        'utils/constants.py',
        'utils/validators.py',
        'utils/logger_config.py',
        'utils/admin_tools.py',
        'utils/log_cleaner.py'
    ]
    
    faltantes = []
    for archivo in archivos_necesarios:
        if not os.path.exists(archivo):
            faltantes.append(archivo)
    
    if faltantes:
        print(f"   ❌ Archivos faltantes: {faltantes}")
        return False
    else:
        print(f"   ✅ Todos los archivos necesarios existen ({len(archivos_necesarios)} archivos)")
        return True

def test_imports_config():
    """Verificar que config.py se importa correctamente"""
    print("2. Verificando config.py...")
    try:
        import config
        config_instance = config.get_config()
        print(f"   ✅ Config cargado: {config_instance.__class__.__name__}")
        return True
    except Exception as e:
        print(f"   ❌ Error importando config: {e}")
        return False

def test_imports_utils():
    """Verificar que los módulos utils se importan correctamente"""
    print("3. Verificando módulos utils...")
    try:
        from utils.constants import ORDEN_BLOQUES, DIAS_SEMANA
        from utils.validators import validar_matricola
        from utils.logger_config import setup_logging
        
        print(f"   ✅ Constants: {len(ORDEN_BLOQUES)} bloques, {len(DIAS_SEMANA)} días")
        print("   ✅ Validators y logger importados correctamente")
        return True
    except Exception as e:
        print(f"   ❌ Error importando utils: {e}")
        return False

def test_imports_core():
    """Verificar que los módulos core se importan correctamente"""
    print("4. Verificando módulos core...")
    try:
        from core.student_scheduler import StudentScheduler
        from core.portal_extractor import PortalExtractor
        from core.demo_generator import DemoDataGenerator
        from core.firebase_manager import FirebaseManager
        from core.data_processor import DataProcessor
        
        print("   ✅ Todos los módulos core importados correctamente")
        return True
    except Exception as e:
        print(f"   ❌ Error importando core: {e}")
        return False

def test_funcionalidad_basica():
    """Verificar funcionalidad básica de los módulos principales"""
    print("5. Verificando funcionalidad básica...")
    try:
        from core.demo_generator import DemoDataGenerator
        generator = DemoDataGenerator()
        
        # Test demo data generation
        horario_demo = generator.generar_horario_demo(3)
        if len(horario_demo) > 0:
            print(f"   ✅ Demo generator funcional: {len(horario_demo)} clases generadas")
        else:
            print("   ⚠️  Demo generator no generó clases")
            return False
        
        # Test configuration
        import config
        config_instance = config.get_config()
        if hasattr(config_instance, 'SECRET_KEY'):
            print("   ✅ Configuración funcional")
        else:
            print("   ❌ Configuración no tiene SECRET_KEY")
            return False
        
        return True
    except Exception as e:
        print(f"   ❌ Error en funcionalidad básica: {e}")
        return False

def main():
    """Ejecutar todos los tests"""
    print("=== TEST DE RESTRUCTURACIÓN PUG ===\n")
    
    tests = [
        test_estructura_archivos,
        test_imports_config,
        test_imports_utils,
        test_imports_core,
        test_funcionalidad_basica
    ]
    
    resultados = []
    for test in tests:
        resultado = test()
        resultados.append(resultado)
        print()
    
    exitosos = sum(resultados)
    total = len(resultados)
    
    print(f"=== RESUMEN ===")
    print(f"Tests exitosos: {exitosos}/{total}")
    
    if exitosos == total:
        print("🎉 RESTRUCTURACIÓN COMPLETADA EXITOSAMENTE")
    else:
        print("⚠️  Hay problemas que necesitan resolución")
    
    return exitosos == total

if __name__ == "__main__":
    main()
