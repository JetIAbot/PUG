# tasks.py

import subprocess
import sys
import json
import firebase_admin
from firebase_admin import credentials, firestore
from celery import Celery
import logging

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURACIÓN DE CELERY ---
# Asegúrate de que Redis esté corriendo en localhost:6379
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# --- LÓGICA DE FIREBASE ---
def initialize_firebase_in_task():
    """Inicializa Firebase si no existe una app, ideal para workers de Celery."""
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate("credenciales.json")
            firebase_admin.initialize_app(cred)
            logging.info("Firebase inicializado en el worker de Celery.")
        except Exception as e:
            logging.error(f"Error al inicializar Firebase en el worker: {e}")
    return firestore.client()

# --- TAREA DE CELERY ---
@celery_app.task(name='tasks.run_scraping_task')
def run_scraping_task(usuario, contrasena):
    """
    Tarea de Celery que ejecuta el script de scraping, procesa su salida
    y guarda los resultados directamente en Firestore.
    """
    logging.info(f"Iniciando tarea de scraping para el usuario: {usuario}")
    db = initialize_firebase_in_task()
    if not db:
        logging.error("No se pudo obtener la instancia de Firestore. Abortando tarea.")
        return {"status": "error", "message": "No se pudo conectar a Firestore."}

    try:
        # 1. Ejecutar el script main.py como un subproceso
        resultado_proceso = subprocess.run(
            [sys.executable, 'main.py', '--usuario', usuario, '--contrasena', contrasena],
            capture_output=True, text=True, check=True, encoding='utf-8', errors='replace'
        )
        
        datos_extraidos = json.loads(resultado_proceso.stdout)

        # 2. Validar la salida del script
        if datos_extraidos.get("error"):
            logging.error(f"El script de scraping devolvió un error para {usuario}: {datos_extraidos['error']}")
            return {"status": "error", "message": datos_extraidos['error']}

        datos_personales = datos_extraidos.get("datos_personales")
        horario_data = datos_extraidos.get("horario")

        if not datos_personales or not datos_personales.get('matricola'):
            logging.error(f"No se encontraron datos personales válidos para {usuario}.")
            return {"status": "error", "message": "Datos personales no encontrados."}

        # 3. Guardar los datos en Firestore
        matricola = datos_personales['matricola']
        estudiante_ref = db.collection('estudiantes').document(matricola)
        
        perfil_data = {'nome': datos_personales['nome'], 'cognome': datos_personales['cognome']}
        estudiante_ref.set(perfil_data, merge=True)
        logging.info(f"Perfil guardado para {matricola}.")

        # Borrar horario antiguo y guardar el nuevo si existe
        horario_ref = estudiante_ref.collection('horario')
        for doc in horario_ref.stream():
            doc.reference.delete()
        
        if horario_data:
            for clase in horario_data:
                horario_ref.add(clase)
            logging.info(f"Horario con {len(horario_data)} clases guardado para {matricola}.")
        else:
            logging.info(f"Horario vacío para {matricola}. Se limpió el horario existente.")

        logging.info(f"Tarea de scraping completada con éxito para: {usuario}")
        return {"status": "success", "matricola": matricola}

    except subprocess.CalledProcessError as e:
        error_output = e.stderr or e.stdout
        logging.error(f"El script de scraping falló para {usuario}. Error: {error_output}")
        return {"status": "error", "message": f"Subprocess error: {error_output}"}
    except json.JSONDecodeError:
        logging.error(f"No se pudo decodificar la salida JSON del script para {usuario}.")
        return {"status": "error", "message": "Invalid JSON output from scraper."}
    except Exception as e:
        logging.error(f"Ocurrió un error inesperado en la tarea para {usuario}: {e}")
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}