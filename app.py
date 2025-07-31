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
from core.car_manager import CarManager
from core.student_manager import StudentManager
from core.viaje_manager import ViajeManager
from core.models import TipoCarro, TipoCombustible, EstadoCarro, TipoLicencia
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
    car_manager = CarManager()
    
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
                    logger.info(f"Login admin exitoso: {username}")
                    flash('Login exitoso', 'success')
                    return redirect(url_for('admin_dashboard'))
                else:
                    logger.warning(f"Login admin fallido: {username}")
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
    def admin_logout():
        """Logout de administrador"""
        username = session.get('admin_username', 'unknown')
        session.clear()
        logger.info(f"Logout admin: {username}")
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
    
    # =================== RUTAS DE GESTIÓN DE CARROS ===================
    
    @app.route('/admin/carros')
    @admin_required
    def admin_carros():
        """Panel de gestión de carros"""
        try:
            # Obtener filtros de la URL
            filtro_estado = request.args.get('estado')
            filtro_tipo = request.args.get('tipo')
            
            # Construir filtros
            filtros = {}
            if filtro_estado:
                filtros['estado'] = filtro_estado
            if filtro_tipo:
                filtros['tipo_carro'] = filtro_tipo
            
            # Obtener carros
            carros = car_manager.obtener_todos_carros(filtros)
            estadisticas = car_manager.obtener_estadisticas()
            
            return render_template('admin/carros.html',
                                 carros=carros,
                                 estadisticas=estadisticas,
                                 tipos_carro=TipoCarro,
                                 tipos_combustible=TipoCombustible,
                                 estados_carro=EstadoCarro,
                                 filtros=filtros)
                                 
        except Exception as e:
            logger.error(f"Error en panel de carros: {e}")
            flash('Error cargando panel de carros', 'error')
            return redirect(url_for('admin_dashboard'))
    
    @app.route('/admin/carros/nuevo', methods=['GET', 'POST'])
    @admin_required
    def admin_carros_nuevo():
        """Crear nuevo carro"""
        if request.method == 'POST':
            try:
                datos_carro = {
                    'marca': request.form.get('marca', '').strip(),
                    'modelo': request.form.get('modelo', '').strip(),
                    'año': request.form.get('año', '').strip(),
                    'placa': request.form.get('placa', '').strip(),
                    'tipo_carro': request.form.get('tipo_carro'),
                    'tipo_combustible': request.form.get('tipo_combustible'),
                    'capacidad_pasajeros': request.form.get('capacidad_pasajeros', '').strip(),
                    'observaciones': request.form.get('observaciones', '').strip()
                }
                
                resultado = car_manager.crear_carro(datos_carro)
                
                if resultado['success']:
                    flash(f'Carro creado exitosamente: {datos_carro["marca"]} {datos_carro["modelo"]}', 'success')
                    return redirect(url_for('admin_carros'))
                else:
                    flash(f'Error creando carro: {resultado["message"]}', 'error')
                    
            except Exception as e:
                logger.error(f"Error creando carro: {e}")
                flash('Error técnico creando carro', 'error')
        
        return render_template('admin/carros_form.html',
                             tipos_carro=TipoCarro,
                             tipos_combustible=TipoCombustible,
                             accion='crear')
    
    @app.route('/admin/carros/<id_carro>/editar', methods=['GET', 'POST'])
    @admin_required
    def admin_carros_editar(id_carro):
        """Editar carro existente"""
        carro = car_manager.obtener_carro(id_carro)
        if not carro:
            flash('Carro no encontrado', 'error')
            return redirect(url_for('admin_carros'))
        
        if request.method == 'POST':
            try:
                datos_actualizacion = {
                    'marca': request.form.get('marca', '').strip(),
                    'modelo': request.form.get('modelo', '').strip(),
                    'año': request.form.get('año', '').strip(),
                    'placa': request.form.get('placa', '').strip(),
                    'tipo_carro': request.form.get('tipo_carro'),
                    'tipo_combustible': request.form.get('tipo_combustible'),
                    'capacidad_pasajeros': request.form.get('capacidad_pasajeros', '').strip(),
                    'estado': request.form.get('estado'),
                    'observaciones': request.form.get('observaciones', '').strip()
                }
                
                resultado = car_manager.actualizar_carro(id_carro, datos_actualizacion)
                
                if resultado['success']:
                    flash(f'Carro actualizado exitosamente', 'success')
                    return redirect(url_for('admin_carros'))
                else:
                    flash(f'Error actualizando carro: {resultado["message"]}', 'error')
                    
            except Exception as e:
                logger.error(f"Error actualizando carro: {e}")
                flash('Error técnico actualizando carro', 'error')
        
        return render_template('admin/carros_form.html',
                             carro=carro,
                             tipos_carro=TipoCarro,
                             tipos_combustible=TipoCombustible,
                             estados_carro=EstadoCarro,
                             accion='editar')
    
    @app.route('/admin/carros/<id_carro>/eliminar', methods=['POST'])
    @admin_required
    def admin_carros_eliminar(id_carro):
        """Eliminar carro"""
        try:
            resultado = car_manager.eliminar_carro(id_carro)
            
            if resultado['success']:
                flash('Carro eliminado exitosamente', 'success')
            else:
                flash(f'Error eliminando carro: {resultado["message"]}', 'error')
                
        except Exception as e:
            logger.error(f"Error eliminando carro: {e}")
            flash('Error técnico eliminando carro', 'error')
        
        return redirect(url_for('admin_carros'))
    
    @app.route('/admin/carros/<id_carro>/estado', methods=['POST'])
    @admin_required
    def admin_carros_cambiar_estado(id_carro):
        """Cambiar estado de un carro"""
        try:
            nuevo_estado = request.form.get('estado')
            if not nuevo_estado:
                flash('Estado requerido', 'error')
                return redirect(url_for('admin_carros'))
            
            resultado = car_manager.cambiar_estado_carro(id_carro, EstadoCarro(nuevo_estado))
            
            if resultado['success']:
                flash('Estado actualizado exitosamente', 'success')
            else:
                flash(f'Error cambiando estado: {resultado["message"]}', 'error')
                
        except Exception as e:
            logger.error(f"Error cambiando estado: {e}")
            flash('Error técnico cambiando estado', 'error')
        
        return redirect(url_for('admin_carros'))
    
    @app.route('/api/carros/disponibles')
    @admin_required
    def api_carros_disponibles():
        """API para obtener carros disponibles"""
        try:
            licencias = request.args.getlist('licencias')
            licencias_obj = [TipoLicencia(l) for l in licencias if l] if licencias else None
            
            carros = car_manager.obtener_carros_disponibles(licencias_obj)
            
            return jsonify({
                'success': True,
                'carros': [carro.to_dict() for carro in carros]
            })
            
        except Exception as e:
            logger.error(f"Error obteniendo carros disponibles: {e}")
            return jsonify({'success': False, 'message': str(e)})
    
    # =================== FIN RUTAS DE GESTIÓN DE CARROS ===================
    
    # Manejadores de errores
    
    # ============================================================================
    # RUTAS PARA GESTIÓN DE ESTUDIANTES
    # ============================================================================
    
    @app.route('/admin/estudiantes')
    @admin_required
    def admin_estudiantes():
        """Listar todos los estudiantes"""
        try:
            student_manager = StudentManager()
            estudiantes = student_manager.listar_estudiantes()
            estadisticas = student_manager.obtener_estadisticas()
            
            return render_template('admin/estudiantes.html', 
                                 estudiantes=estudiantes,
                                 estadisticas=estadisticas)
        except Exception as e:
            logger.error(f"Error en admin_estudiantes: {e}")
            flash(f'Error al cargar estudiantes: {str(e)}', 'error')
            return redirect(url_for('admin_panel'))
    
    @app.route('/admin/estudiantes/nuevo')
    @admin_required
    def admin_estudiantes_nuevo():
        """Formulario para crear nuevo estudiante"""
        tipos_licencia = [{'value': t.value, 'name': t.value} for t in TipoLicencia]
        return render_template('admin/estudiantes_form.html', 
                             tipos_licencia=tipos_licencia,
                             modo='crear')
    
    @app.route('/admin/estudiantes/crear', methods=['POST'])
    @admin_required
    def admin_estudiantes_crear():
        """Crear nuevo estudiante"""
        try:
            student_manager = StudentManager()
            
            # Obtener datos del formulario
            estudiante_data = {
                'matricola': request.form.get('matricola'),
                'nombre': request.form.get('nombre'),
                'apellido': request.form.get('apellido'),
                'email': request.form.get('email'),
                'telefono': request.form.get('telefono', ''),
                'tiene_licencia': request.form.get('tiene_licencia') == 'on',
                'tipos_licencia': request.form.getlist('tipos_licencia'),
                'fecha_vencimiento_licencia': request.form.get('fecha_vencimiento_licencia'),
                'viaja_hoy': request.form.get('viaja_hoy') == 'on'
            }
            
            resultado = student_manager.crear_estudiante(estudiante_data)
            
            if resultado['success']:
                flash(resultado['message'], 'success')
                return redirect(url_for('admin_estudiantes'))
            else:
                flash(f"Error: {resultado['message']}", 'error')
                for error in resultado.get('errors', []):
                    flash(error, 'error')
                return redirect(url_for('admin_estudiantes_nuevo'))
                
        except Exception as e:
            logger.error(f"Error creando estudiante: {e}")
            flash(f'Error técnico: {str(e)}', 'error')
            return redirect(url_for('admin_estudiantes_nuevo'))
    
    @app.route('/admin/estudiantes/<matricola>')
    @admin_required
    def admin_estudiante_detalle(matricola):
        """Ver detalles de un estudiante específico"""
        try:
            student_manager = StudentManager()
            estudiante = student_manager.obtener_estudiante(matricola)
            
            if not estudiante:
                flash('Estudiante no encontrado', 'error')
                return redirect(url_for('admin_estudiantes'))
            
            return render_template('admin/estudiante_detalle.html', 
                                 estudiante=estudiante)
        except Exception as e:
            logger.error(f"Error obteniendo estudiante {matricola}: {e}")
            flash(f'Error al cargar estudiante: {str(e)}', 'error')
            return redirect(url_for('admin_estudiantes'))
    
    @app.route('/admin/estudiantes/<matricola>/editar')
    @admin_required
    def admin_estudiante_editar(matricola):
        """Formulario para editar estudiante"""
        try:
            student_manager = StudentManager()
            estudiante = student_manager.obtener_estudiante(matricola)
            
            if not estudiante:
                flash('Estudiante no encontrado', 'error')
                return redirect(url_for('admin_estudiantes'))
            
            tipos_licencia = [{'value': t.value, 'name': t.value} for t in TipoLicencia]
            return render_template('admin/estudiantes_form.html', 
                                 estudiante=estudiante,
                                 tipos_licencia=tipos_licencia,
                                 modo='editar')
        except Exception as e:
            logger.error(f"Error cargando formulario edición {matricola}: {e}")
            flash(f'Error al cargar formulario: {str(e)}', 'error')
            return redirect(url_for('admin_estudiantes'))
    
    @app.route('/admin/estudiantes/<matricola>/actualizar', methods=['POST'])
    @admin_required
    def admin_estudiante_actualizar(matricola):
        """Actualizar estudiante existente"""
        try:
            student_manager = StudentManager()
            
            # Obtener datos del formulario
            datos_actualizacion = {
                'nombre': request.form.get('nombre'),
                'apellido': request.form.get('apellido'),
                'email': request.form.get('email'),
                'telefono': request.form.get('telefono', ''),
                'tiene_licencia': request.form.get('tiene_licencia') == 'on',
                'tipos_licencia': request.form.getlist('tipos_licencia'),
                'fecha_vencimiento_licencia': request.form.get('fecha_vencimiento_licencia'),
                'viaja_hoy': request.form.get('viaja_hoy') == 'on'
            }
            
            resultado = student_manager.actualizar_estudiante(matricola, datos_actualizacion)
            
            if resultado['success']:
                flash(resultado['message'], 'success')
                return redirect(url_for('admin_estudiante_detalle', matricola=matricola))
            else:
                flash(f"Error: {resultado['message']}", 'error')
                for error in resultado.get('errors', []):
                    flash(error, 'error')
                return redirect(url_for('admin_estudiante_editar', matricola=matricola))
                
        except Exception as e:
            logger.error(f"Error actualizando estudiante {matricola}: {e}")
            flash(f'Error técnico: {str(e)}', 'error')
            return redirect(url_for('admin_estudiante_editar', matricola=matricola))
    
    @app.route('/admin/estudiantes/<matricola>/eliminar', methods=['POST'])
    @admin_required
    def admin_estudiante_eliminar(matricola):
        """Eliminar estudiante"""
        try:
            student_manager = StudentManager()
            resultado = student_manager.eliminar_estudiante(matricola)
            
            if resultado['success']:
                flash(resultado['message'], 'success')
            else:
                flash(f"Error: {resultado['message']}", 'error')
                
            return redirect(url_for('admin_estudiantes'))
                
        except Exception as e:
            logger.error(f"Error eliminando estudiante {matricola}: {e}")
            flash(f'Error técnico: {str(e)}', 'error')
            return redirect(url_for('admin_estudiantes'))
    
    # ============================================================================
    # RUTAS PARA GESTIÓN DE VIAJES
    # ============================================================================
    
    @app.route('/admin/viajes')
    @admin_required
    def admin_viajes():
        """Listar todos los viajes"""
        try:
            viaje_manager = ViajeManager()
            fecha_filtro = request.args.get('fecha')
            estado_filtro = request.args.get('estado')
            
            viajes = viaje_manager.listar_viajes(fecha=fecha_filtro, estado=estado_filtro)
            
            return render_template('admin/viajes.html', 
                                 viajes=viajes,
                                 fecha_filtro=fecha_filtro,
                                 estado_filtro=estado_filtro)
        except Exception as e:
            logger.error(f"Error en admin_viajes: {e}")
            flash(f'Error al cargar viajes: {str(e)}', 'error')
            return redirect(url_for('admin_panel'))
    
    @app.route('/admin/viajes/nuevo')
    @admin_required
    def admin_viaje_nuevo():
        """Formulario para crear nuevo viaje"""
        try:
            car_manager = CarManager()
            student_manager = StudentManager()
            
            carros_disponibles = car_manager.listar_carros({'estado': 'disponible'})
            conductores = student_manager.buscar_conductores_disponibles()
            
            return render_template('admin/viaje_form.html', 
                                 carros=carros_disponibles,
                                 conductores=conductores,
                                 modo='crear')
        except Exception as e:
            logger.error(f"Error cargando formulario viaje: {e}")
            flash(f'Error al cargar formulario: {str(e)}', 'error')
            return redirect(url_for('admin_viajes'))
    
    @app.route('/admin/viajes/crear', methods=['POST'])
    @admin_required
    def admin_viaje_crear():
        """Crear nuevo viaje"""
        try:
            viaje_manager = ViajeManager()
            
            # Obtener datos del formulario
            viaje_data = {
                'fecha': request.form.get('fecha'),
                'hora_salida': request.form.get('hora_salida'),
                'origen': request.form.get('origen'),
                'destino': request.form.get('destino'),
                'id_carro': request.form.get('id_carro'),
                'matricola_conductor': request.form.get('matricola_conductor'),
                'observaciones': request.form.get('observaciones', '')
            }
            
            resultado = viaje_manager.crear_viaje(viaje_data)
            
            if resultado['success']:
                flash(resultado['message'], 'success')
                return redirect(url_for('admin_viajes'))
            else:
                flash(f"Error: {resultado['message']}", 'error')
                for error in resultado.get('errors', []):
                    flash(error, 'error')
                return redirect(url_for('admin_viaje_nuevo'))
                
        except Exception as e:
            logger.error(f"Error creando viaje: {e}")
            flash(f'Error técnico: {str(e)}', 'error')
            return redirect(url_for('admin_viaje_nuevo'))
    
    @app.route('/admin/viajes/<id_viaje>')
    @admin_required
    def admin_viaje_detalle(id_viaje):
        """Ver detalles de un viaje específico"""
        try:
            viaje_manager = ViajeManager()
            viaje = viaje_manager.obtener_viaje(id_viaje)
            
            if not viaje:
                flash('Viaje no encontrado', 'error')
                return redirect(url_for('admin_viajes'))
            
            # Obtener detalles adicionales
            car_manager = CarManager()
            student_manager = StudentManager()
            
            carro = car_manager.obtener_carro(viaje['id_carro'])
            conductor = student_manager.obtener_estudiante(viaje['matricola_conductor'])
            
            pasajeros_info = []
            for matricola in viaje.get('pasajeros', []):
                pasajero = student_manager.obtener_estudiante(matricola)
                if pasajero:
                    pasajeros_info.append(pasajero)
            
            return render_template('admin/viaje_detalle.html', 
                                 viaje=viaje,
                                 carro=carro,
                                 conductor=conductor,
                                 pasajeros=pasajeros_info)
        except Exception as e:
            logger.error(f"Error obteniendo viaje {id_viaje}: {e}")
            flash(f'Error al cargar viaje: {str(e)}', 'error')
            return redirect(url_for('admin_viajes'))
    
    @app.route('/admin/listas-diarias')
    @admin_required
    def admin_listas_diarias():
        """Gestión de listas diarias de viajes"""
        try:
            viaje_manager = ViajeManager()
            fecha_hoy = datetime.now().strftime('%Y-%m-%d')
            
            # Obtener lista de hoy si existe
            lista_hoy = viaje_manager.obtener_lista_diaria(fecha_hoy)
            
            return render_template('admin/listas_diarias.html', 
                                 lista_hoy=lista_hoy,
                                 fecha_hoy=fecha_hoy)
        except Exception as e:
            logger.error(f"Error en listas diarias: {e}")
            flash(f'Error al cargar listas: {str(e)}', 'error')
            return redirect(url_for('admin_panel'))
    
    @app.route('/admin/asignacion-automatica', methods=['POST'])
    @admin_required
    def admin_asignacion_automatica():
        """Generar asignación automática de estudiantes a carros"""
        try:
            viaje_manager = ViajeManager()
            fecha = request.form.get('fecha', datetime.now().strftime('%Y-%m-%d'))
            
            resultado = viaje_manager.generar_asignacion_automatica(fecha)
            
            if resultado['success']:
                flash(f"Asignación automática completada: {resultado['message']}", 'success')
                
                # Crear los viajes en la base de datos
                viajes_creados = 0
                for viaje_data in resultado['data']['viajes_generados']:
                    resultado_creacion = viaje_manager.crear_viaje(viaje_data)
                    if resultado_creacion['success']:
                        viajes_creados += 1
                
                flash(f"Se crearon {viajes_creados} viajes exitosamente", 'info')
            else:
                flash(f"Error en asignación automática: {resultado['message']}", 'error')
                for error in resultado.get('errors', []):
                    flash(error, 'error')
            
            return redirect(url_for('admin_listas_diarias'))
                
        except Exception as e:
            logger.error(f"Error en asignación automática: {e}")
            flash(f'Error técnico: {str(e)}', 'error')
            return redirect(url_for('admin_listas_diarias'))

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
