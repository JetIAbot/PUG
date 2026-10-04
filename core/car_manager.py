"""
CarManager - Gestor de carros para PUG Sistema de Carpooling
CRUD completo para gestión de vehículos del sistema
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from .models import Carro, TipoCarro, TipoCombustible, EstadoCarro, TipoLicencia, PertenenciaCarro
from .obsidian_manager import ObsidianManager

logger = logging.getLogger(__name__)

class CarManager:
    """Gestor principal para operaciones CRUD de carros"""
    
    def __init__(self):
        self.firebase = ObsidianManager()
        self.db = self.firebase.get_client()
        self.collection_name = 'carros'
    
    def crear_carro(self, carro_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear un nuevo carro en el sistema
        
        Args:
            carro_data: Datos del carro a crear
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Validar datos requeridos
            validacion = self._validar_datos_carro(carro_data)
            if not validacion['valid']:
                return {
                    'success': False,
                    'message': 'Datos inválidos',
                    'errors': validacion['errors']
                }
            
            # Verificar que no exista un carro con la misma placa
            placa_norm = carro_data['placa'].strip().upper()
            if self._existe_placa(placa_norm):
                return {
                    'success': False,
                    'message': 'Ya existe un carro con esa placa',
                    'errors': ['Placa duplicada']
                }
            
            # Usar placa normalizada como ID del documento
            id_carro = placa_norm
            
            # Crear objeto Carro
            carro = Carro(
                id_carro=id_carro,
                marca=carro_data['marca'],
                modelo=carro_data['modelo'],
                año=int(carro_data['año']),
                placa=carro_data['placa'],
                tipo_carro=TipoCarro(carro_data['tipo_carro']),
                tipo_combustible=TipoCombustible(carro_data['tipo_combustible']),
                capacidad_pasajeros=int(carro_data['capacidad_pasajeros']),
                pertenencia=self._normalizar_pertenencia(carro_data.get('pertenencia')),
                licencias_requeridas=self._normalizar_licencias_requeridas(carro_data.get('licencias_requeridas')),
                conductor_matricola=str(carro_data.get('conductor_matricola', '')).strip(),
                viajes_particulares=self._normalizar_viajes_particulares(carro_data.get('viajes_particulares')),
                observaciones=carro_data.get('observaciones', '')
            )
            
            # Guardar en Firebase
            doc_ref = self.db.collection(self.collection_name).document(id_carro)
            doc_ref.set(carro.to_dict())
            
            logger.info(f"Carro creado exitosamente: {id_carro} - {carro.marca} {carro.modelo}")
            
            return {
                'success': True,
                'message': 'Carro creado exitosamente',
                'data': carro.to_dict(),
                'id_carro': id_carro
            }
            
        except Exception as e:
            logger.error(f"Error creando carro: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'errors': [str(e)]
            }
    
    def obtener_carro(self, id_carro: str) -> Optional[Carro]:
        """
        Obtener un carro por su ID
        
        Args:
            id_carro: ID del carro
            
        Returns:
            Carro: Objeto carro o None si no existe
        """
        try:
            doc_ref = self.db.collection(self.collection_name).document(id_carro)
            doc = doc_ref.get()
            
            if doc.exists:
                return Carro.from_dict(doc.to_dict())
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo carro {id_carro}: {e}")
            return None
    
    def obtener_todos_carros(self, filtros: Dict[str, Any] = None) -> List[Carro]:
        """
        Obtener todos los carros con filtros opcionales
        
        Args:
            filtros: Filtros opcionales (estado, tipo_carro, etc.)
            
        Returns:
            List[Carro]: Lista de carros
        """
        try:
            query = self.db.collection(self.collection_name)
            
            # Aplicar filtros si se proporcionan
            if filtros:
                if 'estado' in filtros:
                    query = query.where('estado', '==', filtros['estado'])
                if 'tipo_carro' in filtros:
                    query = query.where('tipo_carro', '==', filtros['tipo_carro'])
                if 'disponible_para_licencia' in filtros:
                    # Este filtro se aplicará después de obtener los datos
                    pass
            
            docs = query.stream()
            carros = []
            
            for doc in docs:
                try:
                    carro = Carro.from_dict(doc.to_dict())
                    
                    # Aplicar filtro de licencia si se especifica
                    if filtros and 'disponible_para_licencia' in filtros:
                        licencias = [TipoLicencia(filtros['disponible_para_licencia'])]
                        if carro.puede_ser_conducido_por(licencias):
                            carros.append(carro)
                    else:
                        carros.append(carro)
                        
                except Exception as e:
                    logger.warning(f"Error procesando carro {doc.id}: {e}")
                    continue
            
            return carros
            
        except Exception as e:
            logger.error(f"Error obteniendo carros: {e}")
            return []
    
    def actualizar_carro(self, id_carro: str, datos_actualizacion: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar un carro existente
        
        Args:
            id_carro: ID del carro a actualizar
            datos_actualizacion: Datos a actualizar
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Verificar que el carro existe
            carro_actual = self.obtener_carro(id_carro)
            if not carro_actual:
                return {
                    'success': False,
                    'message': 'Carro no encontrado',
                    'errors': ['Carro inexistente']
                }
            
            id_actual = id_carro.strip().upper()
            nueva_placa = id_actual

            # Si se cambia la placa, verificar que no exista otra igual
            if 'placa' in datos_actualizacion and datos_actualizacion['placa']:
                nueva_placa = str(datos_actualizacion['placa']).strip().upper()
                if nueva_placa != id_actual and self._existe_placa(nueva_placa, excluir_id=id_actual):
                    return {
                        'success': False,
                        'message': 'Ya existe un carro con esa placa',
                        'errors': ['Placa duplicada']
                    }
            
            # Preparar datos para actualización
            datos_update = {}
            campos_actualizables = [
                'marca', 'modelo', 'año', 'placa', 'tipo_carro', 'tipo_combustible',
                'capacidad_pasajeros', 'estado', 'pertenencia', 'licencias_requeridas',
                'conductor_matricola', 'viajes_particulares', 'observaciones'
            ]
            
            for campo in campos_actualizables:
                if campo in datos_actualizacion:
                    valor = datos_actualizacion[campo]
                    
                    # Convertir enums a strings
                    if campo == 'tipo_carro' and isinstance(valor, str):
                        valor = TipoCarro(valor).value
                    elif campo == 'tipo_combustible' and isinstance(valor, str):
                        valor = TipoCombustible(valor).value
                    elif campo == 'estado' and isinstance(valor, str):
                        valor = EstadoCarro(valor).value
                    elif campo == 'pertenencia':
                        valor = self._normalizar_pertenencia(valor).value
                    elif campo == 'licencias_requeridas':
                        valor = self._normalizar_licencias_requeridas(valor)
                    elif campo == 'conductor_matricola':
                        valor = str(valor).strip()
                    elif campo == 'viajes_particulares':
                        valor = self._normalizar_viajes_particulares(valor)
                    elif campo in ['año', 'capacidad_pasajeros']:
                        valor = int(valor)
                    elif campo == 'placa':
                        valor = valor.upper()
                    
                    datos_update[campo] = valor
            
            # Asegurar consistencia entre placa e id_carro
            datos_update['placa'] = nueva_placa
            datos_update['id_carro'] = nueva_placa

            # Agregar timestamp de actualización
            datos_update['fecha_actualizacion'] = datetime.now().isoformat()

            # Si cambia placa, mover documento al nuevo ID
            if nueva_placa != id_actual:
                doc_actual = self.db.collection(self.collection_name).document(id_actual)
                doc_nuevo = self.db.collection(self.collection_name).document(nueva_placa)

                data_nueva = carro_actual.to_dict()
                data_nueva.update(datos_update)

                doc_nuevo.set(data_nueva)
                doc_actual.delete()
                carro_actualizado = self.obtener_carro(nueva_placa)
                logger.info(f"Carro actualizado exitosamente: {id_actual} -> {nueva_placa}")
            else:
                doc_ref = self.db.collection(self.collection_name).document(id_actual)
                doc_ref.update(datos_update)
                carro_actualizado = self.obtener_carro(id_actual)
                logger.info(f"Carro actualizado exitosamente: {id_actual}")
            
            return {
                'success': True,
                'message': 'Carro actualizado exitosamente',
                'data': carro_actualizado.to_dict() if carro_actualizado else None
            }
            
        except Exception as e:
            logger.error(f"Error actualizando carro {id_carro}: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'errors': [str(e)]
            }
    
    def eliminar_carro(self, id_carro: str) -> Dict[str, Any]:
        """
        Eliminar un carro del sistema
        
        Args:
            id_carro: ID del carro a eliminar
            
        Returns:
            dict: Resultado de la operación
        """
        try:
            # Verificar que el carro existe
            carro = self.obtener_carro(id_carro)
            if not carro:
                return {
                    'success': False,
                    'message': 'Carro no encontrado',
                    'errors': ['Carro inexistente']
                }
            
            # TODO: Verificar que no tenga viajes activos antes de eliminar
            # Esta validación se implementará cuando tengamos el módulo de viajes
            
            # Eliminar de Firebase
            doc_ref = self.db.collection(self.collection_name).document(id_carro)
            doc_ref.delete()
            
            logger.info(f"Carro eliminado exitosamente: {id_carro} - {carro.marca} {carro.modelo}")
            
            return {
                'success': True,
                'message': 'Carro eliminado exitosamente'
            }
            
        except Exception as e:
            logger.error(f"Error eliminando carro {id_carro}: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'errors': [str(e)]
            }
    
    def obtener_carros_disponibles(self, licencias: List[TipoLicencia] = None) -> List[Carro]:
        """
        Obtener carros disponibles, opcionalmente filtrados por licencias
        
        Args:
            licencias: Lista de licencias del conductor
            
        Returns:
            List[Carro]: Lista de carros disponibles
        """
        filtros = {'estado': EstadoCarro.DISPONIBLE.value}
        carros = self.obtener_todos_carros(filtros)
        
        if licencias:
            carros_compatibles = []
            for carro in carros:
                if carro.puede_ser_conducido_por(licencias):
                    carros_compatibles.append(carro)
            return carros_compatibles
        
        return carros
    
    def cambiar_estado_carro(self, id_carro: str, nuevo_estado: EstadoCarro) -> Dict[str, Any]:
        """
        Cambiar el estado de un carro
        
        Args:
            id_carro: ID del carro
            nuevo_estado: Nuevo estado del carro
            
        Returns:
            dict: Resultado de la operación
        """
        return self.actualizar_carro(id_carro, {'estado': nuevo_estado.value})
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de los carros
        
        Returns:
            dict: Estadísticas del sistema de carros
        """
        try:
            carros = self.obtener_todos_carros()
            
            # Contar por estado
            estados = {}
            for estado in EstadoCarro:
                estados[estado.value] = 0
            
            # Contar por tipo
            tipos = {}
            for tipo in TipoCarro:
                tipos[tipo.value] = 0
            
            # Contar por combustible
            combustibles = {}
            for combustible in TipoCombustible:
                combustibles[combustible.value] = 0
            
            total_capacidad = 0
            
            for carro in carros:
                estados[carro.estado.value] += 1
                tipos[carro.tipo_carro.value] += 1
                combustibles[carro.tipo_combustible.value] += 1
                total_capacidad += carro.capacidad_pasajeros
            
            return {
                'total_carros': len(carros),
                'por_estado': estados,
                'por_tipo': tipos,
                'por_combustible': combustibles,
                'capacidad_total': total_capacidad,
                'capacidad_promedio': round(total_capacidad / len(carros), 1) if carros else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    def _validar_datos_carro(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar datos de un carro
        
        Args:
            datos: Datos a validar
            
        Returns:
            dict: Resultado de validación
        """
        errores = []
        
        # Campos requeridos
        campos_requeridos = ['marca', 'modelo', 'año', 'placa', 'tipo_carro', 
                           'tipo_combustible', 'capacidad_pasajeros']
        
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                errores.append(f'{campo} es requerido')
        
        # Validaciones específicas
        if 'año' in datos:
            try:
                año = int(datos['año'])
                if año < 1900 or año > datetime.now().year + 1:
                    errores.append('Año inválido')
            except (ValueError, TypeError):
                errores.append('Año debe ser un número')
        
        if 'capacidad_pasajeros' in datos:
            try:
                capacidad = int(datos['capacidad_pasajeros'])
                if capacidad < 1 or capacidad > 50:
                    errores.append('Capacidad debe estar entre 1 y 50')
            except (ValueError, TypeError):
                errores.append('Capacidad debe ser un número')
        
        if 'placa' in datos:
            placa = datos['placa'].strip()
            if len(placa) < 3 or len(placa) > 10:
                errores.append('Placa debe tener entre 3 y 10 caracteres')
        
        # Validar enums
        if 'tipo_carro' in datos:
            try:
                TipoCarro(datos['tipo_carro'])
            except ValueError:
                errores.append('Tipo de carro inválido')
        
        if 'tipo_combustible' in datos:
            try:
                TipoCombustible(datos['tipo_combustible'])
            except ValueError:
                errores.append('Tipo de combustible inválido')

        if 'pertenencia' in datos and datos['pertenencia']:
            try:
                self._normalizar_pertenencia(datos['pertenencia'])
            except ValueError:
                errores.append('Pertenencia inválida')

        if 'licencias_requeridas' in datos and datos['licencias_requeridas']:
            try:
                self._normalizar_licencias_requeridas(datos['licencias_requeridas'])
            except ValueError as exc:
                errores.append(str(exc))
        
        return {
            'valid': len(errores) == 0,
            'errors': errores
        }
    
    def _existe_placa(self, placa: str, excluir_id: str = None) -> bool:
        """
        Verificar si ya existe un carro con la placa dada.
        Como la placa es el ID del documento, basta con verificar si existe.
        """
        placa_norm = placa.strip().upper()
        if excluir_id and placa_norm == excluir_id:
            return False
        doc = self.db.collection(self.collection_name).document(placa_norm).get()
        return doc.exists

    def _normalizar_pertenencia(self, pertenencia: Any) -> PertenenciaCarro:
        """Normalizar pertenencia a enum."""
        valor = str(pertenencia or PertenenciaCarro.INSTITUCIONAL.value).strip().lower()
        return PertenenciaCarro(valor)

    def _normalizar_licencias_requeridas(self, licencias: Any) -> List[str]:
        """Normalizar licencias requeridas a lista de códigos."""
        if licencias is None or licencias == "":
            return []
        if isinstance(licencias, str):
            items = [item.strip().upper() for item in licencias.split(',') if item.strip()]
        elif isinstance(licencias, (list, tuple, set)):
            items = [str(item).strip().upper() for item in licencias if str(item).strip()]
        else:
            raise ValueError('Licencias requeridas inválidas')

        licencias_validas = {lic.value for lic in TipoLicencia}
        for item in items:
            if item not in licencias_validas:
                raise ValueError(f'Licencia requerida inválida: {item}')
        return items

    def _normalizar_viajes_particulares(self, viajes: Any) -> List[Dict[str, Any]]:
        """Normalizar definición de viajes particulares."""
        if not viajes:
            return []
        if isinstance(viajes, dict):
            viajes = [viajes]
        if not isinstance(viajes, list):
            raise ValueError('Viajes particulares inválidos')

        normalizados = []
        for viaje in viajes:
            if not isinstance(viaje, dict):
                continue
            entry = {
                'dia': str(viaje.get('dia', '')).strip(),
                'tipo': str(viaje.get('tipo', 'ida_vuelta')).strip().lower(),
                'estudiantes': [str(m).strip() for m in viaje.get('estudiantes', []) if str(m).strip()],
                'conductor_matricola': str(viaje.get('conductor_matricola', '')).strip(),
                'observaciones': str(viaje.get('observaciones', '')).strip(),
            }
            if not entry['dia']:
                continue
            normalizados.append(entry)
        return normalizados

    def definir_viajes_particulares(self, id_carro: str, viajes_particulares: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Actualizar las definiciones de viaje para un carro particular."""
        return self.actualizar_carro(id_carro, {'viajes_particulares': viajes_particulares})
