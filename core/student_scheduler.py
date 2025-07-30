"""
StudentScheduler - Sistema de Agrupación de Estudiantes por Horarios
Algoritmo principal para encontrar compatibilidades de horarios entre estudiantes
para viajes compartidos a la universidad.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from utils.constants import ORDEN_BLOQUES, BLOQUES_A_HORAS
from .firebase_manager import FirebaseManager
from .portal_extractor import PortalExtractor
from .demo_generator import DemoDataGenerator

logger = logging.getLogger(__name__)

class StudentScheduler:
    """
    Clase principal para gestionar la programación y agrupación de estudiantes
    """
    
    def __init__(self):
        """Inicializar el programador de estudiantes"""
        self.firebase = FirebaseManager()
        self.portal = PortalExtractor()
        self.demo_generator = DemoDataGenerator()
    
    def extraer_y_guardar_datos(self, matricola: str, password: str) -> dict:
        """
        Extraer datos del portal universitario y guardarlos en Firebase
        
        Args:
            matricola: Número de matrícula del estudiante
            password: Contraseña del portal
            
        Returns:
            dict: Resultado de la operación con success, message y data
        """
        logger.info(f"Iniciando extracción para matrícula: {matricola[:2]}****")
        
        try:
            # Extraer datos del portal
            resultado_portal = self.portal.extraer_datos_estudiante(matricola, password)
            
            if not resultado_portal['success']:
                logger.warning(f"Error en extracción del portal: {resultado_portal['message']}")
                return resultado_portal
            
            # Procesar y estructurar datos
            datos_procesados = self._procesar_datos_portal(resultado_portal['data'], matricola)
            
            # Guardar en Firebase
            resultado_guardado = self.firebase.guardar_estudiante(matricola, datos_procesados)
            
            if resultado_guardado['success']:
                logger.info(f"Datos guardados exitosamente para {matricola}")
                return {
                    'success': True,
                    'message': f'Datos extraídos y guardados exitosamente. {resultado_portal["message"]}',
                    'data': datos_procesados,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"Error guardando datos: {resultado_guardado['message']}")
                return resultado_guardado
                
        except Exception as e:
            logger.error(f"Error durante extracción y guardado: {e}")
            return {
                'success': False,
                'message': f'Error técnico: {str(e)}',
                'error': str(e)
            }
    
    def _procesar_datos_portal(self, raw_data: dict, matricola: str) -> dict:
        """
        Procesar datos brutos del portal al formato interno
        
        Args:
            raw_data: Datos brutos del portal
            matricola: Número de matrícula
            
        Returns:
            dict: Datos procesados en formato estándar
        """
        processed = {
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
            'estado_horarios': 'no_disponible'
        }
        
        # Procesar información del estudiante
        if 'student_info' in raw_data and raw_data['student_info']:
            student_info = raw_data['student_info']
            processed['perfil'].update({
                'nome': student_info.get('nome', 'Usuario'),
                'cognome': student_info.get('cognome', 'Universitario'),
                'email': student_info.get('email', f'{matricola}@unigre.it'),
                'telefono': student_info.get('telefono', 'No disponible')
            })
        
        # Procesar horario
        if 'schedule' in raw_data and raw_data['schedule']:
            processed['horario'] = self._convertir_horario_portal(raw_data['schedule'])
            processed['estado_horarios'] = 'disponible'
            logger.info(f"Horarios reales procesados: {len(processed['horario'])} clases")
        else:
            # Generar horario de ejemplo para demostración
            processed['horario'] = self.demo_generator.generar_horario_demo()
            processed['estado_horarios'] = 'ejemplo_demo'
            logger.warning("Horarios no disponibles - usando datos de ejemplo")
        
        # Procesar materias
        if 'courses' in raw_data and raw_data['courses']:
            processed['materias'] = raw_data['courses']
        else:
            processed['materias'] = self.demo_generator.generar_materias_demo()
        
        # Procesar calificaciones si existen
        if 'grades' in raw_data:
            processed['calificaciones'] = raw_data['grades']
        
        return processed
    
    def _convertir_horario_portal(self, schedule_data: list) -> list:
        """
        Convertir horario del portal al formato interno
        
        Args:
            schedule_data: Lista de clases del portal
            
        Returns:
            list: Horario en formato interno
        """
        horario_convertido = []
        
        for clase in schedule_data:
            clase_convertida = {
                'materia': clase.get('subject', ''),
                'profesor': clase.get('professor', ''),
                'dia': clase.get('day', ''),
                'bloque': clase.get('time_block', ''),
                'aula': clase.get('room', ''),
                'info_clase': f"{clase.get('subject', '')} - {clase.get('professor', '')}"
            }
            horario_convertido.append(clase_convertida)
        
        return horario_convertido
    
    def obtener_grupos_compatibles(self, matricola_especifica: Optional[str] = None) -> str:
        """
        Buscar grupos de estudiantes con horarios compatibles
        
        Args:
            matricola_especifica: Matrícula específica para incluir info adicional
            
        Returns:
            str: Informe formateado de grupos compatibles
        """
        logger.info("Iniciando búsqueda de grupos compatibles")
        
        try:
            # Obtener datos de estudiantes
            datos_estudiantes = self.firebase.obtener_todos_estudiantes()
            
            if not datos_estudiantes:
                return "No se encontraron datos de estudiantes en la base de datos."
            
            # Procesar horarios
            horarios_procesados = self._procesar_horarios_estudiantes(datos_estudiantes)
            
            # Encontrar coincidencias
            grupos_compatibles = self._encontrar_coincidencias_horarios(horarios_procesados)
            
            # Formatear resultado
            resultado = self._formatear_informe_grupos(grupos_compatibles)
            
            # Agregar información específica si se solicita
            if matricola_especifica and matricola_especifica in datos_estudiantes:
                resultado += self._agregar_info_estudiante_especifico(
                    matricola_especifica, datos_estudiantes[matricola_especifica]
                )
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error buscando grupos compatibles: {e}")
            return f"Error: No se pudieron procesar los datos de horarios. {str(e)}"
    
    def _procesar_horarios_estudiantes(self, datos_estudiantes: dict) -> dict:
        """
        Procesar horarios de estudiantes para obtener entrada/salida por día
        
        Args:
            datos_estudiantes: Diccionario con datos de todos los estudiantes
            
        Returns:
            dict: Horarios procesados por estudiante
        """
        logger.info("Procesando horarios de estudiantes...")
        horarios_procesados = {}
        
        for matricola, info in datos_estudiantes.items():
            # Verificar datos básicos
            if not info or 'nome' not in info:
                logger.warning(f"Estudiante {matricola} sin datos básicos - omitido")
                continue
            
            horario_diario = {}
            
            # Procesar clases del estudiante
            for clase in info.get('horario', []):
                dia = clase.get('dia')
                bloque = clase.get('bloque', clase.get('hora', ''))
                
                if not dia or not bloque:
                    continue
                
                # Verificar que el bloque sea válido
                if bloque not in ORDEN_BLOQUES:
                    logger.warning(f"Bloque '{bloque}' desconocido para {matricola}")
                    continue
                
                if dia not in horario_diario:
                    horario_diario[dia] = []
                horario_diario[dia].append(bloque)
            
            # Calcular entrada y salida por día
            horario_final = {}
            for dia, bloques in horario_diario.items():
                bloques_ordenados = sorted(bloques, key=lambda b: ORDEN_BLOQUES.index(b))
                if bloques_ordenados:
                    horario_final[dia] = {
                        "entrada": bloques_ordenados[0],
                        "salida": bloques_ordenados[-1]
                    }
            
            horarios_procesados[matricola] = {
                "nombre_completo": f"{info.get('nome', '')} {info.get('cognome', '')}".strip(),
                "horario_diario": horario_final
            }
        
        logger.info(f"Procesados horarios de {len(horarios_procesados)} estudiantes")
        return horarios_procesados
    
    def _encontrar_coincidencias_horarios(self, horarios_procesados: dict) -> dict:
        """
        Encontrar coincidencias de horarios para viajes compartidos
        
        Args:
            horarios_procesados: Horarios procesados de estudiantes
            
        Returns:
            dict: Grupos compatibles para ida y vuelta
        """
        logger.info("Buscando coincidencias de horarios...")
        
        indice_ida = {}
        indice_vuelta = {}
        
        # Construir índices de horarios
        for matricola, data in horarios_procesados.items():
            nombre = data['nombre_completo']
            
            for dia, horas in data['horario_diario'].items():
                # Índice para viajes de ida (entrada a universidad)
                clave_ida = f"{dia}_{horas['entrada']}"
                if clave_ida not in indice_ida:
                    indice_ida[clave_ida] = []
                indice_ida[clave_ida].append(nombre)
                
                # Índice para viajes de vuelta (salida de universidad)
                clave_vuelta = f"{dia}_{horas['salida']}"
                if clave_vuelta not in indice_vuelta:
                    indice_vuelta[clave_vuelta] = []
                indice_vuelta[clave_vuelta].append(nombre)
        
        # Filtrar solo grupos con más de una persona
        grupos_ida = {k: v for k, v in indice_ida.items() if len(v) > 1}
        grupos_vuelta = {k: v for k, v in indice_vuelta.items() if len(v) > 1}
        
        logger.info(f"Encontrados {len(grupos_ida)} grupos de ida y {len(grupos_vuelta)} de vuelta")
        
        return {"ida": grupos_ida, "vuelta": grupos_vuelta}
    
    def _formatear_informe_grupos(self, grupos_compatibles: dict) -> str:
        """
        Formatear informe de grupos compatibles
        
        Args:
            grupos_compatibles: Diccionario con grupos de ida y vuelta
            
        Returns:
            str: Informe formateado
        """
        output = [
            "=" * 60,
            "    GRUPOS DE VIAJE COMPATIBLES - PUG SYSTEM",
            "=" * 60
        ]
        
        # Viajes de ida
        output.append("\n🚌 VIAJES DE IDA (Llegar a la universidad)\n")
        if not grupos_compatibles['ida']:
            output.append("❌ No se encontraron coincidencias para viajes de ida.")
        else:
            for clave, personas in sorted(grupos_compatibles['ida'].items()):
                dia, bloque = clave.split('_')
                hora = BLOQUES_A_HORAS.get(bloque, bloque)
                output.append(f"📅 {dia} a las {hora}:")
                output.append(f"   👥 Grupo compatible: {', '.join(personas)}\n")
        
        # Viajes de vuelta
        output.append("\n🏠 VIAJES DE VUELTA (Salir de la universidad)\n")
        if not grupos_compatibles['vuelta']:
            output.append("❌ No se encontraron coincidencias para viajes de vuelta.")
        else:
            for clave, personas in sorted(grupos_compatibles['vuelta'].items()):
                dia, bloque = clave.split('_')
                hora = BLOQUES_A_HORAS.get(bloque, bloque)
                output.append(f"📅 {dia} a las {hora}:")
                output.append(f"   👥 Grupo compatible: {', '.join(personas)}\n")
        
        return "\n".join(output)
    
    def _agregar_info_estudiante_especifico(self, matricola: str, datos_estudiante: dict) -> str:
        """
        Agregar información específica de un estudiante al informe
        
        Args:
            matricola: Número de matrícula
            datos_estudiante: Datos del estudiante
            
        Returns:
            str: Información adicional formateada
        """
        info_adicional = [
            f"\n{'='*60}",
            f"📋 INFORMACIÓN ESPECÍFICA PARA {matricola}",
            f"{'='*60}",
            f"👤 Estudiante: {datos_estudiante.get('nome', 'N/A')} {datos_estudiante.get('cognome', 'N/A')}",
            f"📧 Email: {datos_estudiante.get('email', 'No disponible')}",
            f"📅 Última actualización: {datos_estudiante.get('ultima_actualizacion', 'No disponible')}",
            f"📚 Estado horarios: {datos_estudiante.get('estado_horarios', 'No disponible')}"
        ]
        
        return "\n".join(info_adicional)

# Funciones de compatibilidad para el sistema existente
def inicializar_firebase():
    """Función de compatibilidad - usar FirebaseManager"""
    firebase_manager = FirebaseManager()
    return firebase_manager.get_client()

def guardar_en_firebase(db, matricola: str, datos_estudiante: dict) -> dict:
    """Función de compatibilidad - usar FirebaseManager"""
    firebase_manager = FirebaseManager()
    return firebase_manager.guardar_estudiante(matricola, datos_estudiante)

def extraer_datos_portal_real(matricola: str, password: str) -> dict:
    """Función de compatibilidad - usar StudentScheduler"""
    scheduler = StudentScheduler()
    return scheduler.extraer_y_guardar_datos(matricola, password)

def realizar_matchmaking(db=None, matricola_especifica=None):
    """Función de compatibilidad - usar StudentScheduler"""
    scheduler = StudentScheduler()
    return scheduler.obtener_grupos_compatibles(matricola_especifica)

if __name__ == '__main__':
    # Ejecutar sistema de matchmaking
    scheduler = StudentScheduler()
    resultado = scheduler.obtener_grupos_compatibles()
    print(resultado)
