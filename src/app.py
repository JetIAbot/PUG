from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import subprocess
import sys
import json
import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv
from tasks import run_scraping_task
from matchmaking import run_matchmaking_logic

# Cargar variables de entorno desde .env
load_dotenv()

# Inicializamos la aplicación Flask
# Se especifica la ruta a la carpeta de plantillas, que está un nivel arriba de 'src'
app = Flask(__name__, template_folder='../templates')
# MEJORA DE SEGURIDAD: La clave secreta se carga desde variables de entorno
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'una-clave-secreta-por-defecto-solo-para-desarrollo')

# Inicializamos Firebase en la app web
cred = credentials.Certificate("credenciales.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


# --- Interfaz para el Estudiante ---
@app.route('/')
def index():
    """Página principal para el usuario/estudiante."""
    return render_template('index.html')

@app.route('/extraer-datos', methods=['POST'])
def extraer_datos():
    """Recibe las credenciales y encola la tarea de scraping."""
    usuario = request.form.get('usuario')
    contrasena = request.form.get('contrasena')

    if not usuario or not contrasena:
        flash("El usuario y la contraseña son obligatorios.", "error")
        return redirect(url_for('index'))

    # En vez de ejecutar el script directamente, llamamos a la tarea de Celery
    run_scraping_task.delay(usuario, contrasena)
    flash("¡Solicitud recibida! Tus datos se están procesando en segundo plano y se guardarán automáticamente.")
    return redirect(url_for('index'))

# La ruta /guardar-horario y la página revisar.html ya no son necesarias en este flujo,
# ya que la tarea de Celery se encarga de todo el proceso de forma automática.

# --- Interfaz para el Administrador ---
@app.route('/admin')
def admin():
    """Página principal para el administrador."""
    return render_template('admin.html')

@app.route('/ejecutar-matchmaking', methods=['POST'])
def ejecutar_matchmaking():
    """Ejecuta la lógica de matchmaking y devuelve el resultado."""
    try:
        # Llamada directa a la función de matchmaking
        resultado_stdout = run_matchmaking_logic()
        return jsonify(titulo="Resultado del Matchmaking", salida=resultado_stdout)
    except Exception as e:
        # Captura cualquier excepción que la lógica de matchmaking pueda lanzar
        return jsonify(titulo="Error inesperado en Matchmaking", salida=str(e)), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)