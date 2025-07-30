# PUG - Portal University Grouper

Sistema integral para la gestión y asignación automatizada de estudiantes universitarios a grupos de trabajo, completamente reestructurado para mayor claridad y mantenibilidad.

## Características

- ✅ Extracción automatizada de datos del portal universitario con Selenium
- ✅ Algoritmo inteligente de asignación de estudiantes a grupos
- ✅ Integración completa con Firebase Firestore
- ✅ Sistema de demostración con datos sintéticos
- ✅ Panel de administración web con validación
- ✅ Procesamiento eficiente de datos estudiantiles
- ✅ Sistema de logging y auditoría completo
- ✅ Validación robusta de credenciales universitarias

## Tecnologías Utilizadas

- **Backend**: Python 3.13+ con Flask 2.3+
- **Automatización Web**: Selenium WebDriver (Chrome/ChromeDriver)
- **Base de Datos**: Firebase Firestore con SDK Admin
- **Interfaz Web**: HTML5, CSS3, JavaScript vanilla
- **Contenerización**: Docker y Docker Compose
- **Tareas Asíncronas**: Celery con Redis
- **Logging**: Sistema centralizado con rotación
- **Testing**: pytest con cobertura completa

## Nueva Estructura del Proyecto (Reestructurada)

```
PUG/
├── app.py                     # 🎯 Aplicación Flask principal
├── config.py                  # ⚙️ Configuración por entornos
├── requirements.txt           # 📦 Dependencias Python
├── docker-compose.yml         # 🐳 Orquestación Docker
├── Dockerfile                 # 🐳 Imagen Docker
├── .gitignore                 # 🔒 Protección datos personales
│
├── core/                      # 🧠 Lógica de negocio principal
│   ├── __init__.py
│   ├── student_scheduler.py   # 👥 Algoritmo de agrupación (ex matchmaking.py)
│   ├── portal_extractor.py    # 🌐 Extracción portal universitario (ex portal.py)
│   ├── demo_generator.py      # 🎭 Generación datos demo (ex demo.py)
│   ├── firebase_manager.py    # 🔥 Operaciones Firebase (ex firebase_ops.py)
│   └── data_processor.py      # 📊 Procesamiento de datos
│
├── utils/                     # 🛠️ Utilidades y herramientas
│   ├── __init__.py
│   ├── constants.py           # 📋 Constantes del sistema
│   ├── validators.py          # ✅ Validaciones de datos
│   ├── logger_config.py       # 📝 Configuración de logging
│   ├── log_cleaner.py         # 🧹 Limpieza de logs
│   └── admin_tools.py         # 👨‍💼 Herramientas administrativas
│
├── templates/                 # 🎨 Plantillas HTML
│   ├── index.html            # 🏠 Página principal
│   ├── admin.html            # 👨‍💼 Panel administrativo
│   ├── admin_login.html      # 🔐 Login administrativo
│   └── revisar.html          # 📋 Revisión de resultados
│
├── static/                    # 📁 Archivos estáticos
│   ├── css/validation.css     # 🎨 Estilos de validación
│   ├── js/validation.js       # ⚡ JavaScript de validación
│   └── uploads/               # 📤 Archivos subidos
│
├── logs/                      # 📝 Sistema de logs
│   ├── app.log               # 📊 Log principal
│   ├── security.log          # 🔒 Log de seguridad
│   ├── errors.log            # ❌ Log de errores
│   └── audit.log             # 🔍 Log de auditoría
│
├── tests/                     # 🧪 Pruebas unitarias
│   ├── __init__.py
│   ├── conftest.py           # ⚙️ Configuración pytest
│   └── test_app.py           # 🧪 Tests principales
│
├── scripts/                   # 🔧 Scripts de utilidades
│   ├── test_restructuracion.py  # ✅ Validación reestructuración
│   ├── analyze_logs.py          # 📊 Análisis de logs
│   └── security_check.py        # 🔒 Verificación seguridad
│
└── temp_downloads/            # 📥 Descargas temporales (ignorado en git)
```

## Instalación y Configuración

### Método 1: Instalación Local

1. **Clonar el repositorio**:
   ```powershell
   git clone <repository-url>
   cd PUG
   ```

2. **Crear entorno virtual**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1   # PowerShell
   # o venv\Scripts\activate.bat  # CMD
   ```

3. **Instalar dependencias**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configurar Firebase**:
   - Crear proyecto en [Firebase Console](https://console.firebase.google.com/)
   - Habilitar Firestore Database
   - Descargar archivo de credenciales JSON de Service Account
   - Renombrar a `credenciales.json` y colocar en la raíz del proyecto

5. **Configurar variables de entorno** (opcional):
   ```powershell
   # Crear archivo .env
   echo "FLASK_ENV=development" > .env
   echo "DEBUG_MODE=true" >> .env
   ```

6. **Ejecutar aplicación**:
   ```powershell
   python app.py
   ```

### Método 2: Docker

1. **Ejecutar con Docker Compose**:
   ```powershell
   docker-compose up --build
   ```

## Uso del Sistema

### Interfaz Web

1. **Acceder** a `http://localhost:5000`
2. **Cargar credenciales** universitarias en formato JSON
3. **Configurar parámetros** de agrupación de estudiantes
4. **Ejecutar proceso** de asignación automática
5. **Revisar resultados** en la interfaz de revisión

### API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/` | Página principal del sistema |
| `POST` | `/procesar` | Procesamiento de datos estudiantiles |
| `GET` | `/revisar` | Revisión de resultados de agrupación |
| `GET` | `/admin` | Panel administrativo |
| `POST` | `/admin/login` | Autenticación administrativa |

## Funcionalidades Principales

### 1. 🌐 Extracción de Datos del Portal (`portal_extractor.py`)
- Automatización completa con Selenium WebDriver
- Manejo inteligente de cookies y sesiones
- Extracción robusta de horarios estudiantiles
- Validación automática de credenciales universitarias
- Manejo de errores y reintentos automáticos

### 2. 👥 Algoritmo de Asignación (`student_scheduler.py`)
- Análisis avanzado de compatibilidad horaria
- Distribución equitativa de estudiantes por grupos
- Consideración de restricciones académicas múltiples
- Optimización mediante algoritmos de matching
- Métricas de calidad de agrupación

### 3. 🔥 Gestión de Datos (`firebase_manager.py`)
- Almacenamiento seguro en Firebase Firestore
- Operaciones CRUD completas y optimizadas
- Backup automático de datos críticos
- Sincronización en tiempo real
- Historial completo de cambios y auditoría

### 4. 🎭 Sistema de Demostración (`demo_generator.py`)
- Generación inteligente de datos sintéticos
- Simulación de escenarios universitarios reales
- Validación exhaustiva de algoritmos
- Entorno de pruebas completamente seguro
- Datos de demo configurables y realistas

## Configuración Avanzada

### Variables de Entorno

Crear archivo `.env` con configuraciones específicas:

```env
# Configuración de Flask
FLASK_ENV=development
FLASK_DEBUG=true

# Configuración de Firebase
FIREBASE_PROJECT_ID=tu-proyecto-firebase

# Configuración de logging
LOG_LEVEL=INFO
LOG_ROTATION_SIZE=10MB

# Configuración de seguridad
SECRET_KEY=tu-clave-secreta-aqui
ADMIN_PASSWORD_HASH=hash-de-password-admin
```

### Personalización de Algoritmos

El sistema permite ajustar parámetros en `utils/constants.py`:

```python
# Configuración de agrupación
GRUPO_CONFIG = {
    'tamaño_maximo': 4,
    'compatibilidad_minima': 0.7,
    'peso_prioridad': 0.3,
    'permitir_grupos_incompletos': True
}

# Configuración de horarios
HORARIO_CONFIG = {
    'hora_inicio': '07:00',
    'hora_fin': '22:00',
    'duracion_bloque': 90,  # minutos
    'descanso_entre_bloques': 15  # minutos
}
```

## Monitoreo y Logs

### Sistema de Logging Centralizado

El sistema genera logs estructurados en `logs/`:

| Archivo | Propósito | Contenido |
|---------|-----------|-----------|
| `app.log` | 📊 Actividad general | Operaciones normales del sistema |
| `security.log` | 🔒 Eventos de seguridad | Autenticaciones, accesos, intentos sospechosos |
| `errors.log` | ❌ Errores y excepciones | Stack traces, errores de sistema |
| `audit.log` | 🔍 Auditoría de operaciones | Cambios de datos, operaciones críticas |

### Análisis de Logs

```powershell
# Ejecutar análisis automático
python scripts/analyze_logs.py

# Limpiar logs antiguos
python scripts/log_cleaner.py
```

## Seguridad y Protección de Datos

### Medidas de Seguridad Implementadas

- 🔐 **Encriptación** de credenciales sensibles
- ✅ **Validación exhaustiva** de entrada de datos
- 🛡️ **Manejo seguro** de sesiones web
- 📝 **Auditoría completa** de accesos y operaciones
- 🚫 **Protección contra** inyecciones y ataques XSS
- 🔒 **Enmascaramiento** de datos personales en logs

### Protección de Datos Personales

El `.gitignore` está configurado para **NO subir**:
- ❌ `credenciales*.json` - Credenciales Firebase
- ❌ `*.log` - Archivos de logging con datos sensibles  
- ❌ `temp_downloads/` - Descargas temporales
- ❌ `.env` - Variables de entorno con secrets
- ❌ `uploads/` - Archivos subidos por usuarios

## Desarrollo y Contribución

### Ejecutar Pruebas

```powershell
# Ejecutar suite completa de pruebas
python -m pytest tests/ -v

# Ejecutar con cobertura
python -m pytest tests/ --cov=core --cov=utils

# Ejecutar pruebas específicas
python test_restructuracion.py  # Validar reestructuración
python test_simple.py          # Pruebas básicas
```

### Guías de Desarrollo

- 📏 **Estilo de código**: Seguir PEP 8 estrictamente
- 📚 **Documentación**: Docstrings para todas las funciones y clases
- 🧪 **Testing**: Crear pruebas para nuevas funcionalidades
- 📝 **Logs**: Mantener registro detallado de cambios
- 🔒 **Seguridad**: Validar todas las entradas de usuario

### Debugging Avanzado

```python
# Activar modo debug completo
if __name__ == '__main__':
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        use_reloader=True
    )
```

## Solución de Problemas

### Problemas Comunes y Soluciones

1. **🔥 Error de conexión Firebase**:
   ```bash
   # Verificar credenciales
   python -c "import json; print(json.load(open('credenciales.json'))['project_id'])"
   ```

2. **🌐 Error WebDriver/Chrome**:
   ```powershell
   # Instalar/actualizar ChromeDriver
   pip install --upgrade selenium webdriver-manager
   ```

3. **📦 Error de dependencias**:
   ```powershell
   # Reinstalación completa
   pip install --upgrade pip
   pip install -r requirements.txt --force-reinstall
   ```

4. **⚡ Error de puerto ocupado**:
   ```powershell
   # Encontrar proceso usando puerto 5000
   netstat -ano | findstr :5000
   taskkill /PID <PID> /F
   ```

### Logs de Debugging

```powershell
# Monitorear logs en tiempo real
Get-Content logs/app.log -Wait -Tail 50

# Buscar errores específicos
Select-String -Path logs/errors.log -Pattern "ERROR"
```

## Licencia

Este proyecto está bajo la **Licencia MIT**. Ver archivo `LICENSE` para detalles completos.

## Changelog de Reestructuración

### ✅ Completado (v2.0.0)
- **Reestructuración completa** de directorios `src/` → `core/` + `utils/`
- **Renombrado inteligente** de archivos por funcionalidad clara
- **Centralización** de configuración en `config.py`
- **Sistema de logging** mejorado y centralizado
- **Protección completa** de datos personales en Git
- **Validación exhaustiva** con suite de pruebas
- **Documentación completa** actualizada

## Soporte y Contacto

Para reportar problemas, solicitar funcionalidades o contribuir:

1. 🐛 **Issues**: Crear un issue detallado en el repositorio
2. 💡 **Feature Requests**: Describir la funcionalidad deseada
3. 🔒 **Problemas de Seguridad**: Contactar directamente al maintainer

---

**⚠️ IMPORTANTE**: Este sistema maneja datos estudiantiles sensibles. Asegurar cumplimiento con:
- 📋 GDPR (General Data Protection Regulation)
- 🇪🇸 LOPD (Ley Orgánica de Protección de Datos)
- 🏫 Regulaciones específicas de la institución educativa

**🔒 SEGURIDAD**: Nunca compartir archivos `credenciales.json` o datos reales de estudiantes.
