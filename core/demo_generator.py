"""
DemoGenerator - Generador de datos de demostración para PUG
Crea datos realistas cuando los horarios universitarios no están disponibles
"""

import random
from datetime import datetime, timedelta
import logging
from utils.constants import (
    DIAS_SEMANA, ORDEN_BLOQUES, DEMO_NAMES, DEMO_MATERIAS, 
    DEMO_PROFESSORI, DEMO_AULAS
)

logger = logging.getLogger(__name__)

class DemoDataGenerator:
    """Generador de datos de demostración realistas"""
    
    def __init__(self):
        self.logger = logging.getLogger('demo_generator')
    
    def generar_horario_demo(self, num_materias: int = 5) -> list:
        """
        Generar horario de demostración realista
        
        Args:
            num_materias: Número de materias para generar
            
        Returns:
            list: Lista de clases generadas
        """
        self.logger.info(f"Generando horario demo con {num_materias} materias")
        
        horario_demo = []
        materias_usadas = random.sample(DEMO_MATERIAS, min(num_materias, len(DEMO_MATERIAS)))
        
        for i, materia in enumerate(materias_usadas):
            # Generar 1-2 clases por materia
            num_clases = random.randint(1, 2)
            
            for j in range(num_clases):
                # Evitar conflictos de horario
                intentos = 0
                while intentos < 10:  # Máximo 10 intentos por clase
                    dia = random.choice(DIAS_SEMANA[:5])  # Solo días laborables
                    bloque = random.choice(ORDEN_BLOQUES[:8])  # Bloques más comunes
                    
                    # Verificar conflicto
                    conflicto = any(
                        clase['dia'] == dia and clase['bloque'] == bloque 
                        for clase in horario_demo
                    )
                    
                    if not conflicto:
                        clase = {
                            'materia': materia,
                            'profesor': random.choice(DEMO_PROFESSORI),
                            'dia': dia,
                            'bloque': bloque,
                            'aula': random.choice(DEMO_AULAS),
                            'info_clase': f'{materia} - {random.choice(DEMO_PROFESSORI)}'
                        }
                        horario_demo.append(clase)
                        break
                    
                    intentos += 1
        
        # Ordenar por día y bloque
        horario_demo.sort(key=lambda x: (DIAS_SEMANA.index(x['dia']), ORDEN_BLOQUES.index(x['bloque'])))
        
        self.logger.info(f"Generado horario demo con {len(horario_demo)} clases")
        return horario_demo
    
    def generar_materias_demo(self, num_materias: int = 5) -> list:
        """
        Generar lista de materias de demostración
        
        Args:
            num_materias: Número de materias para generar
            
        Returns:
            list: Lista de materias generadas
        """
        materias_demo = []
        materias_seleccionadas = random.sample(DEMO_MATERIAS, min(num_materias, len(DEMO_MATERIAS)))
        
        for i, materia in enumerate(materias_seleccionadas):
            materia_data = {
                'name': materia,
                'code': f'MAT{100 + i:03d}',
                'credits': str(random.choice([6, 9, 12])),
                'status': random.choice(['En curso', 'Aprobada', 'Pendiente']),
                'semester': random.choice(['1', '2']),
                'year': '2024-2025'
            }
            materias_demo.append(materia_data)
        
        return materias_demo
    
    def generar_perfil_demo(self, matricola: str) -> dict:
        """
        Generar perfil de estudiante de demostración
        
        Args:
            matricola: Número de matrícula
            
        Returns:
            dict: Perfil generado
        """
        nombre = random.choice(DEMO_NAMES['nombres'])
        apellido = random.choice(DEMO_NAMES['apellidos'])
        
        return {
            'nome': nombre,
            'cognome': apellido,
            'matricola': matricola,
            'email': f'{matricola}@unigre.it',
            'telefono': f'+39 {random.randint(300, 399)} {random.randint(1000000, 9999999)}'
        }
    
    def generar_calificaciones_demo(self, materias: list) -> list:
        """
        Generar calificaciones de demostración
        
        Args:
            materias: Lista de materias para generar calificaciones
            
        Returns:
            list: Lista de calificaciones
        """
        calificaciones = []
        
        for materia in materias[:3]:  # Solo algunas materias tienen calificaciones
            if random.choice([True, False]):  # 50% probabilidad
                calificacion = {
                    'materia': materia.get('name', materia),
                    'nota': random.choice(['18', '20', '22', '24', '26', '28', '30', '30L']),
                    'fecha': (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                    'tipo': random.choice(['Examen', 'Proyecto', 'Práctica'])
                }
                calificaciones.append(calificacion)
        
        return calificaciones

def obtener_datos_demo_rapido(matricola: str) -> dict:
    """
    Función de conveniencia para obtener datos demo completos
    
    Args:
        matricola: Número de matrícula
        
    Returns:
        dict: Datos completos de demostración
    """
    generator = DemoDataGenerator()
    
    perfil = generator.generar_perfil_demo(matricola)
    horario = generator.generar_horario_demo()
    materias = generator.generar_materias_demo()
    calificaciones = generator.generar_calificaciones_demo(materias)
    
    return {
        'perfil': perfil,
        'horario': horario,
        'materias': materias,
        'calificaciones': calificaciones,
        'estado_horarios': 'ejemplo_demo',
        'fecha_generacion': datetime.now().isoformat()
    }