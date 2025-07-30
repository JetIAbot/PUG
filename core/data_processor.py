"""
DataProcessor - Procesador de datos para PUG
Procesa y coordina el flujo de datos entre el portal, Firebase y el sistema de matchmaking
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from .firebase_manager import FirebaseManager
from .student_scheduler import StudentScheduler

logger = logging.getLogger(__name__)

class DataProcessor:
    """
    Procesador principal de datos del sistema
    Coordina el flujo entre extracción, procesamiento y almacenamiento
    """
    
    def __init__(self):
        """Inicializar el procesador de datos"""
        self.firebase = FirebaseManager()
        self.scheduler = StudentScheduler()
        self.logger = logging.getLogger('data_processor')
    
    def procesar_datos_extraidos(self, datos_portal: dict, matricola: str) -> dict:
        """
        Procesar datos extraídos del portal y ejecutar pipeline completo
        
        Args:
            datos_portal: Datos extraídos del portal universitario
            matricola: Número de matrícula del estudiante
            
        Returns:
            dict: Resultado del procesamiento con success, message y data
        """
        try:
            self.logger.info(f"Procesando datos extraídos para matrícula: {matricola[:2]}****")
            
            # Verificar conexión a Firebase
            if not self.firebase.test_connection():
                return {
                    'success': False,
                    'message': 'Error conectando a Firebase',
                    'errors': ['No se pudo conectar a la base de datos']
                }
            
            # Procesar y estructurar datos
            datos_procesados = self._estructurar_datos_estudiante(datos_portal, matricola)
            
            # Guardar en Firebase
            resultado_guardado = self.firebase.guardar_estudiante(matricola, datos_procesados)
            
            if not resultado_guardado['success']:
                return {
                    'success': False,
                    'message': f'Error guardando datos: {resultado_guardado["message"]}',
                    'errors': [resultado_guardado.get('error', 'Error desconocido')]
                }
            
            # Ejecutar matchmaking para encontrar grupos compatibles
            grupos_compatibles = self.scheduler.obtener_grupos_compatibles(matricola)
            
            self.logger.info(f"Datos procesados exitosamente para {matricola}")
            
            return {
                'success': True,
                'message': 'Datos procesados y guardados exitosamente',
                'data': {
                    'estudiante': datos_procesados,
                    'grupos_compatibles': grupos_compatibles,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error procesando datos para {matricola}: {e}")
            return {
                'success': False,
                'message': f'Error técnico durante procesamiento: {str(e)}',
                'errors': [str(e)]
            }
    
    def _estructurar_datos_estudiante(self, datos_portal: dict, matricola: str) -> dict:
        """
        Estructurar datos del portal al formato interno del sistema
        
        Args:
            datos_portal: Datos brutos del portal
            matricola: Número de matrícula
            
        Returns:
            dict: Datos estructurados en formato interno
        """
        # Estructura base
        datos_estructurados = {
            'perfil': {
                'nome': '',
                'cognome': '',
                'matricola': matricola,
                'email': '',
                'telefono': ''
            },
            'horario': [],
            'materias': [],
            'calificaciones': [],
            'estado_horarios': 'no_disponible',
            'fecha_procesamiento': datetime.now().isoformat()
        }
        
        # Procesar información del perfil
        if 'student_info' in datos_portal and datos_portal['student_info']:
            student_info = datos_portal['student_info']
            datos_estructurados['perfil'].update({
                'nome': student_info.get('nome', 'Usuario'),
                'cognome': student_info.get('cognome', 'Universitario'),
                'email': student_info.get('email', f'{matricola}@unigre.it'),
                'telefono': student_info.get('telefono', 'No disponible')
            })
        
        # Procesar horarios
        if 'schedule' in datos_portal and datos_portal['schedule']:
            datos_estructurados['horario'] = self._procesar_horarios(datos_portal['schedule'])
            datos_estructurados['estado_horarios'] = 'disponible'
            self.logger.info(f"Procesados {len(datos_estructurados['horario'])} horarios reales")
        else:
            # Usar datos demo cuando no hay horarios reales
            from .demo_generator import DemoDataGenerator
            demo_gen = DemoDataGenerator()
            datos_estructurados['horario'] = demo_gen.generar_horario_demo()
            datos_estructurados['estado_horarios'] = 'ejemplo_demo'
            self.logger.warning("Horarios no disponibles - usando datos de ejemplo")
        
        # Procesar materias
        if 'courses' in datos_portal and datos_portal['courses']:
            datos_estructurados['materias'] = self._procesar_materias(datos_portal['courses'])
        else:
            # Usar datos demo
            from .demo_generator import DemoDataGenerator
            demo_gen = DemoDataGenerator()
            datos_estructurados['materias'] = demo_gen.generar_materias_demo()
        
        # Procesar calificaciones si existen
        if 'grades' in datos_portal and datos_portal['grades']:
            datos_estructurados['calificaciones'] = self._procesar_calificaciones(datos_portal['grades'])
        
        return datos_estructurados
    
    def _procesar_horarios(self, horarios_raw: List[dict]) -> List[dict]:
        """
        Procesar horarios del portal al formato interno
        
        Args:
            horarios_raw: Lista de horarios del portal
            
        Returns:
            List[dict]: Horarios en formato interno
        """
        horarios_procesados = []
        
        for horario in horarios_raw:
            horario_procesado = {
                'materia': horario.get('subject', horario.get('materia', '')),
                'profesor': horario.get('professor', horario.get('profesor', '')),
                'dia': horario.get('day', horario.get('dia', '')),
                'bloque': horario.get('time_block', horario.get('bloque', horario.get('hora', ''))),
                'aula': horario.get('room', horario.get('aula', '')),
                'info_clase': f"{horario.get('subject', '')} - {horario.get('professor', '')}"
            }
            horarios_procesados.append(horario_procesado)
        
        return horarios_procesados
    
    def _procesar_materias(self, materias_raw: List[dict]) -> List[dict]:
        """
        Procesar materias del portal al formato interno
        
        Args:
            materias_raw: Lista de materias del portal
            
        Returns:
            List[dict]: Materias en formato interno
        """
        materias_procesadas = []
        
        for materia in materias_raw:
            materia_procesada = {
                'nombre': materia.get('name', materia.get('nombre', '')),
                'codigo': materia.get('code', materia.get('codigo', '')),
                'creditos': materia.get('credits', materia.get('creditos', '')),
                'estado': materia.get('status', materia.get('estado', '')),
                'semestre': materia.get('semester', materia.get('semestre', '')),
                'ano': materia.get('year', materia.get('ano', ''))
            }
            materias_procesadas.append(materia_procesada)
        
        return materias_procesadas
    
    def _procesar_calificaciones(self, calificaciones_raw: List[dict]) -> List[dict]:
        """
        Procesar calificaciones del portal al formato interno
        
        Args:
            calificaciones_raw: Lista de calificaciones del portal
            
        Returns:
            List[dict]: Calificaciones en formato interno
        """
        calificaciones_procesadas = []
        
        for calificacion in calificaciones_raw:
            calificacion_procesada = {
                'materia': calificacion.get('subject', calificacion.get('materia', '')),
                'nota': calificacion.get('grade', calificacion.get('nota', '')),
                'fecha': calificacion.get('date', calificacion.get('fecha', '')),
                'tipo': calificacion.get('type', calificacion.get('tipo', 'Examen'))
            }
            calificaciones_procesadas.append(calificacion_procesada)
        
        return calificaciones_procesadas
    
    def obtener_resumen_estudiante(self, matricola: str) -> Optional[dict]:
        """
        Obtener resumen completo de un estudiante
        
        Args:
            matricola: Número de matrícula
            
        Returns:
            dict: Resumen del estudiante o None si no existe
        """
        try:
            datos_estudiante = self.firebase.obtener_estudiante(matricola)
            
            if not datos_estudiante:
                return None
            
            # Calcular estadísticas
            num_clases = len(datos_estudiante.get('horario', []))
            num_materias = len(datos_estudiante.get('materias', []))
            num_calificaciones = len(datos_estudiante.get('calificaciones', []))
            
            # Obtener grupos compatibles
            grupos_compatibles = self.scheduler.obtener_grupos_compatibles(matricola)
            
            resumen = {
                'perfil': {
                    'nombre_completo': f"{datos_estudiante.get('nome', '')} {datos_estudiante.get('cognome', '')}".strip(),
                    'email': datos_estudiante.get('email', ''),
                    'matricola': matricola,
                    'ultima_actualizacion': datos_estudiante.get('ultima_actualizacion'),
                    'estado_horarios': datos_estudiante.get('estado_horarios', 'no_disponible')
                },
                'estadisticas': {
                    'total_clases': num_clases,
                    'total_materias': num_materias,
                    'total_calificaciones': num_calificaciones
                },
                'grupos_compatibles': grupos_compatibles,
                'datos_completos': datos_estudiante
            }
            
            return resumen
            
        except Exception as e:
            self.logger.error(f"Error obteniendo resumen de {matricola}: {e}")
            return None
    
    def obtener_estadisticas_sistema(self) -> dict:
        """
        Obtener estadísticas generales del sistema
        
        Returns:
            dict: Estadísticas del sistema
        """
        try:
            # Estadísticas de Firebase
            stats_firebase = self.firebase.get_statistics()
            
            # Estadísticas adicionales
            todos_estudiantes = self.firebase.obtener_todos_estudiantes()
            
            # Contar estudiantes por estado de horarios
            estados_horarios = {}
            for matricola, datos in todos_estudiantes.items():
                estado = datos.get('estado_horarios', 'no_disponible')
                estados_horarios[estado] = estados_horarios.get(estado, 0) + 1
            
            # Generar estadísticas de grupos
            grupos_compatibles = self.scheduler.obtener_grupos_compatibles()
            num_grupos_ida = grupos_compatibles.count('Para llegar el')
            num_grupos_vuelta = grupos_compatibles.count('Para salir el')
            
            estadisticas = {
                'estudiantes': stats_firebase,
                'horarios': {
                    'por_estado': estados_horarios,
                    'grupos_ida_encontrados': num_grupos_ida,
                    'grupos_vuelta_encontrados': num_grupos_vuelta
                },
                'sistema': {
                    'version': '2.0',
                    'ultima_consulta': datetime.now().isoformat()
                }
            }
            
            return estadisticas
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas del sistema: {e}")
            return {}
    
    def limpiar_datos_antiguos(self, dias: int = 30) -> dict:
        """
        Limpiar datos de estudiantes antiguos
        
        Args:
            dias: Días de antigüedad para considerar datos como antiguos
            
        Returns:
            dict: Resultado de la limpieza
        """
        try:
            from datetime import timedelta
            fecha_limite = datetime.now() - timedelta(days=dias)
            
            todos_estudiantes = self.firebase.obtener_todos_estudiantes()
            estudiantes_eliminados = 0
            
            for matricola, datos in todos_estudiantes.items():
                ultima_actualizacion = datos.get('ultima_actualizacion')
                
                if ultima_actualizacion:
                    # Verificar si es anterior a la fecha límite
                    # TODO: Implementar lógica de comparación de fechas
                    pass
            
            return {
                'success': True,
                'estudiantes_eliminados': estudiantes_eliminados,
                'fecha_limite': fecha_limite.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error limpiando datos antiguos: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Función de compatibilidad para el sistema existente
def procesar_datos_extraidos(datos_portal: dict, matricola: str) -> dict:
    """Función de compatibilidad con el sistema anterior"""
    processor = DataProcessor()
    return processor.procesar_datos_extraidos(datos_portal, matricola)
