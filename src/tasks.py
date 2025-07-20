# tasks.py

from celery import Celery
import json
import logging
from .main import realizar_scraping

# --- CONFIGURACIÓN DE LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURACIÓN DE CELERY ---
# Esta configuración debe ser idéntica a la de app.py
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@celery_app.task(name='tasks.run_scraping_task')
def run_scraping_task(usuario, contrasena):
    """
    Tarea de Celery que llama directamente a la función de scraping.
    Esto es más eficiente y robusto que usar un subproceso.
    """
    logging.info(f"Iniciando tarea de scraping para el usuario: {usuario}")
    try:
        # Llamada directa a la función, no más subprocesos
        datos_extraidos = realizar_scraping(usuario, contrasena)
        
        logging.info(f"Tarea de scraping completada con éxito para: {usuario}")
        # Devolvemos el resultado como una cadena JSON para que Flask lo reciba
        return json.dumps(datos_extraidos)

    except Exception as e:
        # Cualquier excepción lanzada por la función de scraping será capturada aquí
        error_message = f"Error durante el scraping para {usuario}: {e}"
        logging.error(error_message)
        # Devolvemos un JSON de error claro
        return json.dumps({"error": str(e)})