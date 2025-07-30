import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from celery import Celery
from functools import wraps
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from werkzeug.security import check_password_hash
import logging
from dotenv import load_dotenv
import time
# Importar el módulo de matchmaking
from src import matchmaking
# Importar validadores y logger de seguridad
from src.validators import FormValidator, ValidationError
from src.logger_config import security_logger

# --- FÁBRICA DE CELERY ---
def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# --- FÁBRICA DE LA APLICACIÓN FLASK ---
def create_app(config=None):
    app = Flask(__name__, template_folder='../templates')
    
    # Configuración por defecto
    app.config.from_mapping(
        SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'dev'),
        CELERY_BROKER_URL='redis://localhost:6379/0',
        CELERY_RESULT_BACKEND='redis://localhost:6379/0'
    )
    
    # Aplicar configuración personalizada si se proporciona
    if config:
        app.config.update(config)
    
    # Inicializar Firebase dentro de la fábrica (solo si no es testing)
    if not app.config.get('TESTING', False):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate("credenciales.json")
                firebase_admin.initialize_app(cred)
            # No asignamos db globalmente, lo manejaremos a través del contexto de la app si es necesario
        except Exception as e:
            app.logger.error(f"Error Crítico: No se pudo inicializar Firebase. Error: {e}")

    # Registrar las rutas (blueprints) o adjuntarlas aquí
    # Por simplicidad, mantendremos las rutas en este archivo por ahora.
    # Las rutas que usan 'app' ahora usarán 'current_app' o se definirán dentro de la fábrica.

    return app

# --- INICIALIZACIÓN ---
# Variables globales - se inicializan solo cuando no estamos en modo test
app = None
celery_app = None
db = None

def initialize_app():
    """Inicializar la aplicación y sus servicios"""
    global app, celery_app, db
    
    if app is None:
        load_dotenv()
        app = create_app()
        celery_app = make_celery(app)
        
        # Solo inicializar Firebase si no estamos en modo test
        import os
        if not os.environ.get('TESTING'):
            db = firestore.client()

# --- MIDDLEWARE DE LOGGING ---
@app.before_request
def log_request():
    """Log de todas las requests"""
    request.start_time = time.time()
    
    # Log de requests sensibles
    if request.endpoint in ['extraer_datos', 'admin_login', 'guardar_horario']:
        security_logger.log_security_event(
            'request_received',
            {
                'endpoint': request.endpoint,
                'method': request.method,
                'user_agent': request.headers.get('User-Agent')
            },
            session.get('matricola'),
            request.remote_addr
        )

@app.after_request
def log_response(response):
    """Log de responses"""
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        
        # Log responses de endpoints críticos
        if request.endpoint in ['extraer_datos', 'admin_login']:
            security_logger.log_security_event(
                'request_completed',
                {
                    'endpoint': request.endpoint,
                    'status_code': response.status_code,
                    'duration_seconds': round(duration, 3)
                },
                session.get('matricola'),
                request.remote_addr
            )
    
    return response

# --- TAREA DE CELERY ---
# La tarea ahora se define usando la instancia 'celery_app' creada por la fábrica
@celery_app.task(name='src.app.run_scraping_task')
def run_scraping_task(matricula, password):
    """
    Tarea de Celery que ejecuta el proceso de scraping.
    """
    # CORRECCIÓN: Importar la función orquestadora desde main.py.
    # Se usa un alias para evitar un conflicto de nombres con esta misma función de tarea.
    from src.main import run_scraping_task as perform_scraping

    # Llamar a la función correcta del módulo correcto.
    return perform_scraping(matricula, password)

# --- SECCIÓN DE AUTENTICACIÓN Y AUTORIZACIÓN (RESTAURADA) ---
def login_required(role="Admin"):
    """Decorador que verifica si un usuario ha iniciado sesión y tiene el rol requerido."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Debes iniciar sesión para acceder a esta página.", "error")
                return redirect(url_for('admin_login'))
            
            user_role = session.get('user_role')
            role_hierarchy = {"User": 0, "Admin": 1, "Super Admin": 2, "Alpha Prime": 3}

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
    start_time = time.time()
    matricola = None
    
    try:
        # Validar datos del formulario
        validation_result = FormValidator.validate_student_form(request.form)
        
        if not validation_result['valid']:
            # Log intento con datos inválidos
            security_logger.log_security_event(
                'invalid_form_submission',
                {
                    'errors': validation_result['errors'],
                    'endpoint': 'extraer_datos'
                },
                request.form.get('matricola'),
                request.remote_addr
            )
            
            # Retornar errores de validación
            flash('Errores en el formulario:', 'error')
            for field, errors in validation_result['errors'].items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
            return redirect(url_for('index'))
        
        # Usar datos limpios
        matricola = validation_result['cleaned_data']['matricola']
        password = request.form.get('contrasena') or request.form.get('password')
        
        if not password:
            flash('La contraseña es obligatoria', 'error')
            return redirect(url_for('index'))
        
        # Logging de seguridad
        security_logger.app_logger.info(f"Iniciando extracción para matrícula: {matricola}")
        
        # CORRECCIÓN: Llamar a la tarea de forma asíncrona y redirigir.
        # Se usa el nombre explícito de la tarea para evitar errores.
        task = celery_app.send_task('src.app.run_scraping_task', args=[matricola, password])
        
        # Guardamos el ID de la tarea en la sesión para poder consultar su estado después.
        session['task_id'] = task.id
        session['matricola'] = matricola
        
        # Log inicio de extracción
        security_logger.log_data_extraction(
            matricola, 
            True, 
            duration=time.time() - start_time
        )
        
        # Redirigimos a una página de espera o de revisión.
        # Asumimos que la página 'revisar' puede manejar la espera.
        return redirect(url_for('revisar'))
        
    except Exception as e:
        # Log error detallado
        security_logger.log_error(e, {
            'endpoint': 'extraer_datos',
            'matricola': matricola,
            'duration': time.time() - start_time
        })
        
        current_app.logger.error(f"Error al iniciar la tarea Celery: {e}")
        flash("Error interno del servidor", "error")
        return redirect(url_for('index'))

# --- NUEVA RUTA DE REVISIÓN Y ESTADO ---
@app.route('/revisar')
def revisar():
    """
    Muestra la página de espera/revisión. Pasa el ID de la tarea a la plantilla.
    """
    task_id = session.get('task_id')
    if not task_id:
        flash("No se ha iniciado ninguna tarea de extracción de datos.", "warning")
        return redirect(url_for('index'))
    return render_template('revisar.html', task_id=task_id)

@app.route('/task-status/<task_id>')
def task_status(task_id):
    """
    Endpoint de API para consultar el estado de una tarea de Celery.
    """
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'SUCCESS':
        # La tarea terminó correctamente. El resultado está en task.result.
        # El resultado de ejecutar_scraping es un string JSON, lo parseamos.
        try:
            # El resultado de la tarea es un string JSON, lo convertimos a un objeto.
            result_data = json.loads(task.result)
            # Si el scraping devolvió un error interno, lo tratamos como una falla.
            if 'error' in result_data:
                 response = {
                    'state': 'FAILURE',
                    'status': result_data['error']
                }
            else:
                response = {
                    'state': task.state,
                    'result': result_data
                }
        except (json.JSONDecodeError, TypeError):
             # Esto ocurre si la tarea devuelve algo que no es JSON válido.
             response = {
                'state': 'FAILURE',
                'status': f"Error interno: La tarea devolvió un formato inesperado."
            }

    elif task.state == 'FAILURE':
        # La tarea falló. La información del error está en task.info.
        response = {
            'state': task.state,
            'status': str(task.info),  # task.info contiene la excepción.
        }
    elif task.state == 'PENDING':
        # La tarea aún no ha sido recogida por un worker.
        response = {'state': task.state, 'status': 'Tarea pendiente...'}
    else:
        # La tarea está en un estado intermedio (ej. PROGRESS, RETRY).
        response = {
            'state': task.state,
            'status': str(task.info) # Devolvemos la info que haya (ej. 'Procesando...')
        }
        
    return jsonify(response)


# --- RUTA DE GUARDADO (RESTAURADA Y CRÍTICA) ---
@app.route('/guardar_horario', methods=['POST'])
def guardar_horario():
    """
    Recibe los datos del formulario de revisión y los guarda en Firestore.
    """
    try:
        # Extraemos los datos personales del formulario
        matricola = request.form['matricola']
        nome = request.form['nome']
        cognome = request.form['cognome']
        data_nascita = request.form['data_nascita']

        # El horario viene como un string JSON, lo parseamos
        horario_json = request.form.get('horario_json')
        horario = json.loads(horario_json) if horario_json else []

        # --- PROCESO DE LICENCIA MEJORADO Y VALIDADO ---
        tiene_licencia = request.form.get('tiene_licencia') == 'si'
        tipo_licencia = request.form.getlist('tipo_licencia') if tiene_licencia else []
        vencimiento_licencia_str = request.form.get('vencimiento_licencia')
        
        vencimiento_licencia_dt = None
        if tiene_licencia and vencimiento_licencia_str:
            try:
                # 1. VALIDACIÓN: Intentamos convertir el texto a un objeto de fecha.
                # Si el formato es incorrecto (ej. 'hola'), lanzará un error.
                vencimiento_licencia_dt = datetime.strptime(vencimiento_licencia_str, '%Y-%m-%d')
            except ValueError:
                # Si la validación falla, informamos al usuario y detenemos el proceso.
                flash(f"El formato de la fecha de vencimiento ('{vencimiento_licencia_str}') no es válido. Por favor, usa el formato AAAA-MM-DD.", 'danger')
                # Lo ideal sería devolver al usuario a la página de revisión con los datos
                # ya cargados, pero por simplicidad lo redirigimos al inicio.
                return redirect(url_for('index'))

        # Preparamos el documento para Firestore
        doc_ref = db.collection('estudiantes').document(matricola)
        
        datos_a_guardar = {
            'nome': nome,
            'cognome': cognome,
            'data_nascita': data_nascita,
            'horario': horario,
            'tiene_licencia': tiene_licencia,
            'tipo_licencia': tipo_licencia,
            # 2. TIPO DE DATO CORRECTO: Guardamos el objeto de fecha (o None).
            # Firestore lo convertirá automáticamente a un Timestamp.
            'vencimiento_licencia': vencimiento_licencia_dt,
            'ultima_actualizacion': firestore.SERVER_TIMESTAMP
        }

        doc_ref.set(datos_a_guardar, merge=True)

        flash('¡Tus datos y horario se han guardado correctamente!', 'success')
        return redirect(url_for('index'))

    except Exception as e:
        logging.error(f"Error al guardar en Firestore: {e}")
        flash('Hubo un error al intentar guardar tus datos. Por favor, inténtalo de nuevo.', 'danger')
        return redirect(url_for('index'))

# --- RUTAS DE ADMINISTRADOR (RESTAURADAS Y PROTEGIDAS) ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        matricola = request.form.get('user_id') or request.form.get('matricola')
        password = request.form.get('password')
        
        try:
            # Log intento de login
            security_logger.log_login_attempt(
                matricola,
                False,  # Asumimos fallo hasta verificar
                request.remote_addr,
                request.headers.get('User-Agent')
            )
            
            # Validación del formulario
            validation_result = FormValidator.validate_admin_form({
                'matricola': matricola,
                'password': password
            })
            
            if not validation_result['valid']:
                security_logger.log_security_event(
                    'admin_login_validation_failed',
                    {'errors': validation_result['errors']},
                    matricola,
                    request.remote_addr
                )
                
                for field, errors in validation_result['errors'].items():
                    for error in errors:
                        flash(f'Error: {error}', 'error')
                return redirect(url_for('admin_login'))
            
            # Verificar en Firestore
            user_ref = db.collection('estudiantes').document(matricola).get()
            if user_ref.exists:
                user_data = user_ref.to_dict()
                stored_hash = user_data.get('password_hash')
                user_role = user_data.get('rol', 'User')
                
                if stored_hash and check_password_hash(stored_hash, password):
                    if user_role in ["Admin", "Super Admin", "Alpha Prime"]:
                        # Login exitoso
                        session['user_id'] = matricola
                        session['user_role'] = user_role
                        session['user_name'] = user_data.get('nome', 'Admin')
                        
                        # Log login exitoso
                        security_logger.log_login_attempt(
                            matricola,
                            True,
                            request.remote_addr,
                            request.headers.get('User-Agent')
                        )
                        
                        security_logger.log_admin_action(
                            matricola,
                            'login_successful',
                            details={'role': user_role}
                        )
                        
                        return redirect(url_for('admin_dashboard'))
                    else:
                        # Usuario sin permisos de admin
                        security_logger.log_security_event(
                            'unauthorized_admin_attempt',
                            {'user_role': user_role},
                            matricola,
                            request.remote_addr
                        )
            
            # Login fallido
            security_logger.log_security_event(
                'admin_login_failed',
                {'reason': 'invalid_credentials'},
                matricola,
                request.remote_addr
            )
            
            flash("Credenciales incorrectas o sin permisos de administrador.", "error")
            
        except Exception as e:
            security_logger.log_error(e, {
                'endpoint': 'admin_login',
                'matricola': matricola
            })
            
            flash(f"Error al iniciar sesión: {e}", "error")
            
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash("Has cerrado la sesión.", "info")
    return redirect(url_for('admin_login'))

@app.route('/admin')
def admin_redirect():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required(role="Admin")
def admin_dashboard():
    return render_template('admin.html', user_role=session.get('user_role'))

@app.route('/ejecutar-matchmaking', methods=['POST'])
@login_required(role="Admin")
def ejecutar_matchmaking():
    try:
        # MEJORA: Llamar a la función directamente. Es más limpio y eficiente.
        resultado_str = matchmaking.realizar_matchmaking()
        return jsonify(titulo="Resultado del Matchmaking", salida=resultado_str)
    except Exception as e:
        current_app.logger.error(f"Error ejecutando matchmaking: {e}")
        return jsonify(titulo="Error inesperado", salida=str(e)), 500

# --- PUNTO DE ENTRADA ---
if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=5000, debug=True)