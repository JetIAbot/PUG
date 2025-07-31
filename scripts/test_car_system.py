"""
Script de prueba para el sistema de gestión de carros
Prueba todas las funcionalidades CRUD del CarManager
"""

import sys
import os
from datetime import datetime, date

# Agregar el directorio raíz al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.car_manager import CarManager
from core.models import TipoCarro, TipoCombustible, EstadoCarro, TipoLicencia

def test_crear_carro():
    """Probar creación de carro"""
    print("\n=== PRUEBA 1: CREAR CARRO ===")
    
    car_manager = CarManager()
    
    # Datos de prueba
    datos_carro = {
        'marca': 'Toyota',
        'modelo': 'Hiace',
        'año': '2020',
        'placa': 'ABC123',
        'tipo_carro': TipoCarro.FURGONETA.value,
        'tipo_combustible': TipoCombustible.DIESEL.value,
        'capacidad_pasajeros': '8',
        'observaciones': 'Carro de prueba para el sistema'
    }
    
    resultado = car_manager.crear_carro(datos_carro)
    
    if resultado['success']:
        print(f"✅ Carro creado exitosamente: {resultado['id_carro']}")
        print(f"📝 Mensaje: {resultado['message']}")
        return resultado['id_carro']
    else:
        print(f"❌ Error creando carro: {resultado['message']}")
        if 'errors' in resultado:
            for error in resultado['errors']:
                print(f"   - {error}")
        return None

def test_obtener_carro(id_carro):
    """Probar obtención de carro"""
    print(f"\n=== PRUEBA 2: OBTENER CARRO {id_carro} ===")
    
    car_manager = CarManager()
    carro = car_manager.obtener_carro(id_carro)
    
    if carro:
        print(f"✅ Carro encontrado:")
        print(f"   📋 ID: {carro.id_carro}")
        print(f"   🚗 Marca/Modelo: {carro.marca} {carro.modelo}")
        print(f"   📅 Año: {carro.año}")
        print(f"   🏷️ Placa: {carro.placa}")
        print(f"   🔧 Tipo: {carro.tipo_carro.value}")
        print(f"   ⛽ Combustible: {carro.tipo_combustible.value}")
        print(f"   👥 Capacidad: {carro.capacidad_pasajeros} pasajeros")
        print(f"   📊 Estado: {carro.estado.value}")
        return True
    else:
        print(f"❌ Carro no encontrado")
        return False

def test_listar_carros():
    """Probar listado de carros"""
    print("\n=== PRUEBA 3: LISTAR TODOS LOS CARROS ===")
    
    car_manager = CarManager()
    carros = car_manager.obtener_todos_carros()
    
    print(f"📊 Total de carros encontrados: {len(carros)}")
    
    for i, carro in enumerate(carros, 1):
        print(f"{i}. {carro.marca} {carro.modelo} ({carro.placa}) - {carro.estado.value}")
    
    return len(carros) > 0

def test_filtrar_carros():
    """Probar filtros de carros"""
    print("\n=== PRUEBA 4: FILTRAR CARROS DISPONIBLES ===")
    
    car_manager = CarManager()
    
    # Filtrar por estado
    filtros = {'estado': EstadoCarro.DISPONIBLE.value}
    carros_disponibles = car_manager.obtener_todos_carros(filtros)
    
    print(f"🟢 Carros disponibles: {len(carros_disponibles)}")
    
    # Filtrar carros compatibles con licencia B
    licencias = [TipoLicencia.B]
    carros_licencia_b = car_manager.obtener_carros_disponibles(licencias)
    
    print(f"🪪 Carros para licencia B: {len(carros_licencia_b)}")
    
    return True

def test_actualizar_carro(id_carro):
    """Probar actualización de carro"""
    print(f"\n=== PRUEBA 5: ACTUALIZAR CARRO {id_carro} ===")
    
    car_manager = CarManager()
    
    datos_actualizacion = {
        'observaciones': f'Carro actualizado el {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        'estado': EstadoCarro.EN_USO.value
    }
    
    resultado = car_manager.actualizar_carro(id_carro, datos_actualizacion)
    
    if resultado['success']:
        print(f"✅ Carro actualizado exitosamente")
        print(f"📝 Mensaje: {resultado['message']}")
        return True
    else:
        print(f"❌ Error actualizando carro: {resultado['message']}")
        return False

def test_estadisticas():
    """Probar estadísticas del sistema"""
    print("\n=== PRUEBA 6: ESTADÍSTICAS DEL SISTEMA ===")
    
    car_manager = CarManager()
    estadisticas = car_manager.obtener_estadisticas()
    
    if estadisticas:
        print(f"📊 Estadísticas del parque vehicular:")
        print(f"   🚗 Total carros: {estadisticas.get('total_carros', 0)}")
        print(f"   👥 Capacidad total: {estadisticas.get('capacidad_total', 0)} pasajeros")
        print(f"   📈 Capacidad promedio: {estadisticas.get('capacidad_promedio', 0)} pasajeros/carro")
        
        print(f"\n📋 Por estado:")
        for estado, cantidad in estadisticas.get('por_estado', {}).items():
            print(f"   - {estado}: {cantidad}")
            
        print(f"\n🔧 Por tipo:")
        for tipo, cantidad in estadisticas.get('por_tipo', {}).items():
            print(f"   - {tipo}: {cantidad}")
            
        print(f"\n⛽ Por combustible:")
        for combustible, cantidad in estadisticas.get('por_combustible', {}).items():
            print(f"   - {combustible}: {cantidad}")
        
        return True
    else:
        print("❌ Error obteniendo estadísticas")
        return False

def test_validaciones():
    """Probar validaciones del sistema"""
    print("\n=== PRUEBA 7: VALIDACIONES ===")
    
    car_manager = CarManager()
    
    # Datos inválidos
    datos_invalidos = {
        'marca': '',  # Vacío
        'modelo': 'Test',
        'año': '1800',  # Año inválido
        'placa': '',  # Vacío
        'tipo_carro': 'inexistente',  # Tipo inválido
        'tipo_combustible': TipoCombustible.GASOLINA.value,
        'capacidad_pasajeros': '0',  # Capacidad inválida
    }
    
    resultado = car_manager.crear_carro(datos_invalidos)
    
    if not resultado['success']:
        print(f"✅ Validaciones funcionando correctamente")
        print(f"📝 Errores detectados:")
        for error in resultado.get('errors', []):
            print(f"   - {error}")
        return True
    else:
        print(f"❌ Validaciones no funcionan - se creó carro con datos inválidos")
        return False

def test_eliminar_carro(id_carro):
    """Probar eliminación de carro (solo si se confirma)"""
    print(f"\n=== PRUEBA 8: ELIMINAR CARRO {id_carro} ===")
    
    respuesta = input("¿Deseas eliminar el carro de prueba? (s/N): ")
    if respuesta.lower() != 's':
        print("⏭️ Prueba de eliminación omitida")
        return True
    
    car_manager = CarManager()
    resultado = car_manager.eliminar_carro(id_carro)
    
    if resultado['success']:
        print(f"✅ Carro eliminado exitosamente")
        print(f"📝 Mensaje: {resultado['message']}")
        return True
    else:
        print(f"❌ Error eliminando carro: {resultado['message']}")
        return False

def main():
    """Función principal del test"""
    print("🚗 INICIANDO PRUEBAS DEL SISTEMA DE GESTIÓN DE CARROS")
    print("=" * 60)
    
    try:
        # Ejecutar pruebas en secuencia
        id_carro = test_crear_carro()
        
        if id_carro:
            test_obtener_carro(id_carro)
            test_listar_carros()
            test_filtrar_carros()
            test_actualizar_carro(id_carro)
            test_estadisticas()
            test_validaciones()
            test_eliminar_carro(id_carro)
        else:
            print("❌ No se pudo crear el carro de prueba, abortando tests")
            return
        
        print("\n" + "=" * 60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
