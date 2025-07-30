#!/usr/bin/env python3
"""
Script de configuración automática para PUG
Configura el entorno de desarrollo y producción
"""

import os
import subprocess
import sys
import json
from pathlib import Path

def run_command(command, description, check=True):
    """Ejecutar comando con logging"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ {description} completado")
            if result.stdout.strip():
                print(f"   Salida: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False

def check_python_version():
    """Verificar versión de Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ es requerido")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detectado")
    return True

def setup_virtual_environment():
    """Configurar entorno virtual"""
    if not Path("venv").exists():
        run_command("python -m venv venv", "Creando entorno virtual")
    
    # Activar entorno virtual según el SO
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Linux/Mac
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    print(f"💡 Para activar el entorno virtual ejecuta: {activate_cmd}")
    return pip_cmd

def install_dependencies(pip_cmd):
    """Instalar dependencias"""
    commands = [
        (f"{pip_cmd} install --upgrade pip", "Actualizando pip"),
        (f"{pip_cmd} install -r requirements.txt", "Instalando dependencias de Python")
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            return False
    return True

def setup_directories():
    """Crear directorios necesarios"""
    directories = ["logs", "static/uploads", "tests/__pycache__"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Directorio creado: {directory}")

def check_redis():
    """Verificar si Redis está disponible"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis está ejecutándose")
        return True
    except Exception as e:
        print(f"⚠️  Redis no está disponible: {e}")
        print("💡 Para instalar Redis:")
        print("   Windows: Descargar desde https://redis.io/download")
        print("   Ubuntu: sudo apt install redis-server")
        print("   macOS: brew install redis")
        return False

def create_env_file():
    """Crear archivo .env si no existe"""
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Configuración de PUG
FLASK_SECRET_KEY="!&3_;T7UW`X9CA83m}qVJ~J}z\\v£f[rcprU[qKup;:O:D`.Z3`"
FLASK_ENV=development
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
"""
        env_file.write_text(env_content)
        print("✅ Archivo .env creado")
    else:
        print("ℹ️  Archivo .env ya existe")

def create_gitignore():
    """Actualizar .gitignore"""
    gitignore_content = """
# Logs añadidos por las mejoras
logs/
*.log

# Entorno virtual
venv/
env/

# Cache de Python
__pycache__/
*.pyc
*.pyo

# Archivos de prueba
.pytest_cache/
htmlcov/
.coverage

# IDE
.vscode/
.idea/

# Docker
.dockerignore
"""
    
    gitignore_file = Path(".gitignore")
    if gitignore_file.exists():
        existing_content = gitignore_file.read_text()
        if "logs/" not in existing_content:
            gitignore_file.write_text(existing_content + gitignore_content)
            print("✅ .gitignore actualizado con nuevas entradas")
    else:
        gitignore_file.write_text(gitignore_content)
        print("✅ .gitignore creado")

def run_tests():
    """Ejecutar tests básicos"""
    if Path("venv").exists():
        if os.name == 'nt':
            pytest_cmd = "venv\\Scripts\\pytest"
        else:
            pytest_cmd = "venv/bin/pytest"
    else:
        pytest_cmd = "pytest"
    
    return run_command(f"{pytest_cmd} tests/ -v", "Ejecutando tests", check=False)

def main():
    """Función principal de configuración"""
    print("=" * 60)
    print("🚀 CONFIGURACIÓN AUTOMÁTICA DE PUG")
    print("=" * 60)
    
    # Verificaciones previas
    if not check_python_version():
        return False
    
    # Configuración del entorno
    pip_cmd = setup_virtual_environment()
    
    if not install_dependencies(pip_cmd):
        print("❌ Error instalando dependencias")
        return False
    
    # Configuración del proyecto
    setup_directories()
    create_env_file()
    create_gitignore()
    
    # Verificaciones de servicios
    redis_available = check_redis()
    
    # Tests
    print("\n" + "=" * 60)
    print("🧪 EJECUTANDO TESTS")
    print("=" * 60)
    tests_passed = run_tests()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE CONFIGURACIÓN")
    print("=" * 60)
    
    print("✅ Entorno virtual configurado")
    print("✅ Dependencias instaladas")
    print("✅ Directorios creados")
    print("✅ Archivo .env configurado")
    
    if redis_available:
        print("✅ Redis disponible")
    else:
        print("⚠️  Redis no disponible (instalar para funcionalidad completa)")
    
    if tests_passed:
        print("✅ Tests ejecutados correctamente")
    else:
        print("⚠️  Algunos tests fallaron (revisar configuración)")
    
    print("\n🎉 CONFIGURACIÓN COMPLETADA")
    print("\n📖 PRÓXIMOS PASOS:")
    print("1. Activar entorno virtual:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("2. Iniciar Redis (si no está ejecutándose):")
    print("   redis-server")
    
    print("3. Iniciar la aplicación:")
    print("   python src/app.py")
    
    print("4. O usar Docker:")
    print("   docker-compose up --build")
    
    print("\n🔧 HERRAMIENTAS DISPONIBLES:")
    print("• Análisis de logs: python scripts/analyze_logs.py")
    print("• Tests: pytest tests/ -v")
    print("• Crear admin: python hash_pass.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
