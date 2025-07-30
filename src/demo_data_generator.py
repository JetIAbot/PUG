"""
Generador de datos de demostración para cuando los horarios universitarios no están disponibles
"""

import random
from datetime import datetime, timedelta
import logging

class DemoDataGenerator:
    """Generador de datos de demostración realistas para la aplicación"""
    
    def __init__(self):
        self.logger = logging.getLogger('demo_generator')
        
        # Datos base para generar contenido realista
        self.materias_comunes = [
            "Análisis Matemático I",
            "Álgebra Lineal",
            "Física General I",
            "Programación I",
            "Química General",
            "Geometría Analítica",
            "Inglés Técnico",
            "Metodología de la Investigación",
            "Fundamentos de Ingeniería",
            "Cálculo Diferencial e Integral"
        ]
        
        self.profesores_ejemplo = [
            "Prof. García López",
            "Prof. Martín Rodríguez",
            "Prof. Ana Fernández",
            "Prof. Carlos Mendoza",
            "Prof. María González",
            "Prof. Roberto Silva",
            "Prof. Elena Morales",
            "Prof. José Herrera",
            "Prof. Laura Jiménez",
            "Prof. Alberto Ruiz"
        ]
        
        self.aulas_ejemplo = [
            "Aula Magna A",
            "Aula 201",
            "Aula 305",
            "Lab. Informática 1",
            "Lab. Física",
            "Aula 102",
            "Aula 408",
            "Lab. Química",
            "Aula 301",
            "Salón 205"
        ]
        
        self.dias_semana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì"]
        self.bloques_horarios = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
    
    def generar_perfil_estudiante(self, matricola: str) -> dict:
        """Generar perfil de estudiante de demostración"""
        nombres = ["Alessandro", "Marco", "Giulia", "Francesca", "Lorenzo", "Martina", "Luca", "Sofia"]
        apellidos = ["Rossi", "Ferrari", "Russo", "Bianchi", "Romano", "Gallo", "Conti", "Bruno"]
        
        nombre = random.choice(nombres)
        apellido = random.choice(apellidos)
        
        return {
            'nome': nombre,
            'cognome': apellido,
            'matricola': matricola,
            'email': f'{nombre.lower()}.{apellido.lower()}@unigre.it',
            'telefono': f'+39 {random.randint(300, 399)} {random.randint(1000000, 9999999)}'
        }
    
    def generar_horario_demo(self, num_materias: int = None) -> list:
        """Generar horario de demostración realista"""
        if num_materias is None:
            num_materias = random.randint(4, 7)  # Entre 4 y 7 materias
        
        horario = []
        materias_seleccionadas = random.sample(self.materias_comunes, min(num_materias, len(self.materias_comunes)))
        
        for materia in materias_seleccionadas:
            # Cada materia puede tener 1-3 clases por semana
            num_clases = random.randint(1, 3)
            
            dias_usados = random.sample(self.dias_semana, num_clases)
            profesor = random.choice(self.profesores_ejemplo)
            
            for dia in dias_usados:
                aula = random.choice(self.aulas_ejemplo)
                bloque = random.choice(self.bloques_horarios)
                
                # Verificar que no haya conflictos (mismo día y bloque)
                conflicto = any(
                    clase['dia'] == dia and clase['bloque'] == bloque 
                    for clase in horario
                )
                
                if not conflicto:
                    horario.append({
                        'materia': f"{materia} (DEMO)",
                        'profesor': profesor,
                        'dia': dia,
                        'bloque': bloque,
                        'aula': aula
                    })
        
        # Ordenar por día y bloque para mejor presentación
        orden_dias = {dia: i for i, dia in enumerate(self.dias_semana)}
        orden_bloques = {bloque: i for i, bloque in enumerate(self.bloques_horarios)}
        
        horario.sort(key=lambda x: (orden_dias[x['dia']], orden_bloques[x['bloque']]))
        
        self.logger.info(f"Generado horario demo con {len(horario)} clases")
        return horario
    
    def generar_materias_demo(self, num_materias: int = None) -> list:
        """Generar lista de materias de demostración"""
        if num_materias is None:
            num_materias = random.randint(5, 8)
        
        materias_seleccionadas = random.sample(self.materias_comunes, min(num_materias, len(self.materias_comunes)))
        materias = []
        
        for i, materia in enumerate(materias_seleccionadas):
            materias.append({
                'name': f"{materia} (DEMO - Horarios no publicados)",
                'code': f"DEMO{str(i+1).zfill(3)}",
                'credits': str(random.choice([6, 9, 12])),  # Créditos típicos
                'status': 'demo',
                'semester': random.choice(['I', 'II']),
                'year': '2024/2025'
            })
        
        return materias
    
    def generar_datos_completos(self, matricola: str) -> dict:
        """Generar conjunto completo de datos de demostración"""
        return {
            'perfil': self.generar_perfil_estudiante(matricola),
            'horario': self.generar_horario_demo(),
            'materias': self.generar_materias_demo(),
            'calificaciones': [],  # Por ahora vacío
            'estado_horarios': 'demo_realista',
            'timestamp': datetime.now().isoformat(),
            'nota_demo': 'Datos generados automáticamente para demostración. Los horarios reales no han sido publicados aún por la universidad.'
        }
    
    def generar_multiples_estudiantes(self, num_estudiantes: int = 5) -> dict:
        """Generar múltiples estudiantes para pruebas de matchmaking"""
        estudiantes = {}
        
        for i in range(num_estudiantes):
            matricola_demo = f"DEMO{str(i+1).zfill(4)}"
            estudiantes[matricola_demo] = self.generar_datos_completos(matricola_demo)
        
        self.logger.info(f"Generados {num_estudiantes} estudiantes de demostración")
        return estudiantes

def crear_datos_demo_firebase(db, num_estudiantes: int = 3):
    """Crear datos de demostración en Firebase para pruebas de matchmaking"""
    generator = DemoDataGenerator()
    logger = logging.getLogger('demo_firebase')
    
    try:
        estudiantes_demo = generator.generar_multiples_estudiantes(num_estudiantes)
        
        for matricola, datos in estudiantes_demo.items():
            # Crear documento del estudiante
            doc_ref = db.collection('estudiantes').document(matricola)
            doc_ref.set(datos['perfil'])
            logger.info(f"Creado perfil demo para {matricola}")
            
            # Crear documento de horario
            if datos['horario']:
                horario_ref = db.collection('estudiantes').document(matricola).collection('horario')
                for i, clase in enumerate(datos['horario']):
                    horario_ref.document(f"clase_{i+1}").set(clase)
                logger.info(f"Creado horario demo para {matricola} con {len(datos['horario'])} clases")
        
        logger.info(f"✅ Datos de demostración creados exitosamente en Firebase")
        return True
        
    except Exception as e:
        logger.error(f"Error creando datos demo en Firebase: {e}")
        return False

# Función de utilidad para generar datos rápidamente
def obtener_datos_demo_rapido(matricola: str) -> dict:
    """Función rápida para obtener datos de demostración"""
    generator = DemoDataGenerator()
    return generator.generar_datos_completos(matricola)

if __name__ == "__main__":
    # Prueba del generador
    generator = DemoDataGenerator()
    datos_test = generator.generar_datos_completos("TEST123")
    
    print("=== DATOS DE DEMOSTRACIÓN GENERADOS ===")
    print(f"Perfil: {datos_test['perfil']}")
    print(f"Horario: {len(datos_test['horario'])} clases")
    print(f"Materias: {len(datos_test['materias'])} materias")
    print(f"Estado: {datos_test['estado_horarios']}")
