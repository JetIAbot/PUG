# PUG Matchmaking - Sincronizador de Horarios y Buscador de Compañeros de Viaje

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg) ![Flask](https://img.shields.io/badge/Flask-2.x-black.svg) ![Celery](https://img.shields.io/badge/Celery-5.x-green.svg) ![Firebase](https://img.shields.io/badge/Firebase-Firestore-orange.svg) ![Selenium](https://img.shields.io/badge/Selenium-4.x-yellow.svg) ![License](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)

Este proyecto es una aplicación web diseñada para los estudiantes de la Pontificia Universidad Gregoriana (PUG). Su objetivo es doble:
1.  **Automatizar la Sincronización de Horarios:** Permite a los estudiantes extraer su horario académico directamente desde el portal de la universidad y guardarlo en una base de datos centralizada.
2.  **Facilitar el Viaje Compartido:** Proporciona una herramienta para administradores que analiza todos los horarios guardados y encuentra grupos de estudiantes con horarios compatibles para viajar juntos, fomentando la comunidad y optimizando el transporte.

---

## 📋 Características Principales

*   **Interfaz de Estudiante Sencilla:** Un formulario simple para que los estudiantes introduzcan sus credenciales.
*   **Web Scraping Automatizado:** Utiliza Selenium para navegar por el portal de la universidad, iniciar sesión y extraer los datos personales y el horario del estudiante.
*   **Procesamiento Asíncrono:** Gracias a Celery y Redis, las solicitudes de scraping (que pueden tardar) se procesan en segundo plano, manteniendo la interfaz de usuario ágil.
*   **Base de Datos en la Nube:** Almacena toda la información de forma segura en Google Firestore.
*   **Panel de Administrador Seguro:** Una interfaz protegida por contraseña para ejecutar el algoritmo de matchmaking.
*   **Algoritmo de Matchmaking Inteligente:** Analiza los horarios para encontrar la primera y la última clase de cada estudiante por día, identificando así grupos de viaje compatibles.

---

## 🏗️ Arquitectura Tecnológica

*   **Frontend:** HTML5 con CSS simple, renderizado por el motor de plantillas Jinja2 de Flask.
*   **Backend (Servidor Web):** **Flask**, un micro-framework de Python ligero y potente.
*   **Web Scraping:** **Selenium** para controlar un navegador Chrome en modo headless.
*   **Cola de Tareas:** **Celery** para gestionar las tareas de scraping de larga duración.
*   **Intermediario de Mensajes (Broker):** **Redis**, que actúa como la cola donde Celery deposita y recoge las tareas.
*   **Base de Datos:** **Google Firestore**, una base de datos NoSQL, flexible y escalable.

---

## 🚀 Guía de Instalación y Puesta en Marcha

Sigue estos pasos para ejecutar el proyecto en tu máquina local.

### 1. Prerrequisitos

*   **Python 3.9** o superior.
*   **Git** para clonar el repositorio.
*   **Redis Server:** Sigue la [guía de instalación para Windows](https://github.com/tporadowski/redis/releases) (descarga el archivo `.msi` más reciente).

### 2. Configuración del Proyecto

**a. Clonar el Repositorio**
```bash
git clone https://github.com/tu-usuario/PUG.git
cd PUG
```

**b. Crear y Activar un Entorno Virtual**
```bash
# Crear el entorno
python -m venv venv
# Activar en Windows
.\venv\Scripts\activate
# Activar en macOS/Linux
# source venv/bin/activate
```

**c. Instalar Dependencias**
```bash
pip install -r requirements.txt
```

**d. Configurar Credenciales de Firebase**
1.  Obtén tu archivo de credenciales de servicio de Firebase (un archivo `.json`).
2.  Renómbralo a `credenciales.json`.
3.  Colócalo en la **raíz del directorio del proyecto**.

**e. Configurar Variables de Entorno**
1.  Crea un archivo llamado `.env` en la raíz del proyecto.
2.  Añade una clave secreta para Flask. Puedes generar una con `python -c 'import secrets; print(secrets.token_hex())'`.
    ```env
    # .env
    FLASK_SECRET_KEY='pega-aqui-tu-clave-generada'
    ```

---

## ▶️ Cómo Ejecutar la Aplicación

Para que la aplicación funcione, necesitas tener **3 terminales abiertas simultáneamente** (con el entorno virtual `(venv)` activado en cada una).

**Terminal 1: Iniciar el Servidor Redis**
*   Si instalaste Redis como un servicio de Windows, ya debería estar ejecutándose.
*   Si no, inicia el servidor manualmente: `redis-server`
*Deja esta terminal abierta.*

**Terminal 2: Iniciar el Worker de Celery**
Este es el trabajador que procesará las tareas. **¡Comando corregido!**
```bash
# La tarea está en app.py, por lo que usamos app.celery
celery -A app.celery worker --loglevel=info --pool=solo
```
*El parámetro `--pool=solo` es importante para la compatibilidad con Windows. Deja esta terminal abierta para ver los logs de las tareas.*

**Terminal 3: Iniciar el Servidor Web Flask**
```bash
python app.py
```
*Deja esta terminal abierta.*

---

## 💻 Cómo Usar la Aplicación

**Para Estudiantes:**
1.  Abre tu navegador y ve a `http://127.0.0.1:5000/`.
2.  Introduce tu usuario (matrícula) y contraseña del portal.
3.  Haz clic en "Actualizar mi Horario". Serás redirigido a una página para revisar los datos extraídos.
4.  Completa la información adicional (como la licencia de conducir) y haz clic en "Confirmar y Guardar".
5.  Tus datos se guardarán en Firestore y serás redirigido a la página principal con un mensaje de éxito.

**Para Administradores:**
1.  **Crea un hash de contraseña:** Ejecuta `python hash_pass.py` y sigue las instrucciones para generar un hash seguro.
2.  **Configura el admin en Firestore:** Ve a tu base de datos, busca el documento del usuario, y añade/actualiza los campos `password_hash` (con el hash generado) y `rol` (con el valor `Admin`).
3.  **Inicia Sesión:** Ve a `http://127.0.0.1:5000/admin`, introduce la matrícula y la contraseña del administrador.
4.  **Ejecuta el Matchmaking:** Una vez dentro, haz clic en "Encontrar Grupos de Viaje". Los resultados aparecerán en la misma página.

---

## 📂 Estructura del Proyecto (Actualizada)

```
.
├── src/
│   ├── app.py                # App Flask, rutas y tarea Celery
│   ├── constants.py          # Selectores CSS para el scraper
│   ├── main.py               # Scraper de Selenium (lógica principal)
│   └── matchmaking.py        # Algoritmo para encontrar grupos
├── templates/
│   ├── admin.html            # Panel de administrador (con login y resultados)
│   ├── index.html            # Página de inicio para estudiantes
│   └── revisar.html          # Página para revisar y completar datos
├── .env                      # Variables de entorno (ignoradas por Git)
├── .gitignore                # Archivos a ignorar por Git
├── credenciales.json         # Credenciales de Firebase (ignoradas por Git)
├── hash_pass.py              # Utilidad para crear contraseñas de admin
├── LICENSE                   # Licencia del proyecto (AGPLv3)
└── requirements.txt          # Dependencias de Python
```

---

## 📜 Licencia

Este proyecto está licenciado bajo la **Licencia Pública General de Affero GNU v3.0 (AGPLv3)**. Esto asegura que cualquier modificación o uso del código en un servicio de red también debe permanecer como software libre. Consulta el archivo `LICENSE` para más detalles.

---

## 📧 Contacto

**Jose Luis Giraldo Vasquez** - *Encuéntrame en GitHub*
