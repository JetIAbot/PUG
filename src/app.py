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
import atexit

# Importar el módulo de matchmaking
import matchmaking
# Importar validadores y logger de seguridad
from validators import FormValidator, ValidationError
from logger_config import security_logger
from log_cleaner import setup_automatic_cleanup

# Cargar variables de entorno
load_dotenv()

# Configurar limpieza automática de logs al iniciar
log_cleaner = setup_automatic_cleanup()

# Configurar limpieza al cerrar la aplicación
def cleanup_on_exit():
    """Ejecutar limpieza al cerrar la aplicación"""
    if os.getenv('AUTO_CLEANUP', 'True').lower() == 'true':
        log_cleaner.clean_old_logs()

atexit.register(cleanup_on_exit)

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

# --- DECORADORES ---
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('admin_login'))
            
            if role and session.get('user_role') != role:
                flash('No tienes permisos para acceder a esta página.')
                return redirect(url_for('admin_login'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- FÁBRICA DE LA APLICACIÓN FLASK ---
def create_app(config=None):
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
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
        except Exception as e:
            app.logger.error(f"Error Crítico: No se pudo inicializar Firebase. Error: {e}")
    
    # Variable para la base de datos
    if not app.config.get('TESTING', False):
        try:
            db = firestore.client()
            app.config['db'] = db
        except Exception:
            app.config['db'] = None
    
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
    
    # --- RUTAS ---
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/extraer_datos', methods=['POST'])
    def extraer_datos():
        try:
            # Validación de entrada
            validator = FormValidator()
            
            matricola = request.form.get('matricola', '').strip()
            password = request.form.get('password', '').strip()
            
            # Validar datos
            validation_result = validator.validate_student_form({
                'matricola': matricola,
                'password': password
            })
            
            if not validation_result['valid']:
                security_logger.log_security_event(
                    'validation_failed',
                    {'errors': validation_result['errors'], 'matricola': matricola},
                    matricola,
                    request.remote_addr
                )
                
                # Crear lista de errores para mostrar al usuario
                error_messages = []
                for field, field_errors in validation_result['errors'].items():
                    if isinstance(field_errors, list):
                        error_messages.extend(field_errors)
                    else:
                        error_messages.append(str(field_errors))
                
                return jsonify({
                    'titulo': 'Error de Validación',
                    'salida': 'Datos no válidos: ' + ', '.join(error_messages)
                }), 400
            
            # Log intento de extracción
            security_logger.log_security_event(
                'data_extraction_attempt',
                {'matricola': matricola},
                matricola,
                request.remote_addr
            )
            
            # Crear tarea de Celery
            task = extraer_datos_task.delay(matricola, password)
            
            security_logger.log_security_event(
                'data_extraction_task_created',
                {
                    'task_id': task.id,
                    'matricola': matricola
                },
                matricola,
                request.remote_addr
            )
            
            return jsonify({
                'titulo': 'Procesando...',
                'salida': f'Procesando datos para {matricola}. ID de tarea: {task.id}',
                'task_id': task.id
            })
            
        except Exception as e:
            current_app.logger.error(f"Error en extraer_datos: {e}")
            security_logger.log_security_event(
                'extraction_error',
                {'error': str(e)},
                request.form.get('matricola'),
                request.remote_addr
            )
            return jsonify({
                'titulo': 'Error',
                'salida': 'Error interno del servidor'
            }), 500

    @app.route('/check_task/<task_id>')
    def check_task(task_id):
        try:
            task = extraer_datos_task.AsyncResult(task_id)
            
            if task.state == 'PENDING':
                response = {
                    'state': task.state,
                    'status': 'Tarea pendiente...'
                }
            elif task.state == 'SUCCESS':
                response = {
                    'state': task.state,
                    'result': task.result
                }
            else:
                response = {
                    'state': task.state,
                    'status': str(task.info)
                }
            
            return jsonify(response)
            
        except Exception as e:
            current_app.logger.error(f"Error verificando tarea {task_id}: {e}")
            return jsonify({'error': 'Error verificando tarea'}), 500

    @app.route('/guardar_horario', methods=['POST'])
    def guardar_horario():
        try:
            datos = request.get_json()
            matricola = datos.get('matricola')
            horarios = datos.get('horarios', [])
            
            # Validar datos
            validator = FormValidator()
            errors = validator.validate_schedule_data({
                'matricola': matricola,
                'horarios': horarios
            })
            
            if errors:
                security_logger.log_security_event(
                    'schedule_validation_failed',
                    {'errors': errors},
                    matricola,
                    request.remote_addr
                )
                return jsonify({'error': 'Datos no válidos'}), 400
            
            # Obtener referencia a la base de datos
            db = current_app.config.get('db')
            if not db:
                return jsonify({'error': 'Base de datos no disponible'}), 500
            
            # Guardar en Firestore
            doc_ref = db.collection('estudiantes').document(matricola)
            doc_ref.set({
                'matricola': matricola,
                'horarios': horarios,
                'timestamp': datetime.now()
            })
            
            security_logger.log_security_event(
                'schedule_saved',
                {
                    'matricola': matricola,
                    'horarios_count': len(horarios)
                },
                matricola,
                request.remote_addr
            )
            
            return jsonify({'status': 'Horario guardado correctamente'})
            
        except Exception as e:
            current_app.logger.error(f"Error guardando horario: {e}")
            security_logger.log_security_event(
                'schedule_save_error',
                {'error': str(e)},
                request.get_json().get('matricola') if request.get_json() else None,
                request.remote_addr
            )
            return jsonify({'error': 'Error guardando horario'}), 500

    @app.route('/revisar')
    def revisar_datos():
        return render_template('revisar.html')

    @app.route('/admin')
    def admin():
        if 'user_id' in session:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('admin_login'))

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            try:
                matricola = request.form.get('matricola', '').strip()
                password = request.form.get('password', '').strip()
                
                # Validar entrada
                validator = FormValidator()
                errors = validator.validate_admin_login({
                    'matricola': matricola,
                    'password': password
                })
                
                if errors:
                    security_logger.log_security_event(
                        'admin_login_validation_failed',
                        {'errors': errors},
                        matricola,
                        request.remote_addr
                    )
                    flash('Datos no válidos')
                    return render_template('admin_login.html')
                
                # Log intento de login
                security_logger.log_security_event(
                    'admin_login_attempt',
                    {'matricola': matricola},
                    matricola,
                    request.remote_addr
                )
                
                # Verificar credenciales (simulado)
                with open('credenciales.json', 'r') as f:
                    credenciales = json.load(f)
                
                stored_password = credenciales.get('admin_password')
                if matricola == 'admin' and stored_password and check_password_hash(stored_password, password):
                    session['user_id'] = matricola
                    session['user_role'] = 'Admin'
                    
                    security_logger.log_security_event(
                        'admin_login_success',
                        {'matricola': matricola},
                        matricola,
                        request.remote_addr
                    )
                    
                    flash('Login exitoso')
                    return redirect(url_for('admin_dashboard'))
                else:
                    security_logger.log_security_event(
                        'admin_login_failed',
                        {'matricola': matricola, 'reason': 'invalid_credentials'},
                        matricola,
                        request.remote_addr
                    )
                    flash('Credenciales inválidas')
                    
            except Exception as e:
                current_app.logger.error(f"Error en login de admin: {e}")
                security_logger.log_security_event(
                    'admin_login_error',
                    {'error': str(e)},
                    request.form.get('matricola'),
                    request.remote_addr
                )
                flash('Error interno del servidor')
        
        return render_template('admin_login.html')

    @app.route('/admin/dashboard')
    @login_required(role="Admin")
    def admin_dashboard():
        return render_template('admin.html', user_role=session.get('user_role'))

    @app.route('/ejecutar-matchmaking', methods=['POST'])
    @login_required(role="Admin")
    def ejecutar_matchmaking():
        try:
            resultado_str = matchmaking.realizar_matchmaking()
            return jsonify(titulo="Resultado del Matchmaking", salida=resultado_str)
        except Exception as e:
            current_app.logger.error(f"Error ejecutando matchmaking: {e}")
            return jsonify(titulo="Error inesperado", salida=str(e)), 500

    # --- RUTAS DE API PARA VALIDACIÓN ---
    @app.route('/api/validate', methods=['POST'])
    def validate_form():
        """Endpoint para validación en tiempo real"""
        try:
            data = request.get_json()
            validator = FormValidator()
            
            if data.get('type') == 'matricola':
                errors = validator.validate_matricola(data.get('value', ''))
            elif data.get('type') == 'password':
                errors = validator.validate_password(data.get('value', ''))
            elif data.get('type') == 'form':
                errors = validator.validate_student_form(data.get('data', {}))
            else:
                return jsonify({'valid': False, 'errors': ['Tipo de validación no válido']}), 400
            
            return jsonify({
                'valid': len(errors) == 0,
                'errors': errors
            })
            
        except Exception as e:
            current_app.logger.error(f"Error en validación: {e}")
            return jsonify({'valid': False, 'errors': ['Error interno']}), 500

    return app

# --- TAREAS DE CELERY ---
# Se inicializarán solo cuando se cree la aplicación
extraer_datos_task = None

def init_celery_tasks(celery_app):
    """Inicializar las tareas de Celery"""
    global extraer_datos_task
    
    @celery_app.task
    def extraer_datos_task_impl(matricola, password):
        try:
            # Verificar si se debe usar el portal real
            use_real_portal = os.getenv('USE_REAL_PORTAL', 'False').lower() == 'true'
            
            if use_real_portal:
                # Usar el conector del portal real
                from matchmaking import extraer_datos_portal_real
                resultado = extraer_datos_portal_real(matricola, password)
                
                if resultado['success']:
                    # Si la extracción del portal fue exitosa, procesar con matchmaking
                    from main import procesar_datos_extraidos
                    datos_procesados = procesar_datos_extraidos(resultado['data'], matricola)
                    return datos_procesados
                else:
                    # Si falló la extracción del portal, devolver el error
                    return {
                        'success': False,
                        'message': resultado['message'],
                        'errors': resultado.get('errors', [])
                    }
            else:
                # Usar el método original (main.py)
                from main import extraer_datos_estudiante
                resultado = extraer_datos_estudiante(matricola, password)
                return resultado
                
        except Exception as e:
            return {
                'success': False,
                'message': f"Error técnico durante extracción: {str(e)}",
                'errors': [str(e)]
            }
    
    extraer_datos_task = extraer_datos_task_impl

# --- INICIALIZACIÓN GLOBAL ---
app = None
celery_app = None

def initialize_app():
    """Inicializar la aplicación y sus servicios"""
    global app, celery_app, extraer_datos_task
    
    if app is None:
        load_dotenv()
        app = create_app()
        celery_app = make_celery(app)
        
        # Inicializar tareas de Celery
        init_celery_tasks(celery_app)

# --- PUNTO DE ENTRADA ---
if __name__ == '__main__':
    initialize_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
