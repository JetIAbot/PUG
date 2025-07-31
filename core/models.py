"""
Models - Modelos de datos para PUG Sistema de Carpooling
Definiciones de entidades principales del sistema de viajes compartidos
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class EstadoCarro(Enum):
    """Estados posibles de un carro"""
    DISPONIBLE = "disponible"
    EN_USO = "en_uso"
    MANTENIMIENTO = "mantenimiento"
    FUERA_SERVICIO = "fuera_servicio"

class TipoCombustible(Enum):
    """Tipos de combustible según normativa italiana"""
    GASOLINA = "gasolina"
    DIESEL = "diesel"
    HIBRIDO = "hibrido"
    ELECTRICO = "electrico"
    GLP = "glp"  # Gas Licuado del Petróleo
    METANO = "metano"

class TipoCarro(Enum):
    """Tipos de carros según normativa italiana de licencias"""
    MINI = "mini"           # Hasta 4 plazas - Licencia B
    COMPACTO = "compacto"   # 5 plazas - Licencia B
    FAMILIAR = "familiar"   # 6-7 plazas - Licencia B
    FURGONETA = "furgoneta" # 8-9 plazas - Licencia B o C1
    MICROBUS = "microbus"   # Más de 9 plazas - Licencia D1

class TipoLicencia(Enum):
    """Tipos de licencia de conducir italiana"""
    A1 = "A1"  # Motocicletas hasta 125cc
    A2 = "A2"  # Motocicletas hasta 35kW
    A = "A"    # Motocicletas sin límite
    B = "B"    # Automóviles hasta 3.5t y hasta 8 pasajeros
    C1 = "C1"  # Vehículos 3.5t-7.5t
    C = "C"    # Vehículos más de 7.5t
    D1 = "D1"  # Minibuses hasta 16 pasajeros
    D = "D"    # Autobuses más de 16 pasajeros
    BE = "BE"  # B + remolque
    CE = "CE"  # C + remolque
    DE = "DE"  # D + remolque

class EstadoViaje(Enum):
    """Estados de un viaje"""
    PLANIFICADO = "planificado"
    EN_CURSO = "en_curso"
    COMPLETADO = "completado"
    CANCELADO = "cancelado"

class EstadoLista(Enum):
    """Estados de una lista de viajes"""
    BORRADOR = "borrador"
    GENERADA = "generada"
    APROBADA = "aprobada"
    PUBLICADA = "publicada"
    ARCHIVADA = "archivada"

# Matriz de compatibilidad licencia-tipo de carro
MATRIZ_LICENCIA_CARRO = {
    TipoLicencia.B: [TipoCarro.MINI, TipoCarro.COMPACTO, TipoCarro.FAMILIAR],
    TipoLicencia.C1: [TipoCarro.MINI, TipoCarro.COMPACTO, TipoCarro.FAMILIAR, TipoCarro.FURGONETA],
    TipoLicencia.C: [TipoCarro.MINI, TipoCarro.COMPACTO, TipoCarro.FAMILIAR, TipoCarro.FURGONETA],
    TipoLicencia.D1: [TipoCarro.MINI, TipoCarro.COMPACTO, TipoCarro.FAMILIAR, TipoCarro.FURGONETA, TipoCarro.MICROBUS],
    TipoLicencia.D: [TipoCarro.MINI, TipoCarro.COMPACTO, TipoCarro.FAMILIAR, TipoCarro.FURGONETA, TipoCarro.MICROBUS],
    TipoLicencia.BE: [TipoCarro.MINI, TipoCarro.COMPACTO, TipoCarro.FAMILIAR],
    TipoLicencia.CE: [TipoCarro.MINI, TipoCarro.COMPACTO, TipoCarro.FAMILIAR, TipoCarro.FURGONETA],
    TipoLicencia.DE: [TipoCarro.MINI, TipoCarro.COMPACTO, TipoCarro.FAMILIAR, TipoCarro.FURGONETA, TipoCarro.MICROBUS]
}

# Capacidades típicas por tipo de carro
CAPACIDADES_CARRO = {
    TipoCarro.MINI: {"min": 2, "max": 4},
    TipoCarro.COMPACTO: {"min": 4, "max": 5},
    TipoCarro.FAMILIAR: {"min": 5, "max": 7},
    TipoCarro.FURGONETA: {"min": 6, "max": 9},
    TipoCarro.MICROBUS: {"min": 10, "max": 16}
}

class Carro:
    """Modelo de datos para un carro del sistema"""
    
    def __init__(self, 
                 id_carro: str,
                 marca: str,
                 modelo: str,
                 año: int,
                 placa: str,
                 tipo_carro: TipoCarro,
                 tipo_combustible: TipoCombustible,
                 capacidad_pasajeros: int,
                 estado: EstadoCarro = EstadoCarro.DISPONIBLE,
                 observaciones: str = "",
                 fecha_creacion: datetime = None):
        
        self.id_carro = id_carro
        self.marca = marca
        self.modelo = modelo
        self.año = año
        self.placa = placa.upper()
        self.tipo_carro = tipo_carro
        self.tipo_combustible = tipo_combustible
        self.capacidad_pasajeros = capacidad_pasajeros
        self.estado = estado
        self.observaciones = observaciones
        self.fecha_creacion = fecha_creacion or datetime.now()
        self.fecha_actualizacion = datetime.now()
        
        # Validar capacidad según tipo de carro
        self._validar_capacidad()
    
    def _validar_capacidad(self):
        """Validar que la capacidad sea apropiada para el tipo de carro"""
        capacidad_esperada = CAPACIDADES_CARRO.get(self.tipo_carro)
        if capacidad_esperada:
            if not (capacidad_esperada["min"] <= self.capacidad_pasajeros <= capacidad_esperada["max"]):
                logger.warning(f"Capacidad {self.capacidad_pasajeros} fuera del rango esperado para {self.tipo_carro.value}")
    
    def puede_ser_conducido_por(self, licencias: List[TipoLicencia]) -> bool:
        """Verificar si el carro puede ser conducido con las licencias dadas"""
        for licencia in licencias:
            if self.tipo_carro in MATRIZ_LICENCIA_CARRO.get(licencia, []):
                return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para Firebase"""
        return {
            'id_carro': self.id_carro,
            'marca': self.marca,
            'modelo': self.modelo,
            'año': self.año,
            'placa': self.placa,
            'tipo_carro': self.tipo_carro.value,
            'tipo_combustible': self.tipo_combustible.value,
            'capacidad_pasajeros': self.capacidad_pasajeros,
            'estado': self.estado.value,
            'observaciones': self.observaciones,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Carro':
        """Crear instancia desde diccionario de Firebase"""
        return cls(
            id_carro=data['id_carro'],
            marca=data['marca'],
            modelo=data['modelo'],
            año=data['año'],
            placa=data['placa'],
            tipo_carro=TipoCarro(data['tipo_carro']),
            tipo_combustible=TipoCombustible(data['tipo_combustible']),
            capacidad_pasajeros=data['capacidad_pasajeros'],
            estado=EstadoCarro(data.get('estado', 'disponible')),
            observaciones=data.get('observaciones', ''),
            fecha_creacion=datetime.fromisoformat(data.get('fecha_creacion', datetime.now().isoformat()))
        )

class Estudiante:
    """Modelo extendido de estudiante con información de carpooling"""
    
    def __init__(self,
                 matricola: str,
                 nombre: str,
                 apellido: str,
                 email: str,
                 telefono: str = "",
                 tiene_licencia: bool = False,
                 tipos_licencia: List[TipoLicencia] = None,
                 fecha_vencimiento_licencia: date = None,
                 viaja_hoy: bool = True,
                 preferencias: Dict[str, Any] = None,
                 historial_conducciones: List[str] = None):
        
        self.matricola = matricola
        self.nombre = nombre
        self.apellido = apellido
        self.email = email
        self.telefono = telefono
        self.tiene_licencia = tiene_licencia
        self.tipos_licencia = tipos_licencia or []
        self.fecha_vencimiento_licencia = fecha_vencimiento_licencia
        self.viaja_hoy = viaja_hoy
        self.preferencias = preferencias or {}
        self.historial_conducciones = historial_conducciones or []
        self.fecha_actualizacion = datetime.now()
    
    @property
    def licencia_vigente(self) -> bool:
        """Verificar si la licencia está vigente"""
        if not self.tiene_licencia or not self.fecha_vencimiento_licencia:
            return False
        return self.fecha_vencimiento_licencia > date.today()
    
    @property
    def puede_conducir(self) -> bool:
        """Verificar si puede conducir (tiene licencia vigente)"""
        return self.tiene_licencia and self.licencia_vigente and len(self.tipos_licencia) > 0
    
    def puede_conducir_carro(self, carro: Carro) -> bool:
        """Verificar si puede conducir un carro específico"""
        if not self.puede_conducir:
            return False
        return carro.puede_ser_conducido_por(self.tipos_licencia)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para Firebase"""
        return {
            'matricola': self.matricola,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'email': self.email,
            'telefono': self.telefono,
            'tiene_licencia': self.tiene_licencia,
            'tipos_licencia': [t.value for t in self.tipos_licencia],
            'fecha_vencimiento_licencia': self.fecha_vencimiento_licencia.isoformat() if self.fecha_vencimiento_licencia else None,
            'viaja_hoy': self.viaja_hoy,
            'preferencias': self.preferencias,
            'historial_conducciones': self.historial_conducciones,
            'fecha_actualizacion': self.fecha_actualizacion.isoformat()
        }

class Viaje:
    """Modelo de datos para un viaje"""
    
    def __init__(self,
                 id_viaje: str,
                 fecha: date,
                 hora_salida: str,
                 origen: str,
                 destino: str,
                 carro: Carro,
                 conductor: Estudiante,
                 pasajeros: List[Estudiante] = None,
                 estado: EstadoViaje = EstadoViaje.PLANIFICADO,
                 observaciones: str = ""):
        
        self.id_viaje = id_viaje
        self.fecha = fecha
        self.hora_salida = hora_salida
        self.origen = origen
        self.destino = destino
        self.carro = carro
        self.conductor = conductor
        self.pasajeros = pasajeros or []
        self.estado = estado
        self.observaciones = observaciones
        self.fecha_creacion = datetime.now()
    
    @property
    def ocupacion_actual(self) -> int:
        """Número actual de ocupantes (conductor + pasajeros)"""
        return 1 + len(self.pasajeros)  # +1 por el conductor
    
    @property
    def plazas_disponibles(self) -> int:
        """Plazas disponibles en el viaje"""
        return self.carro.capacidad_pasajeros - self.ocupacion_actual
    
    @property
    def esta_lleno(self) -> bool:
        """Verificar si el viaje está lleno"""
        return self.plazas_disponibles <= 0
    
    def puede_agregar_pasajero(self, estudiante: Estudiante) -> bool:
        """Verificar si se puede agregar un pasajero"""
        if self.esta_lleno:
            return False
        if estudiante.matricola == self.conductor.matricola:
            return False
        if any(p.matricola == estudiante.matricola for p in self.pasajeros):
            return False
        return True
    
    def agregar_pasajero(self, estudiante: Estudiante) -> bool:
        """Agregar un pasajero al viaje"""
        if self.puede_agregar_pasajero(estudiante):
            self.pasajeros.append(estudiante)
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para Firebase"""
        return {
            'id_viaje': self.id_viaje,
            'fecha': self.fecha.isoformat(),
            'hora_salida': self.hora_salida,
            'origen': self.origen,
            'destino': self.destino,
            'carro': self.carro.to_dict(),
            'conductor': self.conductor.to_dict(),
            'pasajeros': [p.to_dict() for p in self.pasajeros],
            'estado': self.estado.value,
            'observaciones': self.observaciones,
            'fecha_creacion': self.fecha_creacion.isoformat()
        }

class ListaViajes:
    """Modelo para una lista diaria de viajes"""
    
    def __init__(self,
                 id_lista: str,
                 fecha: date,
                 viajes_ida: List[Viaje] = None,
                 viajes_vuelta: List[Viaje] = None,
                 estado: EstadoLista = EstadoLista.BORRADOR,
                 creado_por: str = "",
                 observaciones: str = ""):
        
        self.id_lista = id_lista
        self.fecha = fecha
        self.viajes_ida = viajes_ida or []
        self.viajes_vuelta = viajes_vuelta or []
        self.estado = estado
        self.creado_por = creado_por
        self.observaciones = observaciones
        self.fecha_creacion = datetime.now()
        self.fecha_actualizacion = datetime.now()
    
    @property
    def total_estudiantes_ida(self) -> int:
        """Total de estudiantes en viajes de ida"""
        return sum(viaje.ocupacion_actual for viaje in self.viajes_ida)
    
    @property
    def total_estudiantes_vuelta(self) -> int:
        """Total de estudiantes en viajes de vuelta"""
        return sum(viaje.ocupacion_actual for viaje in self.viajes_vuelta)
    
    @property
    def total_carros_usados(self) -> int:
        """Total de carros únicos usados"""
        carros_ida = {viaje.carro.id_carro for viaje in self.viajes_ida}
        carros_vuelta = {viaje.carro.id_carro for viaje in self.viajes_vuelta}
        return len(carros_ida.union(carros_vuelta))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario para Firebase"""
        return {
            'id_lista': self.id_lista,
            'fecha': self.fecha.isoformat(),
            'viajes_ida': [v.to_dict() for v in self.viajes_ida],
            'viajes_vuelta': [v.to_dict() for v in self.viajes_vuelta],
            'estado': self.estado.value,
            'creado_por': self.creado_por,
            'observaciones': self.observaciones,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_actualizacion': self.fecha_actualizacion.isoformat(),
            'estadisticas': {
                'total_estudiantes_ida': self.total_estudiantes_ida,
                'total_estudiantes_vuelta': self.total_estudiantes_vuelta,
                'total_carros_usados': self.total_carros_usados
            }
        }

def validar_compatibilidad_licencia_carro(licencias: List[TipoLicencia], tipo_carro: TipoCarro) -> bool:
    """Función utilitaria para validar compatibilidad licencia-carro"""
    for licencia in licencias:
        if tipo_carro in MATRIZ_LICENCIA_CARRO.get(licencia, []):
            return True
    return False

def obtener_carros_compatibles(licencias: List[TipoLicencia]) -> List[TipoCarro]:
    """Obtener tipos de carros que se pueden conducir con las licencias dadas"""
    carros_compatibles = set()
    for licencia in licencias:
        carros_compatibles.update(MATRIZ_LICENCIA_CARRO.get(licencia, []))
    return list(carros_compatibles)
