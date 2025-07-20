from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from datetime import datetime
import json
import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import check_password_hash
from celery import Celery

# NO importamos desde .tasks aquí para evitar la dependencia circular
# from .tasks import run_scraping_task 
from .matchmaking import run_matchmaking_logic

# --- CONFIGURACIÓN INICIAL ---
load_dotenv()
app = Flask(__name__, template_folder='../templates')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key-for-dev')

# Conectamos Flask a la misma configuración de Celery que usa tasks.py
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

# --- INICIALIZACIÓN DE FIREBASE (MEJORADA) ---
db = None
try:
    cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'credenciales.json')
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase inicializado correctamente.")
except Exception as e:
    print(f"Error Crítico: No se pudo inicializar Firebase. Verifica el archivo de credenciales. Error: {e}")

# --- DECORADOR DE AUTORIZACIÓN ---
def login_required(role="Admin"):
    """
    Decorador que verifica si un usuario ha iniciado sesión y tiene el rol requerido.
    """
    @wraps(role)
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Debes iniciar sesión para acceder a esta página.", "error")
                return redirect(url_for('admin_login'))
            
            user_role = session.get('user_role')
            
            role_hierarchy = {
                "User": 0,
                "Admin": 1,
                "Super Admin": 2,
                "Alpha Prime": 3
            }

            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(role, 1):
                flash("No tienes los permisos necesarios para acceder a esta página.", "error")
                return redirect(url_for('admin_dashboard'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- RUTAS DE ESTUDIANTE ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extraer-datos', methods=['POST'])
def extraer_datos():
    usuario = request.form.get('usuario')
    contrasena = request.form.get('contrasena')

    if not usuario or not contrasena:
        flash("El usuario y la contraseña son obligatorios.", "error")
        return redirect(url_for('index'))

    try:
        # --- CAMBIO CLAVE ---
        # Llamamos a la tarea por su nombre (string) en lugar de por el objeto importado
        task = celery_app.send_task('tasks.run_scraping_task', args=[usuario, contrasena])
        
        # .get() sigue funcionando igual para esperar el resultado
        resultado_json_str = task.get(timeout=120)
        datos_extraidos = json.loads(resultado_json_str)

        if datos_extraidos.get("error"):
            flash(f"Error durante la extracción: {datos_extraidos['error']}", "error")
            return redirect(url_for('index'))

        return render_template('revisar.html', datos=datos_extraidos)

    except Exception as e:
        flash(f"Ocurrió un error al procesar tu solicitud: {e}", "error")
        return redirect(url_for('index'))

@app.route('/guardar-horario', methods=['POST'])
def guardar_horario():
    if not db:
        flash("Error de conexión con la base de datos. Inténtalo más tarde.", "error")
        return redirect(url_for('index'))
    
    try:
        matricola = request.form.get('matricola')
        if not matricola:
            raise ValueError("Falta la matrícula. No se puede guardar.")
            
        guardar_datos_estudiante_en_db(matricola, request.form)
        
        flash("¡Tus datos han sido guardados con éxito!", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        flash(f"Ocurrió un error inesperado al guardar tus datos: {e}", "error")
    
    return redirect(url_for('index'))

# --- RUTAS DE ADMINISTRADOR ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')

        if not user_id or not password:
            flash("El ID de usuario y la contraseña son obligatorios.", "error")
            return redirect(url_for('admin_login'))

        if not db:
            flash("Error de conexión con la base de datos.", "error")
            return redirect(url_for('admin_login'))

        try:
            user_ref = db.collection('estudiantes').document(user_id).get()
            if user_ref.exists:
                user_data = user_ref.to_dict()
                user_role = user_data.get('rol', 'User')
                
                if user_data.get('password_hash') and check_password_hash(user_data['password_hash'], password):
                    if user_role in ["Admin", "Super Admin", "Alpha Prime"]:
                        session['user_id'] = user_id
                        session['user_role'] = user_role
                        session['user_name'] = user_data.get('nome', 'Admin')
                        return redirect(url_for('admin_dashboard'))
                    else:
                        flash("Acceso denegado. No tienes un rol de administrador.", "error")
                else:
                    flash("ID de usuario o contraseña incorrectos.", "error")
            else:
                flash("ID de usuario o contraseña incorrectos.", "error")
        except Exception as e:
            flash(f"Error al iniciar sesión: {e}", "error")

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@login_required(role="Admin")
def admin_dashboard():
    return render_template('admin.html', user_role=session.get('user_role'))

@app.route('/admin')
def admin_redirect():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash("Has cerrado la sesión.", "info")
    return redirect(url_for('admin_login'))

@app.route('/ejecutar-matchmaking', methods=['POST'])
@login_required(role="Admin")
def ejecutar_matchmaking():
    try:
        resultado_stdout = run_matchmaking_logic()
        return jsonify(titulo="Resultado del Matchmaking", salida=resultado_stdout)
    except Exception as e:
        return jsonify(titulo="Error en el Matchmaking", salida=str(e)), 500

# --- FUNCIONES HELPER ---
def guardar_datos_estudiante_en_db(matricola, form_data):
    tiene_licencia = form_data.get('tiene_licencia')
    datos_conduccion = {"tiene_licencia": False, "tipos_licencia": [], "vencimiento_licencia": None}
    
    if tiene_licencia == 'si':
        tipos = form_data.getlist('tipo_licencia')
        vencimiento_str = form_data.get('vencimiento_licencia')
        if not tipos or not vencimiento_str:
            raise ValueError("Si tienes licencia, debes seleccionar al menos un tipo y la fecha de vencimiento.")
        vencimiento_dt = datetime.strptime(vencimiento_str, '%Y-%m-%d').date()
        if vencimiento_dt < datetime.now().date():
            raise ValueError("La fecha de vencimiento de la licencia no puede ser una fecha pasada.")
        datos_conduccion["tiene_licencia"] = True
        datos_conduccion["tipos_licencia"] = tipos
        datos_conduccion["vencimiento_licencia"] = vencimiento_str

    estudiante_ref = db.collection('estudiantes').document(matricola)
    doc = estudiante_ref.get()
    rol_actual = doc.to_dict().get('rol') if doc.exists else None

    perfil_completo = {
        'nome': form_data.get('nome'), 
        'cognome': form_data.get('cognome'),
        'informacion_conduccion': datos_conduccion,
        'ultima_actualizacion': firestore.SERVER_TIMESTAMP
    }
    if not rol_actual:
        perfil_completo['rol'] = 'User'

    estudiante_ref.set(perfil_completo, merge=True)
    
    horario_str = form_data.get('horario_json')
    horario_data = json.loads(horario_str)
    horario_antiguo_ref = estudiante_ref.collection('horario')
    for doc in horario_antiguo_ref.stream():
        doc.reference.delete()
    if horario_data:
        for clase in horario_data:
            horario_antiguo_ref.add(clase)

# --- PUNTO DE ENTRADA PARA EJECUTAR LA APLICACIÓN ---
if __name__ == '__main__':
    # Este bloque es esencial para iniciar el servidor de desarrollo de Flask.
    # El host '0.0.0.0' lo hace accesible desde otros dispositivos en tu red.
    app.run(host='0.0.0.0', port=5000, debug=True)