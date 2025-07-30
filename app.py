"""
PUG - Portal University Grouper
Aplicación Flask principal para agrupación de estudiantes universitarios
Sistema de viajes compartidos basado en compatibilidad de horarios
"""

import os
import json
import logging
import time
import atexit
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from celery import Celery
from werkzeug.security import check_password_hash
from dotenv import load_dotenv

# Importar módulos internos restructurados
from core.student_scheduler import StudentScheduler
from core.data_processor import DataProcessor
from core.firebase_manager import FirebaseManager
from utils.validators import FormValidator, ValidationError
from utils.logger_config import security_logger, setup_logging
from utils.log_cleaner import setup_automatic_cleanup
from config import get_config

# Cargar configuración
load_dotenv()
config_class = get_config()

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

# Configurar limpieza automática de logs
log_cleaner = setup_automatic_cleanup()

def cleanup_on_exit():
    """Ejecutar limpieza al cerrar la aplicación"""
    if config_class.AUTO_CLEANUP:
        log_cleaner.clean_old_logs()

atexit.register(cleanup_on_exit)

def make_celery(app):
    """Configurar Celery para tareas asíncronas"""
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

def create_app(config_name='default'):
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configuración
    app.config.from_object(config_class)
    
    # Configuración específica de Celery
    app.config.update(
        CELERY_BROKER_URL=config_class.CELERY_BROKER_URL,
        CELERY_RESULT_BACKEND=config_class.CELERY_RESULT_BACKEND
    )
    
    # Inicializar Celery
    celery = make_celery(app)
    
    # Inicializar componentes del sistema
    scheduler = StudentScheduler()
    data_processor = DataProcessor()
    firebase_manager = FirebaseManager()
    
    # Decorador de autenticación
    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('admin_logged_in'):
                flash('Acceso restringido. Por favor, inicia sesión como administrador.', 'error')
                return redirect(url_for('admin_login'))
            return f(*args, **kwargs)
        return decorated_function
    
    # Decorador de validación de formularios
    def validate_form(validator_class):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    validator = validator_class(request.form)
                    if not validator.validate():
                        flash('Datos del formulario inválidos', 'error')
                        return redirect(request.referrer or url_for('index'))
                    return f(*args, **kwargs)
                except ValidationError as e:
                    flash(f'Error de validación: {str(e)}', 'error')
                    return redirect(request.referrer or url_for('index'))
            return decorated_function
        return decorator
    
    # Rutas principales
    @app.route('/')
    def index():
        """Página principal del sistema"""
        try:
            # Obtener estadísticas del sistema
            estadisticas = data_processor.obtener_estadisticas_sistema()
            
            return render_template('index.html', 
                                 estadisticas=estadisticas,
                                 demo_mode=config_class.DEMO_MODE)
        except Exception as e:
            logger.error(f"Error en página principal: {e}")
            flash('Error cargando página principal', 'error')
            return render_template('index.html', estadisticas={})
    
    @app.route('/procesar', methods=['POST'], endpoint='procesar')
    @validate_form(FormValidator)
    def procesar_estudiante():
        """Procesar datos de estudiante"""
        try:
            matricula = request.form.get('matricula', '').strip()
            password = request.form.get('password', '').strip()
            
            if not matricula or not password:
                flash('Matrícula y contraseña son requeridas', 'error')
                return redirect(url_for('index'))
            
            # Log de seguridad
            security_logger.info(f"Intento de procesamiento para matrícula: {matricula[:2]}****")
            
            # Procesar de forma asíncrona
            task = procesar_estudiante_async.delay(matricula, password)
            
            # Guardar ID de tarea en sesión
            session['current_task_id'] = task.id
            session['matricula_actual'] = matricula
            
            flash(f'Procesando datos para matrícula {matricula[:2]}****...', 'info')
            return redirect(url_for('revisar'))
            
        except Exception as e:
            logger.error(f"Error procesando estudiante: {e}")
            flash('Error durante el procesamiento', 'error')
            return redirect(url_for('index'))
    
    @app.route('/revisar')
    def revisar():
        """Página de revisión de resultados"""
        try:
            task_id = session.get('current_task_id')
            matricula = session.get('matricula_actual')
            
            if not task_id or not matricula:
                flash('No hay datos para revisar', 'warning')
                return redirect(url_for('index'))
            
            # Verificar estado de la tarea
            task = procesar_estudiante_async.AsyncResult(task_id)
            
            if task.state == 'PENDING':
                return render_template('revisar.html', 
                                     estado='procesando',
                                     matricula=matricula[:2] + '****')
            elif task.state == 'SUCCESS':
                resultado = task.result
                return render_template('revisar.html',
                                     estado='completado',
                                     matricula=matricula[:2] + '****',
                                     resultado=resultado)
            else:
                return render_template('revisar.html',
                                     estado='error',
                                     matricula=matricula[:2] + '****',
                                     error=str(task.info))
                
        except Exception as e:
            logger.error(f"Error en página de revisión: {e}")
            flash('Error cargando resultados', 'error')
            return redirect(url_for('index'))
    
    @app.route('/api/status/<task_id>')
    def check_task_status(task_id):
        """API para verificar estado de tarea"""
        try:
            task = procesar_estudiante_async.AsyncResult(task_id)
            
            if task.state == 'PENDING':
                response = {
                    'state': task.state,
                    'current': 0,
                    'total': 1,
                    'status': 'Procesando...'
                }
            elif task.state != 'FAILURE':
                response = {
                    'state': task.state,
                    'current': 1,
                    'total': 1,
                    'status': 'Completado',
                    'result': task.info
                }
            else:
                response = {
                    'state': task.state,
                    'current': 1,
                    'total': 1,
                    'status': str(task.info)
                }
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Error verificando estado de tarea: {e}")
            return jsonify({'state': 'ERROR', 'status': 'Error del sistema'})
    
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        """Login de administrador"""
        if request.method == 'POST':
            try:
                username = request.form.get('username', '').strip()
                password = request.form.get('password', '').strip()
                
                if not username or not password:
                    flash('Usuario y contraseña requeridos', 'error')
                    return render_template('admin_login.html')
                
                # Verificar credenciales (implementar verificación real)
                if verificar_credenciales_admin(username, password):
                    session['admin_logged_in'] = True
                    session['admin_username'] = username
                    security_logger.info(f"Login admin exitoso: {username}")
                    flash('Login exitoso', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    security_logger.warning(f"Login admin fallido: {username}")
                    flash('Credenciales incorrectas', 'error')
                    
            except Exception as e:
                logger.error(f"Error en login admin: {e}")
                flash('Error durante login', 'error')
        
        return render_template('admin_login.html')
    
    @app.route('/admin')
    @admin_required
    def admin_dashboard():
        """Dashboard de administrador"""
        try:
            # Obtener estadísticas completas
            estadisticas = data_processor.obtener_estadisticas_sistema()
            
            # Obtener lista de estudiantes recientes
            todos_estudiantes = firebase_manager.obtener_todos_estudiantes()
            estudiantes_recientes = list(todos_estudiantes.items())[:10]  # Últimos 10
            
            return render_template('admin.html',
                                 estadisticas=estadisticas,
                                 estudiantes_recientes=estudiantes_recientes)
                                 
        except Exception as e:
            logger.error(f"Error en dashboard admin: {e}")
            flash('Error cargando dashboard', 'error')
            return render_template('admin.html', estadisticas={})
    
    @app.route('/admin/logout')
    @admin_required
    def admin_logout():
        """Logout de administrador"""
        username = session.get('admin_username', 'unknown')
        session.clear()
        security_logger.info(f"Logout admin: {username}")
        flash('Sesión cerrada exitosamente', 'info')
        return redirect(url_for('index'))
    
    @app.route('/api/grupos')
    def api_grupos_compatibles():
        """API para obtener grupos compatibles"""
        try:
            matricula = request.args.get('matricula')
            grupos = scheduler.obtener_grupos_compatibles(matricula)
            
            return jsonify({
                'success': True,
                'grupos': grupos,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo grupos: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            })
    
    # Tareas asíncronas de Celery
    @celery.task(bind=True)
    def procesar_estudiante_async(self, matricula, password):
        """Tarea asíncrona para procesar estudiante"""
        try:
            self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': 'Iniciando...'})
            
            # Extraer y guardar datos
            self.update_state(state='PROGRESS', meta={'current': 25, 'total': 100, 'status': 'Extrayendo datos...'})
            resultado = scheduler.extraer_y_guardar_datos(matricula, password)
            
            if not resultado['success']:
                raise Exception(resultado['message'])
            
            # Procesar datos
            self.update_state(state='PROGRESS', meta={'current': 75, 'total': 100, 'status': 'Procesando datos...'})
            resultado_procesado = data_processor.procesar_datos_extraidos(resultado['data'], matricula)
            
            self.update_state(state='PROGRESS', meta={'current': 100, 'total': 100, 'status': 'Completado'})
            
            return {
                'success': True,
                'message': 'Datos procesados exitosamente',
                'data': resultado_procesado
            }
            
        except Exception as e:
            logger.error(f"Error en tarea asíncrona: {e}")
            raise self.retry(countdown=60, max_retries=3)
    
    def verificar_credenciales_admin(username, password):
        """Verificar credenciales de administrador"""
        try:
            # TODO: Implementar verificación real con Firebase
            # Por ahora, credenciales de desarrollo
            if username == "admin" and password == "admin123":
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error verificando credenciales: {e}")
            return False
    
    # Manejadores de errores
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('index.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Error interno del servidor: {error}")
        return render_template('index.html'), 500
    
    return app

# Crear aplicación
app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Iniciando PUG en puerto {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
