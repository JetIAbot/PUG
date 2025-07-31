"""
ViajeManager - Gestor de viajes para PUG Sistema de Carpooling
CRUD completo para gestión de viajes y listas diarias
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from firebase_admin import firestore

from .models import Viaje, ListaViajes, Carro, Estudiante, EstadoViaje, EstadoLista, TipoLicencia
from .firebase_manager import FirebaseManager
from .car_manager import CarManager
from .student_manager import StudentManager

logger = logging.getLogger(__name__)

class ViajeManager:
    """Gestor principal para operaciones de viajes y listas diarias"""
    
    def __init__(self):
        self.firebase = FirebaseManager()
        self.db = self.firebase.get_client()
        self.car_manager = CarManager()
        self.student_manager = StudentManager()
        self.collection_viajes = 'viajes'
        self.collection_listas = 'listas_diarias'
        
        if not self.db:
            raise Exception("No se pudo conectar a Firebase")
    
    def crear_viaje(self, viaje_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear un nuevo viaje
        
        Args:
            viaje_data: Datos del viaje a crear
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validar datos requeridos
            validacion = self._validar_datos_viaje(viaje_data)
            if not validacion['valid']:
                return {
                    'success': False,
                    'message': 'Datos inválidos',
                    'errors': validacion['errors']
                }
            
            # Verificar disponibilidad del carro
            carro_data = self.car_manager.obtener_carro(viaje_data['id_carro'])
            if not carro_data:
                return {
                    'success': False,
                    'message': 'Carro no encontrado',
                    'errors': ['ID de carro inválido']
                }
            
            if carro_data.get('estado') != 'disponible':
                return {
                    'success': False,
                    'message': 'Carro no disponible',
                    'errors': ['El carro no está disponible para viajes']
                }
            
            # Verificar que el conductor existe y puede conducir el carro
            conductor_data = self.student_manager.obtener_estudiante(viaje_data['matricola_conductor'])
            if not conductor_data:
                return {
                    'success': False,
                    'message': 'Conductor no encontrado',
                    'errors': ['Matrícula de conductor inválida']
                }
            
            # Verificar licencia del conductor
            if not self._puede_conducir_carro(conductor_data, carro_data):
                return {
                    'success': False,
                    'message': 'Conductor no puede manejar este tipo de carro',
                    'errors': ['Licencia incompatible con el tipo de vehículo']
                }
            
            # Generar ID único para el viaje
            id_viaje = self._generar_id_viaje(viaje_data['fecha'], viaje_data['hora_salida'])
            
            # Crear objeto viaje
            viaje_dict = {
                'id_viaje': id_viaje,
                'fecha': viaje_data['fecha'],
                'hora_salida': viaje_data['hora_salida'],
                'origen': viaje_data['origen'],
                'destino': viaje_data['destino'],
                'id_carro': viaje_data['id_carro'],
                'matricola_conductor': viaje_data['matricola_conductor'],
                'pasajeros': viaje_data.get('pasajeros', []),
                'estado': viaje_data.get('estado', 'planificado'),
                'observaciones': viaje_data.get('observaciones', ''),
                'fecha_creacion': datetime.now().isoformat(),
                'capacidad_maxima': carro_data['capacidad_pasajeros'],
                'ocupacion_actual': 1 + len(viaje_data.get('pasajeros', []))  # conductor + pasajeros
            }
            
            # Guardar en Firebase
            doc_ref = self.db.collection(self.collection_viajes).document(id_viaje)
            doc_ref.set(viaje_dict)
            
            logger.info(f"Viaje creado exitosamente: {id_viaje}")
            
            return {
                'success': True,
                'message': 'Viaje creado exitosamente',
                'data': viaje_dict,
                'id': id_viaje
            }
            
        except Exception as e:
            logger.error(f"Error creando viaje: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'errors': [str(e)]
            }
    
    def agregar_pasajero(self, id_viaje: str, matricola_pasajero: str) -> Dict[str, Any]:
        """
        Agregar un pasajero a un viaje existente
        
        Args:
            id_viaje: ID del viaje
            matricola_pasajero: Matrícula del pasajero
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Obtener viaje actual
            viaje_data = self.obtener_viaje(id_viaje)
            if not viaje_data:
                return {
                    'success': False,
                    'message': 'Viaje no encontrado',
                    'errors': ['ID de viaje inválido']
                }
            
            # Verificar que el estudiante existe
            estudiante_data = self.student_manager.obtener_estudiante(matricola_pasajero)
            if not estudiante_data:
                return {
                    'success': False,
                    'message': 'Estudiante no encontrado',
                    'errors': ['Matrícula inválida']
                }
            
            # Verificar que no sea el conductor
            if matricola_pasajero == viaje_data['matricola_conductor']:
                return {
                    'success': False,
                    'message': 'El conductor no puede ser pasajero',
                    'errors': ['Conflicto conductor-pasajero']
                }
            
            # Verificar que no esté ya en la lista
            pasajeros_actuales = viaje_data.get('pasajeros', [])
            if matricola_pasajero in pasajeros_actuales:
                return {
                    'success': False,
                    'message': 'El estudiante ya está en este viaje',
                    'errors': ['Pasajero duplicado']
                }
            
            # Verificar capacidad
            ocupacion_actual = viaje_data.get('ocupacion_actual', 1)
            capacidad_maxima = viaje_data.get('capacidad_maxima', 5)
            
            if ocupacion_actual >= capacidad_maxima:
                return {
                    'success': False,
                    'message': 'Viaje lleno',
                    'errors': ['No hay plazas disponibles']
                }
            
            # Agregar pasajero
            pasajeros_actuales.append(matricola_pasajero)
            datos_actualizacion = {
                'pasajeros': pasajeros_actuales,
                'ocupacion_actual': ocupacion_actual + 1,
                'fecha_actualizacion': datetime.now().isoformat()
            }
            
            # Actualizar en Firebase
            doc_ref = self.db.collection(self.collection_viajes).document(id_viaje)
            doc_ref.update(datos_actualizacion)
            
            logger.info(f"Pasajero {matricola_pasajero} agregado al viaje {id_viaje}")
            
            return {
                'success': True,
                'message': 'Pasajero agregado exitosamente',
                'data': datos_actualizacion
            }
            
        except Exception as e:
            logger.error(f"Error agregando pasajero: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'errors': [str(e)]
            }
    
    def obtener_viaje(self, id_viaje: str) -> Optional[Dict[str, Any]]:
        """
        Obtener un viaje por ID
        
        Args:
            id_viaje: ID del viaje
            
        Returns:
            dict: Datos del viaje o None si no existe
        """
        try:
            doc_ref = self.db.collection(self.collection_viajes).document(id_viaje)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                logger.info(f"Viaje encontrado: {id_viaje}")
                return data
            else:
                logger.warning(f"Viaje no encontrado: {id_viaje}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo viaje {id_viaje}: {e}")
            return None
    
    def listar_viajes(self, fecha: Optional[str] = None, estado: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Listar viajes con filtros opcionales
        
        Args:
            fecha: Fecha específica (YYYY-MM-DD)
            estado: Estado del viaje
            
        Returns:
            list: Lista de viajes
        """
        try:
            query = self.db.collection(self.collection_viajes)
            
            # Aplicar filtros
            if fecha:
                query = query.where('fecha', '==', fecha)
            
            if estado:
                query = query.where('estado', '==', estado)
            
            # Ordenar por fecha y hora
            query = query.order_by('fecha').order_by('hora_salida')
            
            # Ejecutar consulta
            docs = query.stream()
            viajes = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id_viaje'] = doc.id
                viajes.append(data)
            
            logger.info(f"Encontrados {len(viajes)} viajes")
            return viajes
            
        except Exception as e:
            logger.error(f"Error listando viajes: {e}")
            return []
    
    def crear_lista_diaria(self, fecha: str, viajes_ida: List[str] = None, viajes_vuelta: List[str] = None) -> Dict[str, Any]:
        """
        Crear una lista diaria de viajes
        
        Args:
            fecha: Fecha de la lista (YYYY-MM-DD)
            viajes_ida: IDs de viajes de ida
            viajes_vuelta: IDs de viajes de vuelta
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Generar ID para la lista
            id_lista = f"lista_{fecha.replace('-', '')}"
            
            # Verificar que no exista ya una lista para esa fecha
            lista_existente = self.obtener_lista_diaria(fecha)
            if lista_existente:
                return {
                    'success': False,
                    'message': 'Ya existe una lista para esta fecha',
                    'errors': ['Lista duplicada']
                }
            
            # Validar que los viajes existen
            viajes_ida = viajes_ida or []
            viajes_vuelta = viajes_vuelta or []
            
            for vid in viajes_ida + viajes_vuelta:
                if not self.obtener_viaje(vid):
                    return {
                        'success': False,
                        'message': f'Viaje {vid} no encontrado',
                        'errors': ['Viaje inválido']
                    }
            
            # Crear objeto lista
            lista_dict = {
                'id_lista': id_lista,
                'fecha': fecha,
                'viajes_ida': viajes_ida,
                'viajes_vuelta': viajes_vuelta,
                'estado': 'borrador',
                'creado_por': 'admin',  # TODO: obtener del contexto de sesión
                'observaciones': '',
                'fecha_creacion': datetime.now().isoformat(),
                'fecha_actualizacion': datetime.now().isoformat(),
                'total_estudiantes_ida': self._calcular_total_estudiantes(viajes_ida),
                'total_estudiantes_vuelta': self._calcular_total_estudiantes(viajes_vuelta),
                'total_carros_usados': len(set(viajes_ida + viajes_vuelta))
            }
            
            # Guardar en Firebase
            doc_ref = self.db.collection(self.collection_listas).document(id_lista)
            doc_ref.set(lista_dict)
            
            logger.info(f"Lista diaria creada: {id_lista}")
            
            return {
                'success': True,
                'message': 'Lista diaria creada exitosamente',
                'data': lista_dict,
                'id': id_lista
            }
            
        except Exception as e:
            logger.error(f"Error creando lista diaria: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'errors': [str(e)]
            }
    
    def obtener_lista_diaria(self, fecha: str) -> Optional[Dict[str, Any]]:
        """
        Obtener lista diaria por fecha
        
        Args:
            fecha: Fecha (YYYY-MM-DD)
            
        Returns:
            dict: Datos de la lista o None si no existe
        """
        try:
            id_lista = f"lista_{fecha.replace('-', '')}"
            doc_ref = self.db.collection(self.collection_listas).document(id_lista)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                logger.info(f"Lista diaria encontrada: {fecha}")
                return data
            else:
                logger.warning(f"Lista diaria no encontrada: {fecha}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo lista diaria {fecha}: {e}")
            return None
    
    def generar_asignacion_automatica(self, fecha: str) -> Dict[str, Any]:
        """
        Generar asignación automática de estudiantes a carros para una fecha
        
        Args:
            fecha: Fecha para la asignación (YYYY-MM-DD)
            
        Returns:
            dict: Resultado con viajes generados
        """
        try:
            # Obtener estudiantes que viajan hoy
            estudiantes_viajan = self.student_manager.listar_estudiantes({'viaja_hoy': True})
            
            if not estudiantes_viajan:
                return {
                    'success': False,
                    'message': 'No hay estudiantes que viajen hoy',
                    'errors': ['Sin estudiantes']
                }
            
            # Obtener carros disponibles
            carros_disponibles = self.car_manager.listar_carros({'estado': 'disponible'})
            
            if not carros_disponibles:
                return {
                    'success': False,
                    'message': 'No hay carros disponibles',
                    'errors': ['Sin carros']
                }
            
            # Identificar conductores potenciales
            conductores = [e for e in estudiantes_viajan if e.get('tiene_licencia', False)]
            
            if not conductores:
                return {
                    'success': False,
                    'message': 'No hay conductores disponibles',
                    'errors': ['Sin conductores']
                }
            
            # Algoritmo de asignación
            viajes_generados = self._algoritmo_asignacion(conductores, estudiantes_viajan, carros_disponibles, fecha)
            
            logger.info(f"Asignación automática completada: {len(viajes_generados)} viajes generados")
            
            return {
                'success': True,
                'message': f'Asignación completada: {len(viajes_generados)} viajes generados',
                'data': {
                    'viajes_generados': viajes_generados,
                    'total_viajes': len(viajes_generados),
                    'total_estudiantes_asignados': sum(v['ocupacion_actual'] for v in viajes_generados),
                    'carros_utilizados': len(set(v['id_carro'] for v in viajes_generados))
                }
            }
            
        except Exception as e:
            logger.error(f"Error en asignación automática: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'errors': [str(e)]
            }
    
    def _algoritmo_asignacion(self, conductores: List[Dict], estudiantes: List[Dict], carros: List[Dict], fecha: str) -> List[Dict]:
        """
        Algoritmo para asignar estudiantes a carros con conductores
        
        Args:
            conductores: Lista de conductores disponibles
            estudiantes: Lista de todos los estudiantes
            carros: Lista de carros disponibles
            fecha: Fecha del viaje
            
        Returns:
            list: Lista de viajes generados
        """
        viajes_generados = []
        estudiantes_asignados = set()
        carros_usados = set()
        
        # Ordenar conductores por cantidad de licencias (más versátiles primero)
        conductores_ordenados = sorted(conductores, key=lambda c: len(c.get('tipos_licencia', [])), reverse=True)
        
        for conductor in conductores_ordenados:
            if conductor['matricola'] in estudiantes_asignados:
                continue
            
            # Encontrar carro compatible
            carro_asignado = None
            for carro in carros:
                if carro['id_carro'] in carros_usados:
                    continue
                
                if self._puede_conducir_carro(conductor, carro):
                    carro_asignado = carro
                    break
            
            if not carro_asignado:
                continue
            
            # Crear viaje de ida y vuelta
            pasajeros_ida = []
            pasajeros_vuelta = []
            capacidad_disponible = carro_asignado['capacidad_pasajeros'] - 1  # -1 por el conductor
            
            # Asignar pasajeros (estudiantes sin licencia primero)
            estudiantes_sin_conductor = [e for e in estudiantes if e['matricola'] not in estudiantes_asignados and e['matricola'] != conductor['matricola']]
            estudiantes_sin_licencia = [e for e in estudiantes_sin_conductor if not e.get('tiene_licencia', False)]
            otros_estudiantes = [e for e in estudiantes_sin_conductor if e.get('tiene_licencia', False)]
            
            # Priorizar estudiantes sin licencia
            for estudiante in estudiantes_sin_licencia[:capacidad_disponible]:
                pasajeros_ida.append(estudiante['matricola'])
                pasajeros_vuelta.append(estudiante['matricola'])
                estudiantes_asignados.add(estudiante['matricola'])
                capacidad_disponible -= 1
            
            # Llenar con otros estudiantes si hay espacio
            for estudiante in otros_estudiantes[:capacidad_disponible]:
                pasajeros_ida.append(estudiante['matricola'])
                pasajeros_vuelta.append(estudiante['matricola'])
                estudiantes_asignados.add(estudiante['matricola'])
                capacidad_disponible -= 1
            
            # Crear viaje de ida
            viaje_ida = {
                'id_viaje': f"ida_{fecha}_{conductor['matricola']}_{carro_asignado['id_carro']}",
                'fecha': fecha,
                'hora_salida': '07:30',  # Hora estándar de ida
                'origen': 'Seminario',
                'destino': 'Universidad Gregoriana',
                'id_carro': carro_asignado['id_carro'],
                'matricola_conductor': conductor['matricola'],
                'pasajeros': pasajeros_ida,
                'estado': 'planificado',
                'ocupacion_actual': 1 + len(pasajeros_ida),
                'capacidad_maxima': carro_asignado['capacidad_pasajeros'],
                'tipo_viaje': 'ida'
            }
            
            # Crear viaje de vuelta
            viaje_vuelta = {
                'id_viaje': f"vuelta_{fecha}_{conductor['matricola']}_{carro_asignado['id_carro']}",
                'fecha': fecha,
                'hora_salida': '18:00',  # Hora estándar de vuelta
                'origen': 'Universidad Gregoriana',
                'destino': 'Seminario',
                'id_carro': carro_asignado['id_carro'],
                'matricola_conductor': conductor['matricola'],
                'pasajeros': pasajeros_vuelta,
                'estado': 'planificado',
                'ocupacion_actual': 1 + len(pasajeros_vuelta),
                'capacidad_maxima': carro_asignado['capacidad_pasajeros'],
                'tipo_viaje': 'vuelta'
            }
            
            viajes_generados.extend([viaje_ida, viaje_vuelta])
            estudiantes_asignados.add(conductor['matricola'])
            carros_usados.add(carro_asignado['id_carro'])
        
        return viajes_generados
    
    def _puede_conducir_carro(self, conductor_data: Dict, carro_data: Dict) -> bool:
        """Verificar si un conductor puede manejar un carro específico"""
        if not conductor_data.get('tiene_licencia', False):
            return False
        
        tipos_licencia_conductor = conductor_data.get('tipos_licencia', [])
        tipo_carro = carro_data.get('tipo_carro')
        
        # Mapeo simplificado de compatibilidad
        compatibilidad = {
            'mini': ['B', 'C', 'D'],
            'compacto': ['B', 'C', 'D'],
            'familiar': ['B', 'C', 'D'],
            'furgoneta': ['C', 'D'],
            'microbus': ['D']
        }
        
        licencias_requeridas = compatibilidad.get(tipo_carro, [])
        return any(licencia in tipos_licencia_conductor for licencia in licencias_requeridas)
    
    def _calcular_total_estudiantes(self, ids_viajes: List[str]) -> int:
        """Calcular total de estudiantes en una lista de viajes"""
        total = 0
        for id_viaje in ids_viajes:
            viaje = self.obtener_viaje(id_viaje)
            if viaje:
                total += viaje.get('ocupacion_actual', 0)
        return total
    
    def _generar_id_viaje(self, fecha: str, hora: str) -> str:
        """Generar ID único para viaje"""
        fecha_clean = fecha.replace('-', '')
        hora_clean = hora.replace(':', '')
        timestamp = datetime.now().strftime('%H%M%S')
        return f"viaje_{fecha_clean}_{hora_clean}_{timestamp}"
    
    def _validar_datos_viaje(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Validar datos de viaje"""
        errores = []
        
        # Campos requeridos
        campos_requeridos = ['fecha', 'hora_salida', 'origen', 'destino', 'id_carro', 'matricola_conductor']
        for campo in campos_requeridos:
            if not datos.get(campo):
                errores.append(f"{campo} es requerido")
        
        # Validar formato de fecha
        if datos.get('fecha'):
            try:
                datetime.strptime(datos['fecha'], '%Y-%m-%d')
            except ValueError:
                errores.append("Formato de fecha inválido (usar YYYY-MM-DD)")
        
        # Validar formato de hora
        if datos.get('hora_salida'):
            try:
                datetime.strptime(datos['hora_salida'], '%H:%M')
            except ValueError:
                errores.append("Formato de hora inválido (usar HH:MM)")
        
        return {
            'valid': len(errores) == 0,
            'errors': errores
        }
