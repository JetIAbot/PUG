# tasks.py

import json
import logging
from celery import Celery
from .main import realizar_scraping

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURACIÓN DE CELERY ---
# Asegúrate de que Redis esté corriendo en localhost:6379
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# --- TAREA DE CELERY ---
@celery_app.task(name='tasks.run_scraping_task')
def run_scraping_task(usuario: str, contrasena: str) -> str:
    """
    Tarea de Celery que ejecuta la función de scraping y devuelve el resultado como JSON.
    """
    logging.info(f"Iniciando tarea de scraping para el usuario: {usuario}")
    try:
        datos_extraidos = realizar_scraping(usuario, contrasena)
        logging.info(f"Tarea de scraping completada con éxito para: {usuario}")
        return json.dumps(datos_extraidos)
    except Exception as e:
        # La función de scraping ya registró el error, aquí solo lo empaquetamos para Flask.
        logging.error(f"La tarea de scraping falló para {usuario}. Error: {e}")
        # Devolvemos un JSON de error claro para que la interfaz lo muestre.
        return json.dumps({"error": str(e)})