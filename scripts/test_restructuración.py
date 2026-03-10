"""
Script de prueba para verificar la restructuración del proyecto PUG
Verifica que todos los módulos se importen correctamente y que el sistema funcione
"""

import sys
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_imports():
    """Probar que todos los imports funcionen correctamente"""
    logger.info("🧪 PROBANDO IMPORTS DE MÓDULOS RESTRUCTURADOS")
    logger.info("=" * 60)
    
    errores = []
    
    # Probar imports de core
    try:
        from core.student_scheduler import StudentScheduler
        logger.info("✅ core.student_scheduler - IMPORT OK")
    except Exception as e:
        errores.append(f"❌ core.student_scheduler - ERROR: {e}")
    
    try:
        from core.obsidian_manager import ObsidianManager
        logger.info("✅ core.obsidian_manager - IMPORT OK")
    except Exception as e:
        errores.append(f"❌ core.obsidian_manager - ERROR: {e}")
    
    try:
        from core.portal_extractor import PortalExtractor
        logger.info("✅ core.portal_extractor - IMPORT OK")
    except Exception as e:
        errores.append(f"❌ core.portal_extractor - ERROR: {e}")
    
    try:
        from core.demo_generator import DemoDataGenerator
        logger.info("✅ core.demo_generator - IMPORT OK")
    except Exception as e:
        errores.append(f"❌ core.demo_generator - ERROR: {e}")
    
    try:
        from core.data_processor import DataProcessor
        logger.info("✅ core.data_processor - IMPORT OK")
    except Exception as e:
        errores.append(f"❌ core.data_processor - ERROR: {e}")
    
    # Probar imports de utils
    try:
        from utils.constants import ORDEN_BLOQUES, BLOQUES_A_HORAS
        logger.info("✅ utils.constants - IMPORT OK")
    except Exception as e:
        errores.append(f"❌ utils.constants - ERROR: {e}")
    
    try:
        from utils.validators import FormValidator
        logger.info("✅ utils.validators - IMPORT OK")
    except Exception as e:
        errores.append(f"❌ utils.validators - ERROR: {e}")
    
    try:
        from utils.admin_tools import AdminPasswordManager
        logger.info("✅ utils.admin_tools - IMPORT OK")
    except Exception as e:
        errores.append(f"❌ utils.admin_tools - ERROR: {e}")
    
    # Probar configuración
    try:
        from config import get_config
        config = get_config()
        logger.info("✅ config - IMPORT OK")
    except Exception as e:
        errores.append(f"❌ config - ERROR: {e}")
    
    return errores

def test_demo_system():
    """Probar el sistema de generación de datos demo"""
    logger.info("\n🎭 PROBANDO SISTEMA DE DATOS DEMO")
    logger.info("=" * 60)
    
    try:
        from core.demo_generator import DemoDataGenerator
        
        # Crear generador
        generator = DemoDataGenerator()
        
        # Probar generación de horario
        horario = generator.generar_horario_demo(3)
        logger.info(f"✅ Horario demo generado: {len(horario)} clases")
        
        # Probar generación de materias
        materias = generator.generar_materias_demo(3)
        logger.info(f"✅ Materias demo generadas: {len(materias)} materias")
        
        # Probar generación de perfil
        perfil = generator.generar_perfil_demo("172934")
        logger.info(f"✅ Perfil demo generado: {perfil['nome']} {perfil['cognome']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en sistema demo: {e}")
        return False

def test_constants():
    """Probar que las constantes estén disponibles"""
    logger.info("\n📋 PROBANDO CONSTANTES DEL SISTEMA")
    logger.info("=" * 60)
    
    try:
        from utils.constants import (
            ORDEN_BLOQUES, BLOQUES_A_HORAS, DIAS_SEMANA,
            DEMO_NAMES, DEMO_MATERIAS, PORTAL_SELECTORS
        )
        
        logger.info(f"✅ ORDEN_BLOQUES: {len(ORDEN_BLOQUES)} bloques")
        logger.info(f"✅ BLOQUES_A_HORAS: {len(BLOQUES_A_HORAS)} horarios")
        logger.info(f"✅ DIAS_SEMANA: {len(DIAS_SEMANA)} días")
        logger.info(f"✅ DEMO_NAMES: {len(DEMO_NAMES['nombres'])} nombres")
        logger.info(f"✅ DEMO_MATERIAS: {len(DEMO_MATERIAS)} materias")
        logger.info(f"✅ PORTAL_SELECTORS: {len(PORTAL_SELECTORS)} secciones")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en constantes: {e}")
        return False

def test_compatibility_functions():
    """Probar funciones de compatibilidad con el sistema anterior"""
    logger.info("\n🔄 PROBANDO FUNCIONES DE COMPATIBILIDAD")
    logger.info("=" * 60)
    
    try:
        # Probar funciones de compatibilidad en student_scheduler
        from core.student_scheduler import inicializar_firebase, realizar_matchmaking
        logger.info("✅ Funciones de compatibilidad de student_scheduler disponibles")
        
        # Probar funciones de compatibilidad en firebase_manager
        from core.firebase_manager import guardar_en_firebase
        logger.info("✅ Funciones de compatibilidad de firebase_manager disponibles")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en funciones de compatibilidad: {e}")
        return False

def test_file_structure():
    """Verificar que la estructura de archivos sea correcta"""
    logger.info("\n📁 VERIFICANDO ESTRUCTURA DE ARCHIVOS")
    logger.info("=" * 60)
    
    archivos_requeridos = [
        "app.py",
        "config.py",
        "core/__init__.py",
        "core/student_scheduler.py",
        "core/firebase_manager.py",
        "core/portal_extractor.py",
        "core/demo_generator.py",
        "core/data_processor.py",
        "utils/__init__.py",
        "utils/constants.py",
        "utils/validators.py",
        "utils/admin_tools.py",
        "utils/logger_config.py",
        "utils/log_cleaner.py"
    ]
    
    archivos_faltantes = []
    
    for archivo in archivos_requeridos:
        if os.path.exists(archivo):
            logger.info(f"✅ {archivo}")
        else:
            archivos_faltantes.append(archivo)
            logger.error(f"❌ {archivo} - NO ENCONTRADO")
    
    return len(archivos_faltantes) == 0

def main():
    """Ejecutar todas las pruebas de restructuración"""
    logger.info("🚀 INICIANDO PRUEBAS DE RESTRUCTURACIÓN PUG")
    logger.info("=" * 60)
    logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    resultados = []
    
    # Ejecutar pruebas
    errores_imports = test_imports()
    resultados.append(("Imports de módulos", len(errores_imports) == 0))
    
    if errores_imports:
        logger.error("\n❌ ERRORES DE IMPORT ENCONTRADOS:")
        for error in errores_imports:
            logger.error(f"   {error}")
    
    demo_ok = test_demo_system()
    resultados.append(("Sistema de datos demo", demo_ok))
    
    constants_ok = test_constants()
    resultados.append(("Constantes del sistema", constants_ok))
    
    compatibility_ok = test_compatibility_functions()
    resultados.append(("Funciones de compatibilidad", compatibility_ok))
    
    structure_ok = test_file_structure()
    resultados.append(("Estructura de archivos", structure_ok))
    
    # Resumen final
    logger.info("\n" + "=" * 60)
    logger.info("📊 RESUMEN DE PRUEBAS DE RESTRUCTURACIÓN")
    logger.info("=" * 60)
    
    total_pruebas = len(resultados)
    pruebas_exitosas = sum(1 for _, resultado in resultados if resultado)
    
    for nombre, resultado in resultados:
        status = "✅ PASS" if resultado else "❌ FAIL"
        logger.info(f"{status} - {nombre}")
    
    logger.info("=" * 60)
    logger.info(f"🎯 Resultado: {pruebas_exitosas}/{total_pruebas} pruebas exitosas")
    
    if pruebas_exitosas == total_pruebas:
        logger.info("🎉 ¡RESTRUCTURACIÓN COMPLETADA EXITOSAMENTE!")
        logger.info("✅ Todos los módulos están funcionando correctamente")
        logger.info("✅ La nueva estructura está operativa")
        return True
    else:
        logger.error("⚠️  RESTRUCTURACIÓN INCOMPLETA")
        logger.error("❌ Algunos módulos necesitan revisión")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
