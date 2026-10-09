# PUG — Portal University Grouper

Sistema de carpooling para estudiantes de la **Pontificia Università Gregoriana** de Roma. PUG obtiene los horarios del portal universitario, calcula la disponibilidad de los estudiantes y ayuda a organizar viajes compartidos hacia la universidad.

> **Estado actual:** la extracción del portal y la gestión de estudiantes han sido probadas con datos reales. La aplicación se encuentra actualmente en fase CLI.

## Índice

- [Qué hace PUG](#qué-hace-pug)
- [Estado del proyecto](#estado-del-proyecto)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Arquitectura](#arquitectura)
- [Portal universitario](#portal-universitario)
- [Almacenamiento](#almacenamiento)
- [Seguridad y privacidad](#seguridad-y-privacidad)
- [Validación](#validación)

## Qué hace PUG

- Extrae el perfil y el horario del estudiante desde el portal universitario.
- Detecta el semestre activo publicado.
- Calcula la disponibilidad semanal a partir del horario.
- Gestiona estudiantes, licencias de conducir y vehículos.
- Crea viajes y asigna pasajeros según disponibilidad y capacidad.
- Genera listas diarias y planes de rutas en PDF.
- Guarda los datos localmente en archivos Markdown compatibles con Obsidian.
- Ofrece una interfaz interactiva de terminal en español.

### Selección de elementos en la interfaz

Las operaciones de consulta y edición muestran los elementos disponibles en
una lista numerada. El usuario selecciona la opción correspondiente y ya no
necesita recordar matrículas, placas o IDs técnicos largos. Los identificadores
completos se conservan internamente para mantener la unicidad y las referencias
históricas; la opción `[0] Cancelar` está disponible en estos selectores.

## Estado del proyecto

### Listo para versión preliminar Alpha

Los siguientes módulos tienen un flujo funcional completo y están preparados para formar parte de una primera versión preliminar **Alpha**:

- Gestión de estudiantes: registro manual y desde el portal, edición, consulta, disponibilidad y eliminación.
- Gestión de vehículos: registro, consulta, edición, estados, capacidad y compatibilidad de licencias.

La versión Alpha todavía debe continuar validándose con más escenarios y datos antes de considerarse estable para producción.

### Operativo y verificado

- Extracción de perfil y horario desde `segreteria.unigre.it`.
- Microsoft Edge mediante Selenium en modo headless.
- Detección del semestre activo.
- Guardado y lectura de estudiantes en Markdown con YAML frontmatter.
- Gestión de estudiantes y actualización de disponibilidad.
- Almacenamiento local en la carpeta `datos/`.

### Implementado, pendiente de validación completa

- Creación manual y asignación automática de viajes.
- Persistencia de viajes y actualización automática a `completado` cuando su fecha ya pasó.
- Archivado manual de viajes completados desde el menú, conservando su consulta histórica.
- Listas diarias y planificación de rutas.
- Exportación de rutas a PDF.
- Estadísticas, logging y herramientas administrativas.

### En desarrollo

- Interfaz web: actualmente solo está disponible la CLI.
- Extracción específica de calificaciones del portal.
- Comparación automática de fechas de datos extraídos.
- Impedir la eliminación de vehículos con viajes activos.
- Registrar el usuario real que crea una lista diaria.
- Archivado automático por antigüedad y política configurable de conservación.

Este resumen también está disponible dentro de la aplicación en:

**Sistema / Configuración → Estado del proyecto**

## Requisitos

- Windows con Microsoft Edge instalado.
- Python **3.12 o superior**.
- El entorno utilizado para la validación actual es **Python 3.14.8**.
- Conexión a Internet para acceder al portal universitario.
- Credenciales válidas del portal para registrar estudiantes mediante extracción automática.

### Dependencias principales

| Dependencia | Uso |
|---|---|
| `selenium` | Automatización del navegador y extracción del portal |
| Selenium Manager | Localización y gestión de `msedgedriver` |
| `PyYAML` | Lectura y escritura del frontmatter Markdown |
| `python-dotenv` | Carga de configuración desde `.env` |
| `Werkzeug` | Hashing de contraseñas administrativas |
| `ReportLab` | Generación de rutas en PDF |

Google Chrome también puede utilizarse como alternativa configurando `BROWSER=chrome`.

## Instalación

```powershell
git clone https://github.com/JetIAbot/PUG.git
cd PUG

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Para salir del entorno virtual:

```powershell
deactivate
```

### Servicios de aplicación

La lógica reutilizable para la futura interfaz web se encuentra en
`services/`. `RegistrationService` valida solicitudes y evita duplicar
matrículas; `ExtractionService` encapsula `StudentScheduler`. Ninguno guarda
contraseñas del portal en Markdown, logs o configuración. La CLI existente
continúa funcionando de forma independiente; la cola de trabajos y Flask se
incorporarán en fases posteriores.

La fase web inicial está disponible en `app.py`. Para ejecutarla localmente:

```powershell
.\.venv\Scripts\python.exe app.py
```

Incluye `/health`, `POST /students/register` y `GET /jobs/<id>`. Las
solicitudes se colocan en una cola local consumida por un pool limitado de
workers Selenium. Por defecto se ejecutan dos extracciones simultáneas y se
aceptan hasta 20 trabajos esperando en la cola. Los estados posibles son
`pending`, `processing`, `completed` y `failed`. La
contraseña del portal se conserva únicamente en memoria mientras el worker
procesa la extracción; no se incluye en respuestas, logs ni archivos. Los
Los metadatos se conservan en `JOB_STORE_PATH` (por defecto,
`datos/.pug_jobs.json`). Si el proceso se reinicia, los trabajos que estaban
`pending` o `processing` se marcan como `failed`, porque sus contraseñas no se
persisten y deben volver a enviarse de forma explícita.

Para actualizar el horario de un estudiante ya registrado se utiliza
`POST /students/refresh`. Este endpoint conserva los datos de carpooling y
vuelve a ejecutar la extracción del portal. La misma matrícula queda
bloqueada mientras haya un trabajo activo y durante
`REFRESH_COOLDOWN_SECONDS` (15 minutos por defecto). Las solicitudes
rechazadas reciben HTTP `429`.

La concurrencia se puede ajustar con `EXTRACTION_WORKERS`,
`MAX_PENDING_JOBS` y `EXTRACTION_TIMEOUT_SECONDS`. Se recomienda comenzar con
dos workers y aumentarlos solo después de probar los límites del portal, la
memoria del equipo y las escrituras concurrentes en SMB. La autenticación del
portal continúa ocurriendo dentro de cada extracción; no se persisten ni se
duplican las contraseñas para realizar una validación previa.

La interfaz web solicita también los datos de conducción: si el estudiante
tiene licencia, los tipos (`A1`, `A2`, `A`, `B`, `C1`, `C`, `D1`, `D`, `BE`,
`CE` o `DE`) y la fecha de vencimiento. Estos datos se guardan en el Markdown
solo después de que la extracción haya terminado correctamente. El
identificador interno del trabajo no se muestra en la interfaz.

### Almacenamiento Markdown en carpeta SMB del QNAP

PUG puede conservar el almacenamiento Markdown sin usar SQL. Para una
instalación interna pequeña, basta con que Windows tenga acceso al recurso
compartido y que `DATOS_PATH` apunte a su ruta UNC:

```env
DATOS_PATH=\\10.0.0.7\.private
```

La autenticación SMB no se guarda en `.env`, en el código ni en comandos del
repositorio. Configura el acceso desde Windows con las credenciales del
recurso, preferiblemente mediante **Administrador de credenciales** o
mapeando la unidad desde el Explorador de archivos. Si utilizas PowerShell,
Windows solicitará la contraseña de forma interactiva:

```powershell
net use \\10.0.0.7\.private /user:USUARIO_DEL_RECURSO *
```

No añadas la contraseña al comando. La ruta compartida debe conceder al
usuario permisos de lectura, escritura y creación de carpetas. Una vez
autenticado Windows, verifica el recurso:

```powershell
Test-Path '\\10.0.0.7\.private'
```

PUG crea dentro de esa ruta las carpetas `estudiantes`, `carros`, `viajes` y
las demás colecciones cuando se ejecuta `test_connection()` desde la CLI.
Antes de usar datos reales, prueba desde **Sistema / Configuración →
Verificar almacenamiento** y confirma que se puede crear y eliminar el
archivo de prueba.

## Configuración

1. Copia `.env.example` como `.env`.
2. Ajusta la ruta de datos y el navegador si es necesario.

```powershell
Copy-Item .env.example .env
```

Configuración mínima recomendada:

```env
APP_ENV=development
DEBUG=True
DEMO_MODE=True

DATOS_PATH=datos

PORTAL_URL=https://segreteria.unigre.it
BROWSER=edge
HEADLESS_MODE=True

LOG_LEVEL=INFO
AUTO_CLEANUP=True
LOG_MAX_DAYS=7

MASK_CREDENTIALS=True
LOG_SENSITIVE_DATA=False
```

Las credenciales del portal **no se guardan en `.env` ni en archivos del proyecto**. Se introducen durante el registro y se utilizan únicamente durante la sesión de extracción.

## Uso

Inicia la aplicación con:

```powershell
python main.py
```

### Menú principal

```text
[1] Gestionar Carros
[2] Gestionar Estudiantes
[3] Gestionar Viajes
[4] Listas Diarias
[5] Sistema / Configuración
[0] Salir
```

### Flujo recomendado

1. **Registrar un estudiante**
   - Manualmente, o
   - mediante el portal universitario.
2. **Actualizar la disponibilidad semanal** del estudiante.
3. **Registrar los vehículos** disponibles y sus conductores.
4. **Generar viajes** mediante asignación manual o automática.
5. **Crear y consultar listas diarias**.
6. **Exportar el plan diario a PDF** cuando la planificación haya sido validada.

En el menú **Sistema / Configuración** también están disponibles las comprobaciones de almacenamiento, navegador/Selenium, estadísticas y administración.

## Arquitectura

```text
PUG/
├── main.py                    # Interfaz CLI y menús
├── config.py                  # Configuración por entorno
├── requirements.txt           # Dependencias Python
├── pyproject.toml             # Metadatos y configuración de pytest
├── .env.example               # Plantilla de configuración local
│
├── core/
│   ├── portal_extractor.py    # Extracción mediante Selenium
│   ├── student_scheduler.py   # Procesamiento de horarios y compatibilidades
│   ├── student_manager.py     # CRUD de estudiantes
│   ├── car_manager.py         # CRUD de vehículos
│   ├── viaje_manager.py       # CRUD y asignación de viajes
│   ├── daily_route_planner.py # Planificación diaria y exportación PDF
│   ├── obsidian_manager.py    # Persistencia Markdown/YAML
│   ├── data_processor.py      # Procesamiento coordinado de datos
│   ├── demo_generator.py      # Datos de demostración
│   └── models.py              # Modelos y reglas de dominio
│
├── utils/
│   ├── constants.py           # Constantes y selectores del portal
│   ├── validators.py          # Validaciones
│   ├── logger_config.py       # Configuración de logging
│   ├── log_cleaner.py         # Limpieza de logs
│   └── admin_tools.py         # Herramientas administrativas
│
├── datos/                     # Datos locales; excluidos de Git
├── logs/                      # Logs; excluidos de Git
├── scripts/                   # Diagnóstico y utilidades
└── tests/                     # Pruebas automatizadas
```

## Portal universitario

PUG utiliza:

```text
https://segreteria.unigre.it
```

La extracción obtiene:

- datos personales del estudiante;
- materias disponibles;
- horario semanal;
- semestre activo;
- calificaciones cuando el portal y el extractor las proporcionan.

El navegador predeterminado es Edge:

```env
BROWSER=edge
```

Para utilizar Chrome:

```env
BROWSER=chrome
```

El modo headless se controla mediante `HEADLESS_MODE`.

## Almacenamiento

Cada estudiante se guarda normalmente en:

```text
datos/estudiantes/<matricola>.md
```

El archivo contiene YAML frontmatter, por ejemplo:

```yaml
---
matricola: '100000'
nome: MARIO
cognome: ROSSI
email: mario.rossi@example.com
telefono: '390000000000'
semestre_activo: 2
estado_horarios: disponible
horario:
  - codigo: XX1234
    materia: NOMBRE DE MATERIA
    profesor: Prof. APELLIDO Nombre
    dia: Lunedì
    bloque: I
    aula: 'Aula: A101 Piano: 1'
materias: []
calificaciones: []
---
```

La carpeta `datos/` está incluida en `.gitignore` porque puede contener información personal.

## Seguridad y privacidad

- `.env`, `datos/` y `logs/` están excluidos del repositorio.
- Las credenciales del portal no se almacenan.
- Las contraseñas administrativas se guardan mediante hashing de Werkzeug.
- El registro de logs puede configurarse para no incluir datos sensibles.
- No deben compartirse ni versionarse archivos de datos reales.

## Validación

Comprobaciones realizadas durante la validación actual:

```powershell
python -m pip check
python -m compileall -q .
```

También se verificó que:

- Edge inicia correctamente mediante Selenium.
- El portal universitario carga correctamente en Edge.
- El almacenamiento local responde correctamente.
- Un estudiante existente puede leerse desde `datos/estudiantes/`.

El directorio `tests/` todavía contiene una cobertura automatizada limitada; los scripts de `scripts/` sirven como diagnósticos y pruebas manuales.

## Licencia

Consulta [LICENSE](LICENSE).
