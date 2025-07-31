"""
StudentManager - Gestor de estudiantes para PUG Sistema de Carpooling
CRUD completo para gestión de estudiantes del sistema
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from firebase_admin import firestore

from .models import Estudiante, TipoLicencia
from .firebase_manager import FirebaseManager

logger = logging.getLogger(__name__)

class StudentManager:
    """Gestor principal para operaciones CRUD de estudiantes"""
    
    def __init__(self):
        self.firebase = FirebaseManager()
        self.db = self.firebase.get_client()
        self.collection_name = 'estudiantes'
        
        if not self.db:
            raise Exception("No se pudo conectar a Firebase")
    
    def crear_estudiante(self, estudiante_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear un nuevo estudiante en el sistema
        
        Args:
            estudiante_data: Datos del estudiante a crear
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validar datos requeridos
            validacion = self._validar_datos_estudiante(estudiante_data)
            if not validacion['valid']:
                return {
                    'success': False,
                    'message': 'Datos inválidos',
                    'errors': validacion['errors']
                }
            
            # Verificar que no exista un estudiante con la misma matrícula
            if self._existe_matricula(estudiante_data['matricola']):
                return {
                    'success': False,
                    'message': 'Ya existe un estudiante con esa matrícula',
                    'errors': ['Matrícula duplicada']
                }
            
            # Crear objeto Estudiante
            estudiante = Estudiante(
                matricola=estudiante_data['matricola'],
                nombre=estudiante_data['nombre'],
                apellido=estudiante_data['apellido'],
                email=estudiante_data['email'],
                telefono=estudiante_data.get('telefono', ''),
                tiene_licencia=estudiante_data.get('tiene_licencia', False),
                tipos_licencia=[TipoLicencia(t) for t in estudiante_data.get('tipos_licencia', [])],
                fecha_vencimiento_licencia=self._parse_fecha(estudiante_data.get('fecha_vencimiento_licencia')),
                viaja_hoy=estudiante_data.get('viaja_hoy', True),
                preferencias=estudiante_data.get('preferencias', {}),
                historial_conducciones=estudiante_data.get('historial_conducciones', [])
            )
            
            # Guardar en Firebase
            doc_ref = self.db.collection(self.collection_name).document(estudiante.matricola)
            doc_ref.set(estudiante.to_dict())
            
            logger.info(f"Estudiante creado exitosamente: {estudiante.matricola} - {estudiante.nombre} {estudiante.apellido}")
            
            return {
                'success': True,
                'message': 'Estudiante creado exitosamente',
                'data': estudiante.to_dict(),
                'id': estudiante.matricola
            }
            
        except Exception as e:
            logger.error(f"Error creando estudiante: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'errors': [str(e)]
            }
    
    def obtener_estudiante(self, matricola: str) -> Optional[Dict[str, Any]]:
        """
        Obtener un estudiante por matrícula
        
        Args:
            matricola: Matrícula del estudiante
            
        Returns:
            dict: Datos del estudiante o None si no existe
        """
        try:
            doc_ref = self.db.collection(self.collection_name).document(matricola)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                logger.info(f"Estudiante encontrado: {matricola}")
                return data
            else:
                logger.warning(f"Estudiante no encontrado: {matricola}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo estudiante {matricola}: {e}")
            return None
    
    def listar_estudiantes(self, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Listar todos los estudiantes con filtros opcionales
        
        Args:
            filtros: Diccionario con filtros a aplicar
            
        Returns:
            list: Lista de estudiantes
        """
        try:
            query = self.db.collection(self.collection_name)
            
            # Aplicar filtros si se proporcionan
            if filtros:
                if 'tiene_licencia' in filtros:
                    query = query.where('tiene_licencia', '==', filtros['tiene_licencia'])
                
                if 'viaja_hoy' in filtros:
                    query = query.where('viaja_hoy', '==', filtros['viaja_hoy'])
                
                if 'tipos_licencia' in filtros:
                    # Filtrar por al menos uno de los tipos de licencia
                    query = query.where('tipos_licencia', 'array_contains_any', filtros['tipos_licencia'])
            
            # Ejecutar consulta
            docs = query.stream()
            estudiantes = []
            
            for doc in docs:
                data = doc.to_dict()
                data['matricola'] = doc.id  # Asegurar que tenga la matrícula
                estudiantes.append(data)
            
            logger.info(f"Encontrados {len(estudiantes)} estudiantes")
            return estudiantes
            
        except Exception as e:
            logger.error(f"Error listando estudiantes: {e}")
            return []
    
    def actualizar_estudiante(self, matricola: str, datos_actualizacion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar un estudiante existente
        
        Args:
            matricola: Matrícula del estudiante
            datos_actualizacion: Datos a actualizar
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Verificar que el estudiante existe
            estudiante_actual = self.obtener_estudiante(matricola)
            if not estudiante_actual:
                return {
                    'success': False,
                    'message': 'Estudiante no encontrado',
                    'errors': ['Matrícula no existe']
                }
            
            # Validar datos de actualización
            validacion = self._validar_datos_actualizacion(datos_actualizacion)
            if not validacion['valid']:
                return {
                    'success': False,
                    'message': 'Datos de actualización inválidos',
                    'errors': validacion['errors']
                }
            
            # Preparar datos para actualización
            datos_actualizados = datos_actualizacion.copy()
            datos_actualizados['fecha_actualizacion'] = datetime.now().isoformat()
            
            # Procesar tipos de licencia si se proporcionan
            if 'tipos_licencia' in datos_actualizados:
                datos_actualizados['tipos_licencia'] = [
                    t if isinstance(t, str) else t.value 
                    for t in datos_actualizados['tipos_licencia']
                ]
            
            # Procesar fecha de vencimiento
            if 'fecha_vencimiento_licencia' in datos_actualizados:
                fecha = self._parse_fecha(datos_actualizados['fecha_vencimiento_licencia'])
                datos_actualizados['fecha_vencimiento_licencia'] = fecha.isoformat() if fecha else None
            
            # Actualizar en Firebase
            doc_ref = self.db.collection(self.collection_name).document(matricola)
            doc_ref.update(datos_actualizados)
            
            logger.info(f"Estudiante actualizado: {matricola}")
            
            return {
                'success': True,
                'message': 'Estudiante actualizado exitosamente',
                'data': datos_actualizados
            }
            
        except Exception as e:
            logger.error(f"Error actualizando estudiante {matricola}: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'errors': [str(e)]
            }
    
    def eliminar_estudiante(self, matricola: str) -> Dict[str, Any]:
        """
        Eliminar un estudiante del sistema
        
        Args:
            matricola: Matrícula del estudiante a eliminar
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Verificar que el estudiante existe
            estudiante = self.obtener_estudiante(matricola)
            if not estudiante:
                return {
                    'success': False,
                    'message': 'Estudiante no encontrado',
                    'errors': ['Matrícula no existe']
                }
            
            # Eliminar de Firebase
            doc_ref = self.db.collection(self.collection_name).document(matricola)
            doc_ref.delete()
            
            logger.info(f"Estudiante eliminado: {matricola}")
            
            return {
                'success': True,
                'message': 'Estudiante eliminado exitosamente',
                'data': {'matricola': matricola}
            }
            
        except Exception as e:
            logger.error(f"Error eliminando estudiante {matricola}: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'errors': [str(e)]
            }
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del sistema de estudiantes
        
        Returns:
            dict: Estadísticas completas
        """
        try:
            estudiantes = self.listar_estudiantes()
            
            # Estadísticas básicas
            total_estudiantes = len(estudiantes)
            con_licencia = len([e for e in estudiantes if e.get('tiene_licencia', False)])
            viajan_hoy = len([e for e in estudiantes if e.get('viaja_hoy', True)])
            
            # Estadísticas por tipo de licencia
            licencias_count = {}
            for estudiante in estudiantes:
                for licencia in estudiante.get('tipos_licencia', []):
                    licencias_count[licencia] = licencias_count.get(licencia, 0) + 1
            
            # Licencias vigentes
            hoy = date.today()
            licencias_vigentes = 0
            for estudiante in estudiantes:
                if estudiante.get('tiene_licencia') and estudiante.get('fecha_vencimiento_licencia'):
                    try:
                        vencimiento = datetime.fromisoformat(estudiante['fecha_vencimiento_licencia']).date()
                        if vencimiento > hoy:
                            licencias_vigentes += 1
                    except:
                        pass
            
            estadisticas = {
                'resumen': {
                    'total_estudiantes': total_estudiantes,
                    'con_licencia': con_licencia,
                    'sin_licencia': total_estudiantes - con_licencia,
                    'viajan_hoy': viajan_hoy,
                    'no_viajan_hoy': total_estudiantes - viajan_hoy,
                    'licencias_vigentes': licencias_vigentes,
                    'porcentaje_con_licencia': round((con_licencia / total_estudiantes * 100) if total_estudiantes > 0 else 0, 1)
                },
                'por_tipo_licencia': licencias_count,
                'conductores_potenciales': con_licencia,
                'fecha_calculo': datetime.now().isoformat()
            }
            
            logger.info("Estadísticas de estudiantes calculadas")
            return estadisticas
            
        except Exception as e:
            logger.error(f"Error calculando estadísticas: {e}")
            return {}
    
    def buscar_conductores_disponibles(self, tipos_licencia_requeridos: List[str] = None) -> List[Dict[str, Any]]:
        """
        Buscar estudiantes que pueden actuar como conductores
        
        Args:
            tipos_licencia_requeridos: Lista de tipos de licencia requeridos
            
        Returns:
            list: Lista de conductores disponibles
        """
        try:
            filtros = {'tiene_licencia': True, 'viaja_hoy': True}
            
            if tipos_licencia_requeridos:
                filtros['tipos_licencia'] = tipos_licencia_requeridos
            
            conductores = self.listar_estudiantes(filtros)
            
            # Filtrar por licencia vigente
            hoy = date.today()
            conductores_vigentes = []
            
            for conductor in conductores:
                if conductor.get('fecha_vencimiento_licencia'):
                    try:
                        vencimiento = datetime.fromisoformat(conductor['fecha_vencimiento_licencia']).date()
                        if vencimiento > hoy:
                            conductores_vigentes.append(conductor)
                    except:
                        pass
            
            logger.info(f"Encontrados {len(conductores_vigentes)} conductores disponibles")
            return conductores_vigentes
            
        except Exception as e:
            logger.error(f"Error buscando conductores: {e}")
            return []
    
    def _validar_datos_estudiante(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Validar datos de estudiante"""
        errores = []
        
        # Campos requeridos
        campos_requeridos = ['matricola', 'nombre', 'apellido', 'email']
        for campo in campos_requeridos:
            if not datos.get(campo):
                errores.append(f"{campo} es requerido")
        
        # Validar matrícula
        if datos.get('matricola'):
            matricola = str(datos['matricola']).strip()
            if len(matricola) < 6 or len(matricola) > 10:
                errores.append("Matrícula debe tener entre 6 y 10 caracteres")
        
        # Validar email
        if datos.get('email') and '@' not in datos['email']:
            errores.append("Email debe tener formato válido")
        
        # Validar tipos de licencia
        if datos.get('tipos_licencia'):
            try:
                for tipo in datos['tipos_licencia']:
                    if isinstance(tipo, str):
                        TipoLicencia(tipo)
                    elif hasattr(tipo, 'value'):
                        TipoLicencia(tipo.value)
            except ValueError:
                errores.append("Tipo de licencia inválido")
        
        return {
            'valid': len(errores) == 0,
            'errors': errores
        }
    
    def _validar_datos_actualizacion(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Validar datos de actualización"""
        errores = []
        
        # Validar email si se proporciona
        if 'email' in datos and datos['email'] and '@' not in datos['email']:
            errores.append("Email debe tener formato válido")
        
        # Validar tipos de licencia si se proporcionan
        if 'tipos_licencia' in datos:
            try:
                for tipo in datos['tipos_licencia']:
                    if isinstance(tipo, str):
                        TipoLicencia(tipo)
                    elif hasattr(tipo, 'value'):
                        TipoLicencia(tipo.value)
            except ValueError:
                errores.append("Tipo de licencia inválido")
        
        return {
            'valid': len(errores) == 0,
            'errors': errores
        }
    
    def _existe_matricula(self, matricola: str) -> bool:
        """Verificar si existe una matrícula"""
        try:
            doc_ref = self.db.collection(self.collection_name).document(matricola)
            doc = doc_ref.get()
            return doc.exists
        except:
            return False
    
    def _parse_fecha(self, fecha_str: Any) -> Optional[date]:
        """Convertir string a fecha"""
        if not fecha_str:
            return None
        
        try:
            if isinstance(fecha_str, str):
                # Intentar varios formatos
                formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
                for formato in formatos:
                    try:
                        return datetime.strptime(fecha_str, formato).date()
                    except ValueError:
                        continue
            elif isinstance(fecha_str, date):
                return fecha_str
            elif isinstance(fecha_str, datetime):
                return fecha_str.date()
        except:
            pass
        
        return None
