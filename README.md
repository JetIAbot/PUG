# PUG Matchmaking - Sincronizador de Horarios y Buscador de Compañeros de Viaje

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg) ![Flask](https://img.shields.io/badge/Flask-2.x-black.svg) ![Celery](https://img.shields.io/badge/Celery-5.x-green.svg) ![Firebase](https://img.shields.io/badge/Firebase-Firestore-orange.svg) ![Selenium](https://img.shields.io/badge/Selenium-4.x-yellow.svg)

Este proyecto es una aplicación web diseñada para los estudiantes de la Pontificia Universidad Gregoriana (PUG). Su objetivo es doble:
1.  **Automatizar la Sincronización de Horarios:** Permite a los estudiantes extraer su horario académico directamente desde el portal de la universidad y guardarlo en una base de datos centralizada.
2.  **Facilitar el Viaje Compartido:** Proporciona una herramienta para administradores que analiza todos los horarios guardados y encuentra grupos de estudiantes con horarios compatibles para viajar juntos hacia y desde la universidad, fomentando la comunidad y optimizando el transporte.

---

## 📋 Características Principales

*   **Interfaz de Estudiante Sencilla:** Un formulario simple para que los estudiantes introduzcan sus credenciales de la universidad.
*   **Web Scraping Automatizado:** Utiliza Selenium para navegar por el portal de la universidad, iniciar sesión y extraer los datos personales y el horario del estudiante.
*   **Procesamiento Asíncrono de Tareas:** Gracias a Celery y Redis, las solicitudes de scraping se encolan y se procesan en segundo plano, permitiendo que la aplicación maneje múltiples usuarios simultáneamente sin colapsar.
*   **Base de Datos en la Nube:** Almacena toda la información de forma segura en Google Firestore.
*   **Panel de Administrador:** Una interfaz para ejecutar el algoritmo de matchmaking con un solo clic.
*   **Algoritmo de Matchmaking Inteligente:** Analiza los horarios para encontrar la primera y la última clase de cada estudiante por día, identificando así grupos de viaje compatibles.

---

## 🏗️ Arquitectura Tecnológica

El proyecto está construido con una arquitectura moderna y escalable:

*   **Frontend:** HTML5 con CSS simple (renderizado por Flask).
*   **Backend (Servidor Web):** **Flask**, un micro-framework de Python ligero y potente.
*   **Web Scraping:** **Selenium** para controlar un navegador Chrome en modo headless.
*   **Cola de Tareas:** **Celery** para gestionar las tareas de scraping de larga duración.
*   **Intermediario de Mensajes (Broker):** **Redis**, que actúa como la cola donde Celery deposita y recoge las tareas.
*   **Base de Datos:** **Google Firestore**, una base de datos NoSQL, flexible y escalable.

---

## 🚀 Guía de Instalación y Puesta en Marcha

Sigue estos pasos para ejecutar el proyecto en tu máquina local.

### 1. Prerrequisitos

Asegúrate de tener instalado lo siguiente en tu sistema:
*   **Python 3.9** o superior.
*   **Git** para clonar el repositorio.
*   **Redis Server:** Sigue la [guía de instalación para Windows](https://github.com/tporadowski/redis/releases) (descarga el archivo `.msi`).

### 2. Configuración del Proyecto

**a. Clonar el Repositorio**
Abre una terminal y clona este repositorio:
```bash
git clone https://github.com/tu-usuario/PUG.git
cd PUG
```

**b. Crear un Entorno Virtual**
Es una buena práctica aislar las dependencias del proyecto.
```bash
python -m venv venv
```
Activa el entorno virtual:
*   En Windows: `.\venv\Scripts\activate`
*   En macOS/Linux: `source venv/bin/activate`

**c. Instalar Dependencias**
Instala todas las librerías de Python necesarias con un solo comando:
```bash
pip install -r requirements.txt
```

**d. Configurar Credenciales de Firebase**
1.  Obtén tu archivo de credenciales de servicio de Firebase (un archivo `.json`).
2.  Renómbralo a `credenciales.json`.
3.  Colócalo en la **raíz del directorio del proyecto**.

**e. Configurar Variables de Entorno**
1.  Crea un archivo llamado `.env` en la raíz del proyecto.
2.  Añade el siguiente contenido al archivo `.env`, reemplazando el valor con una cadena de caracteres larga y aleatoria:
    ```
    FLASK_SECRET_KEY='un-valor-aleatorio-muy-largo-y-dificil-de-adivinar'
    ```

---

## ▶️ Cómo Ejecutar la Aplicación

Para que la aplicación funcione, necesitas tener **3 terminales abiertas simultáneamente** (con el entorno virtual activado en cada una).

**Terminal 1: Iniciar el Servidor Redis**
*   Si instalaste Redis como un servicio de Windows, ya debería estar ejecutándose. Puedes verificarlo en `services.msc`.
*   Si no, inicia el servidor manualmente:
    ```bash
    redis-server
    ```
*Deja esta terminal abierta.*

**Terminal 2: Iniciar el Worker de Celery**
Este es el trabajador que procesará las tareas de scraping. **Importante:** Ejecuta este comando desde la raíz del proyecto.
```bash
python -m celery -A src.tasks worker --loglevel=info --pool=solo
```
*El parámetro `--pool=solo` es importante para la compatibilidad con Windows. Deja esta terminal abierta para ver los logs de las tareas.*

**Terminal 3: Iniciar el Servidor Web Flask**
Este es el motor de tu aplicación web. **Importante:** Ejecuta este comando desde la raíz del proyecto.
```bash
python -m src.app
```
*Deja esta terminal abierta.*

---

## 💻 Cómo Usar la Aplicación

Una vez que los tres componentes estén en marcha:

**Para Estudiantes:**
1.  Abre tu navegador y ve a `http://127.0.0.1:5000/`.
2.  Introduce tu usuario (matrícula) y contraseña del portal de la universidad.
3.  Haz clic en "Actualizar mi Horario".
4.  Recibirás un mensaje de confirmación. La tarea se está procesando en segundo plano. Puedes revisar la terminal del worker de Celery para ver el progreso. Una vez completada, tus datos estarán en Firestore.

**Para Administradores:**
1.  Abre tu navegador y ve a `http://127.0.0.1:5000/admin`.
2.  Haz clic en el botón "Encontrar Grupos de Viaje".
3.  Aparecerá un spinner de carga y, tras unos segundos, los resultados del matchmaking se mostrarán directamente en la página.

---

## 📂 Estructura del Proyecto

```
.
├── src/                # Directorio principal del código fuente
│   ├── __init__.py     # Hace que src sea un paquete de Python
│   ├── app.py          # Aplicación principal Flask (rutas y lógica web)
│   ├── main.py         # Script de Web Scraping con Selenium
│   ├── tasks.py        # Definición de las tareas de Celery
│   └── matchmaking.py  # Algoritmo para encontrar grupos de viaje
├── templates/          # Archivos HTML para la interfaz
│   ├── index.html      # Página de login para estudiantes
│   └── admin.html      # Panel de control del administrador
├── .env                # (Tú lo creas) Variables de entorno (ej. FLASK_SECRET_KEY)
├── credenciales.json   # (Tú lo añades) Credenciales de servicio de Firebase
├── requirements.txt    # Lista de dependencias de Python
└── README.md           # Este archivo
```

---

## 🛠️ Solución de Problemas Comunes

*   **Error: `ModuleNotFoundError` al importar bibliotecas:** Asegúrate de que el entorno virtual esté activado. Deberías ver el prefijo `(venv)` en tu terminal.
*   **Problemas con Redis en Windows:** Si `redis-server` no se reconoce como un comando, asegúrate de que la ruta de instalación de Redis esté en tu variable de entorno `PATH`.
*   **Errores de Firebase:** Verifica que el archivo `credenciales.json` esté en la raíz del proyecto y que las reglas de Firestore permitan la lectura/escritura durante el desarrollo.

---

## 📅 Roadmap y Futuras Mejoras

*   **Interfaz de Usuario Mejorada:** Rediseñar la interfaz con un framework moderno como React o Vue.js.
*   **Autenticación Segura:** Implementar OAuth2.0 para una autenticación más segura y flexible.
*   **Despliegue en la Nube:** Instrucciones para desplegar la aplicación en plataformas como Heroku, AWS o Google Cloud.
*   **Optimización del Algoritmo de Matchmaking:** Usar técnicas avanzadas de machine learning para mejorar la precisión del matchmaking.

---

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:
1.  Haz un fork del repositorio.
2.  Crea una nueva rama (`git checkout -b mi-rama`).
3.  Realiza tus cambios y asegúrate de que todo funcione.
4.  Haz un commit de tus cambios (`git commit -m 'Descripción de mis cambios'`).
5.  Sube tus cambios a tu fork (`git push origin mi-rama`).
6.  Crea un Pull Request describiendo tus cambios y por qué deberían ser aceptados.

---

## 📜 Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

---

## 📧 Contacto

Para preguntas o más información, por favor contacta a:
**Jose Giraldo** - jose.giraldo.vasquez@srmmedellin.com

---

¡Gracias por usar PUG Matchmaking! Esperamos que esta herramienta mejore tu experiencia académica y de transporte en la Pontificia Universidad Gregoriana.
