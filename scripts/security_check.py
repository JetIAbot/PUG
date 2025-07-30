"""
Script de verificación de seguridad para desarrollo con datos reales
"""
import os
import sys
from dotenv import load_dotenv

def check_security_configuration():
    """Verificar que todas las medidas de seguridad están correctamente configuradas"""
    
    print("🔒 VERIFICACIÓN DE SEGURIDAD - DATOS REALES")
    print("=" * 50)
    
    # Cargar variables de entorno
    load_dotenv()
    
    checks_passed = 0
    total_checks = 10
    
    # 1. Verificar enmascaramiento de credenciales
    mask_credentials = os.getenv('MASK_CREDENTIALS', 'False').lower() == 'true'
    print(f"✅ Enmascaramiento de credenciales: {'ACTIVO' if mask_credentials else '❌ INACTIVO'}")
    if mask_credentials:
        checks_passed += 1
    
    # 2. Verificar que no se loguean datos sensibles
    log_sensitive = os.getenv('LOG_SENSITIVE_DATA', 'True').lower() == 'false'
    print(f"✅ Protección de datos sensibles: {'ACTIVO' if log_sensitive else '❌ INACTIVO'}")
    if log_sensitive:
        checks_passed += 1
    
    # 3. Verificar retención limitada de logs
    retention_days = int(os.getenv('LOG_RETENTION_DAYS', '30'))
    retention_ok = retention_days <= 7
    print(f"✅ Retención de logs: {retention_days} días ({'OK' if retention_ok else '❌ DEMASIADO LARGO'})")
    if retention_ok:
        checks_passed += 1
    
    # 4. Verificar limpieza automática
    auto_cleanup = os.getenv('AUTO_CLEANUP', 'False').lower() == 'true'
    print(f"✅ Limpieza automática: {'ACTIVO' if auto_cleanup else '❌ INACTIVO'}")
    if auto_cleanup:
        checks_passed += 1
    
    # 5. Verificar modo de producción
    production_mode = os.getenv('PRODUCTION_MODE', 'False').lower() == 'true'
    print(f"✅ Modo de producción: {'ACTIVO' if production_mode else '❌ INACTIVO'}")
    if production_mode:
        checks_passed += 1
    
    # 6. Verificar autorización
    real_data_auth = os.getenv('REAL_DATA_AUTHORIZED', 'False').lower() == 'true'
    print(f"✅ Autorización para datos reales: {'CONFIRMADA' if real_data_auth else '❌ NO AUTORIZADA'}")
    if real_data_auth:
        checks_passed += 1
    
    # 7. Verificar modo de usuario único
    single_user = os.getenv('SINGLE_USER_MODE', 'False').lower() == 'true'
    print(f"✅ Modo de usuario único: {'ACTIVO' if single_user else '❌ INACTIVO'}")
    if single_user:
        checks_passed += 1
    
    # 8. Verificar timeout de sesión
    session_timeout = int(os.getenv('SESSION_TIMEOUT', '3600'))
    timeout_ok = session_timeout <= 1800  # Máximo 30 minutos
    print(f"✅ Timeout de sesión: {session_timeout//60} min ({'OK' if timeout_ok else '❌ DEMASIADO LARGO'})")
    if timeout_ok:
        checks_passed += 1
    
    # 9. Verificar que .env existe y está protegido
    env_exists = os.path.exists('.env')
    print(f"✅ Archivo .env: {'EXISTE' if env_exists else '❌ NO ENCONTRADO'}")
    if env_exists:
        checks_passed += 1
    
    # 10. Verificar .gitignore para protección
    gitignore_exists = os.path.exists('.gitignore')
    gitignore_ok = False
    if gitignore_exists:
        with open('.gitignore', 'r') as f:
            content = f.read()
            if '.env' in content and '*.log' in content:
                gitignore_ok = True
    print(f"✅ Protección .gitignore: {'CONFIGURADO' if gitignore_ok else '❌ INCOMPLETO'}")
    if gitignore_ok:
        checks_passed += 1
    
    print("\n" + "=" * 50)
    print(f"RESULTADO: {checks_passed}/{total_checks} verificaciones pasadas")
    
    if checks_passed == total_checks:
        print("🎉 CONFIGURACIÓN DE SEGURIDAD COMPLETA")
        print("✅ Es seguro proceder con datos reales")
        return True
    else:
        print("❌ CONFIGURACIÓN INCOMPLETA")
        print("⚠️  Configurar todas las medidas antes de usar datos reales")
        return False

def show_security_reminders():
    """Mostrar recordatorios importantes de seguridad"""
    print("\n🚨 RECORDATORIOS DE SEGURIDAD:")
    print("- Solo usar durante sesiones de desarrollo activas")
    print("- Cerrar completamente la aplicación después de cada uso")
    print("- Verificar limpieza de logs después de cada sesión")
    print("- NO compartir credenciales con terceros")
    print("- NO hacer commit de archivos con datos reales")
    print("- Mantener registro de todos los accesos")

if __name__ == "__main__":
    print("Iniciando verificación de seguridad...")
    
    if check_security_configuration():
        show_security_reminders()
        print("\n✅ Sistema listo para uso seguro con datos reales")
        sys.exit(0)
    else:
        print("\n❌ Sistema NO está listo. Configurar medidas de seguridad primero.")
        sys.exit(1)
