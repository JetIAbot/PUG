# PUG - Portal University Grouper

Sistema de carpooling para estudiantes universitarios de la Pontificia Università Gregoriana (Roma). Gestiona estudiantes, horarios extraídos automáticamente del portal universitario y organiza viajes compartidos semanales.

## Estado actual del proyecto

La extracción de datos del portal universitario fue validada en una prueba individual:

- Microsoft Edge inicia correctamente mediante Selenium.
- El portal `segreteria.unigre.it` carga correctamente.
- El registro de un estudiante desde el portal captura y guarda sus datos y horario.
- La persistencia local en archivos Markdown/YAML funciona con los datos de `datos/`.

Desde el menú **Sistema / Configuración > Estado del proyecto** se puede consultar este estado directamente en la CLI.

### Funciones operativas y verificadas

- Extracción de perfil y horario desde el portal universitario.
- Detección del semestre activo.
- Guardado y lectura de estudiantes en Markdown con YAML frontmatter.
- Gestión de estudiantes y actualización de disponibilidad.
- Selenium con Microsoft Edge en modo headless.

### Funciones implementadas pendientes de validación completa

- CRUD de carros, estados y compatibilidad de licencias.
- Creación manual y asignación automática de viajes.
- Listas diarias de viajes y planificación de rutas.
- Exportación de rutas a PDF.
- Estadísticas, logging y herramientas administrativas.

### Funciones aún en desarrollo

- Interfaz web: la aplicación actual es exclusivamente CLI.
- Extracción específica de calificaciones del portal.
- Comparación automática de fechas de datos extraídos.
- Impedir la eliminación de carros que tengan viajes activos.
- Registrar el usuario real que crea una lista diaria.

## Caracteristicas

- Extraccion automatizada de horarios desde el portal universitario (Selenium + Microsoft Edge)
- Deteccion automatica de semestre activo (1ro o 2do)
- Registro manual o via portal de estudiantes
- Calculo automatico de disponibilidad semanal segun horario
- Gestion de licencias de conducir y vehiculos
- Almacenamiento local en archivos Markdown (compatible con Obsidian)
- Interfaz CLI completa con menus interactivos
- Deteccion de licencias vencidas al registrar
- Visualizacion de horario semanal en formato grilla
- Sistema de logging y auditoria

## Tecnologias

- **Python** 3.12+
- **Selenium WebDriver** + Selenium Manager para Edge (extraccion del portal)
- **PyYAML** (almacenamiento Markdown con YAML frontmatter)
- **Werkzeug** (hashing de contrasenas admin)
- **python-dotenv** (configuracion por entorno)

## Estructura del Proyecto

```
PUG/
+-- main.py                    # Interfaz CLI principal
+-- config.py                  # Configuracion por entornos
+-- requirements.txt           # Dependencias Python
+-- .env / .env.example        # Variables de entorno
+-- pyproject.toml             # Metadata del proyecto
|
+-- core/                      # Logica de negocio
|   +-- portal_extractor.py    # Extraccion del portal universitario
|   +-- student_scheduler.py   # Orquestador: extraccion + procesamiento + guardado
|   +-- student_manager.py     # CRUD de estudiantes
|   +-- car_manager.py         # CRUD de vehiculos
|   +-- viaje_manager.py       # CRUD de viajes y asignacion automatica
|   +-- obsidian_manager.py    # Almacenamiento local Markdown (reemplaza Firebase)
|   +-- data_processor.py      # Procesamiento de datos
|   +-- demo_generator.py      # Generacion de datos demo
|   +-- models.py              # Modelos: Estudiante, Carro, Viaje, TipoLicencia
|
+-- utils/                     # Utilidades
|   +-- constants.py           # Constantes y selectores del portal
|   +-- validators.py          # Validaciones de datos
|   +-- logger_config.py       # Configuracion de logging
|   +-- log_cleaner.py         # Limpieza de logs
|   +-- admin_tools.py         # Herramientas administrativas
|
+-- datos/                     # Base de datos local (gitignored)
|   +-- estudiantes/           # Un archivo .md por estudiante
|
+-- scripts/                   # Scripts de utilidades
|   +-- analyze_logs.py
|   +-- security_check.py
|   +-- test_chrome.py
|   +-- test_portal.py
|
+-- logs/                      # Logs del sistema
+-- tests/                     # Pruebas
```

## Instalacion

```powershell
git clone https://github.com/JetIAbot/PUG.git
cd PUG
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configurar variables de entorno

Copiar `.env.example` a `.env` y ajustar:

```env
APP_ENV=development
DEBUG=True
DATOS_PATH=datos
LOG_LEVEL=INFO
```

### Requisitos adicionales

- **Microsoft Edge** instalado (navegador predeterminado para la extracción del portal)
- Selenium Manager localiza Edge y gestiona `msedgedriver` automáticamente
- Google Chrome también es compatible como alternativa configurando `BROWSER=chrome`

## Uso

```powershell
python main.py
```

### Menú principal

```
[1] Gestionar Carros
[2] Gestionar Estudiantes
[3] Gestionar Viajes
[4] Listas Diarias
[5] Sistema / Configuracion
[0] Salir
```

### Gestion de Estudiantes

```
[1] Listar estudiantes
[2] Crear estudiante (manual)
[3] Registrar via portal
[4] Ver detalle de estudiante
[5] Editar estudiante
[6] Actualizar disponibilidad semanal
[7] Eliminar estudiante
[0] Volver
```

### Flujo tipico

1. **Registrar estudiante via portal** (opcion 1 -> 3): extrae nombre, email, telefono y horario completo del semestre activo. Pregunta tipo de licencia y preferencia de viaje.
2. **Actualizar disponibilidad semanal** (opcion 1 -> 6): calcula automaticamente que dias viaja cada estudiante segun su horario.
3. **Registrar vehiculos** (opcion 2): anadir carros disponibles para carpooling.
4. **Generar viajes** (opcion 3): asignacion automatica de pasajeros a conductores por dia.

### Portal universitario

El sistema se conecta a `https://segreteria.unigre.it` y extrae:
- Datos personales (nombre, apellido, email, telefono) desde "Dati Anagrafici"
- Horario semanal completo desde "Orario Settimanale"
- Deteccion automatica del semestre publicado (cuando un semestre esta publicado, el otro aparece vacio)

### Almacenamiento

Cada estudiante se guarda como un archivo `.md` en `datos/estudiantes/` con YAML frontmatter:

```yaml
---
matricola: '100000'
nome: MARIO
cognome: ROSSI
email: mario.rossi@example.com
telefono: '390000000000'
semestre_activo: 2
horario:
  - codigo: XX1234
    materia: NOMBRE DE MATERIA
    profesor: Prof. APELLIDO Nombre
    dia: Lunedi
    bloque: I
    aula: 'Aula: A101 Piano: 1'
materias:
  - codigo: XX1234
    nombre: NOMBRE DE MATERIA
    creditos: '3'
    semestre: '2'
---
```

## Seguridad

- `.gitignore` protege: `.env`, `datos/`, `*.log`
- Credenciales del portal nunca se almacenan, solo se usan durante la extraccion
- Contrasenas admin hasheadas con Werkzeug
- Datos personales solo en almacenamiento local

## Licencia

Ver [LICENSE](LICENSE)
