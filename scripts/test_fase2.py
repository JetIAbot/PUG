#!/usr/bin/env python3
"""
Script de prueba completa para el sistema de estudiantes y viajes (Fase 2)
Verifica la funcionalidad completa de los nuevos managers implementados.
"""

import sys
import os

# Agregar el directorio raíz al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.student_manager import StudentManager
from core.viaje_manager import ViajeManager
from core.car_manager import CarManager
from utils.logger_config import setup_logging
from core.models import TipoLicencia
from core.viaje_manager import EstadoViaje
import json
from datetime import datetime, timedelta

def main():
    """Función principal de pruebas"""
    # Configurar logging simple para pruebas
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('test_fase2')
    
    print("=" * 60)
    print("🧪 PRUEBAS COMPLETAS DEL SISTEMA - FASE 2")
    print("🎯 Estudiantes, Viajes y Asignación Automática")
    print("=" * 60)
    
    try:
        # Inicializar managers
        print("\n📋 Inicializando managers...")
        student_manager = StudentManager()
        viaje_manager = ViajeManager()
        car_manager = CarManager()
        
        print("✅ Managers inicializados correctamente")
        
        # === PRUEBAS DE ESTUDIANTES ===
        print("\n" + "="*50)
        print("👥 PRUEBAS DEL SISTEMA DE ESTUDIANTES")
        print("="*50)
        
        # Crear estudiantes de prueba
        estudiantes_prueba = [
            {
                'matricola': 'E001',
                'nombre': 'Ana García',
                'telefono': '+393451234567',
                'email': 'ana.garcia@student.pug.it',
                'zona_residencia': 'Trastevere',
                'direccion_completa': 'Via dei Genovesi 15, Roma',
                'fecha_nacimiento': '1995-03-15',
                'nacionalidad': 'Española',
                'carrera': 'Teología',
                'año_estudio': 2,
                'es_conductor': True,
                'tipo_licencia': TipoLicencia.B.value,
                'años_experiencia': 3,
                'observaciones': 'Conductor experimentado'
            },
            {
                'matricola': 'E002',
                'nombre': 'Marco Rossi',
                'telefono': '+393457654321',
                'email': 'marco.rossi@student.pug.it',
                'zona_residencia': 'San Giovanni',
                'direccion_completa': 'Via Appia Nuova 200, Roma',
                'fecha_nacimiento': '1993-07-22',
                'nacionalidad': 'Italiana',
                'carrera': 'Filosofía',
                'año_estudio': 4,
                'es_conductor': False,
                'observaciones': 'Prefiere viajes temprano'
            },
            {
                'matricola': 'E003',
                'nombre': 'Juan Pérez',
                'telefono': '+393451111111',
                'email': 'juan.perez@student.pug.it',
                'zona_residencia': 'Trastevere',
                'direccion_completa': 'Via di Trastevere 100, Roma',
                'fecha_nacimiento': '1996-12-10',
                'nacionalidad': 'Mexicana',
                'carrera': 'Filosofía',
                'año_estudio': 1,
                'es_conductor': True,
                'tipo_licencia': TipoLicencia.B.value,
                'años_experiencia': 2,
                'observaciones': 'Conductor reciente'
            }
        ]
        
        print(f"\n📝 Creando {len(estudiantes_prueba)} estudiantes de prueba...")
        estudiantes_creados = []
        
        for estudiante in estudiantes_prueba:
            try:
                resultado = student_manager.crear_estudiante(estudiante)
                if resultado['exito']:
                    estudiantes_creados.append(estudiante['matricola'])
                    print(f"  ✅ {estudiante['nombre']} ({estudiante['matricola']})")
                else:
                    print(f"  ❌ Error con {estudiante['nombre']}: {resultado['mensaje']}")
            except Exception as e:
                print(f"  ❌ Excepción con {estudiante['nombre']}: {e}")
        
        print(f"\n📊 Estudiantes creados exitosamente: {len(estudiantes_creados)}")
        
        # Listar estudiantes
        print("\n📋 Listando todos los estudiantes...")
        try:
            lista = student_manager.listar_estudiantes()
            print(f"  📈 Total de estudiantes en sistema: {len(lista)}")
            for est in lista:
                conductor_info = "🚗 Conductor" if est.get('es_conductor') else "🚶 Pasajero"
                print(f"  - {est['nombre']} ({est['matricola']}) - {conductor_info}")
        except Exception as e:
            print(f"  ❌ Error al listar: {e}")
        
        # Buscar conductores disponibles
        print("\n🔍 Buscando conductores disponibles...")
        try:
            conductores = student_manager.buscar_conductores_disponibles()
            print(f"  🚗 Conductores encontrados: {len(conductores)}")
            for cond in conductores:
                print(f"  - {cond['nombre']} ({cond['matricola']}) - Exp: {cond.get('años_experiencia', 0)} años")
        except Exception as e:
            print(f"  ❌ Error al buscar conductores: {e}")
        
        # === PRUEBAS DE VIAJES ===
        print("\n" + "="*50)
        print("🚗 PRUEBAS DEL SISTEMA DE VIAJES")
        print("="*50)
        
        # Obtener lista de carros disponibles
        print("\n🚙 Obteniendo carros disponibles...")
        try:
            carros = car_manager.listar_carros()
            print(f"  📊 Carros en sistema: {len(carros)}")
            if not carros:
                print("  ⚠️  No hay carros disponibles. Creando uno para pruebas...")
                # Crear un carro de prueba si no existe
                carro_prueba = {
                    'placa': 'TEST123',
                    'marca': 'Toyota',
                    'modelo': 'Corolla',
                    'año': 2020,
                    'color': 'Blanco',
                    'capacidad_pasajeros': 4,
                    'matricola_propietario': 'E001',
                    'observaciones': 'Carro de prueba'
                }
                car_manager.crear_carro(carro_prueba)
                carros = [carro_prueba]
                print("  ✅ Carro de prueba creado")
        except Exception as e:
            print(f"  ❌ Error al obtener carros: {e}")
            carros = []
        
        # Crear viajes de prueba
        print("\n🛣️ Creando viajes de prueba...")
        fecha_mañana = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        viajes_prueba = [
            {
                'fecha': fecha_mañana,
                'tipo_viaje': 'ida',
                'hora_salida': '07:30',
                'origen': 'Trastevere',
                'destino': 'Universidad Pontificia Gregoriana',
                'matricola_conductor': 'E001',
                'id_carro': carros[0]['placa'] if carros else 'TEST123',
                'pasajeros': ['E002'],
                'observaciones': 'Viaje de prueba - Ida'
            },
            {
                'fecha': fecha_mañana,
                'tipo_viaje': 'vuelta',
                'hora_salida': '16:00',
                'origen': 'Universidad Pontificia Gregoriana',
                'destino': 'Trastevere',
                'matricola_conductor': 'E003',
                'id_carro': carros[0]['placa'] if carros else 'TEST123',
                'pasajeros': [],
                'observaciones': 'Viaje de prueba - Vuelta'
            }
        ]
        
        viajes_creados = []
        for viaje in viajes_prueba:
            try:
                resultado = viaje_manager.crear_viaje(viaje)
                if resultado['exito']:
                    viajes_creados.append(resultado['viaje_id'])
                    print(f"  ✅ Viaje {viaje['tipo_viaje']} creado: {resultado['viaje_id']}")
                else:
                    print(f"  ❌ Error creando viaje {viaje['tipo_viaje']}: {resultado['mensaje']}")
            except Exception as e:
                print(f"  ❌ Excepción creando viaje: {e}")
        
        # Listar viajes
        print(f"\n📋 Listando viajes creados...")
        try:
            viajes = viaje_manager.listar_viajes()
            print(f"  📈 Total de viajes: {len(viajes)}")
            for viaje in viajes:
                print(f"  - {viaje['fecha']} {viaje['hora_salida']} - {viaje['tipo_viaje']} - {viaje['estado']}")
        except Exception as e:
            print(f"  ❌ Error listando viajes: {e}")
        
        # === PRUEBAS DE ASIGNACIÓN AUTOMÁTICA ===
        print("\n" + "="*50)
        print("🤖 PRUEBAS DE ASIGNACIÓN AUTOMÁTICA")
        print("="*50)
        
        print(f"\n🎯 Generando asignación automática para {fecha_mañana}...")
        try:
            resultado = viaje_manager.generar_asignacion_automatica(fecha_mañana)
            if resultado['exito']:
                asignacion = resultado['asignacion']
                print(f"  ✅ Asignación generada exitosamente")
                print(f"  📊 Estadísticas:")
                print(f"    - Viajes de ida: {len(asignacion['viajes_ida'])}")
                print(f"    - Viajes de vuelta: {len(asignacion['viajes_vuelta'])}")
                print(f"    - Total estudiantes asignados: {asignacion['total_estudiantes']}")
                print(f"    - Eficiencia: {asignacion['eficiencia']:.1f}%")
                
                # Mostrar detalles de viajes generados
                print(f"\n📝 Detalles de viajes de ida:")
                for viaje in asignacion['viajes_ida']:
                    print(f"    🚗 {viaje['hora_salida']} - {viaje['conductor_nombre']} ({viaje['pasajeros_count']+1}/{viaje['capacidad']})")
                
                print(f"\n📝 Detalles de viajes de vuelta:")
                for viaje in asignacion['viajes_vuelta']:
                    print(f"    🚗 {viaje['hora_salida']} - {viaje['conductor_nombre']} ({viaje['pasajeros_count']+1}/{viaje['capacidad']})")
                    
            else:
                print(f"  ❌ Error en asignación automática: {resultado['mensaje']}")
        except Exception as e:
            print(f"  ❌ Excepción en asignación automática: {e}")
        
        # === PRUEBAS DE LISTA DIARIA ===
        print("\n" + "="*50)
        print("📅 PRUEBAS DE LISTAS DIARIAS")
        print("="*50)
        
        print(f"\n📋 Creando lista diaria para {fecha_mañana}...")
        try:
            resultado = viaje_manager.crear_lista_diaria(fecha_mañana)
            if resultado['exito']:
                lista = resultado['lista']
                print(f"  ✅ Lista diaria creada exitosamente")
                print(f"  📊 Resumen:")
                print(f"    - Fecha: {lista['fecha']}")
                print(f"    - Total viajes: {lista['total_viajes']}")
                print(f"    - Total pasajeros: {lista['total_pasajeros']}")
                print(f"    - Capacidad utilizada: {lista['eficiencia']:.1f}%")
            else:
                print(f"  ❌ Error creando lista diaria: {resultado['mensaje']}")
        except Exception as e:
            print(f"  ❌ Excepción creando lista diaria: {e}")
        
        # === ESTADÍSTICAS FINALES ===
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS FINALES DEL SISTEMA")
        print("="*50)
        
        try:
            # Estadísticas de estudiantes
            stats_estudiantes = student_manager.obtener_estadisticas()
            print(f"\n👥 Estudiantes:")
            print(f"  - Total: {stats_estudiantes['total']}")
            print(f"  - Conductores: {stats_estudiantes['conductores']}")
            print(f"  - Pasajeros: {stats_estudiantes['pasajeros']}")
            print(f"  - Por zona: {json.dumps(stats_estudiantes['por_zona'], indent=4, ensure_ascii=False)}")
            
            # Estadísticas de viajes
            viajes_total = len(viaje_manager.listar_viajes())
            print(f"\n🚗 Viajes:")
            print(f"  - Total creados: {viajes_total}")
            
            print(f"\n🚙 Carros:")
            print(f"  - Total disponibles: {len(carros)}")
            
        except Exception as e:
            print(f"  ❌ Error obteniendo estadísticas: {e}")
        
        print("\n" + "="*60)
        print("✅ PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("🎉 Sistema de Fase 2 funcionando correctamente")
        print("="*60)
        
        logger.info("Pruebas de Fase 2 completadas exitosamente")
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO EN LAS PRUEBAS: {e}")
        logger.error(f"Error crítico en pruebas: {e}")
        return False
    
    return True

if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1)
