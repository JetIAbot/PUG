"""
FirebaseManager - Gestor de Firebase para PUG
Manejo centralizado de operaciones con Firebase Firestore
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

class FirebaseManager:
    """Gestor principal de Firebase Firestore"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Inicializar el gestor de Firebase
        
        Args:
            credentials_path: Ruta al archivo de credenciales JSON
        """
        self.credentials_path = credentials_path or os.getenv(
            'FIREBASE_CREDENTIALS_PATH', 
            'credenciales.json'
        )
        self.db = None
        self.logger = logging.getLogger('firebase_manager')
        self._initialize_firebase()
    
    def _initialize_firebase(self) -> bool:
        """
        Inicializar conexión con Firebase
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            # Verificar si Firebase ya está inicializado
            if not firebase_admin._apps:
                if not os.path.exists(self.credentials_path):
                    self.logger.error(f"Archivo de credenciales no encontrado: {self.credentials_path}")
                    return False
                
                # Inicializar Firebase
                cred = credentials.Certificate(self.credentials_path)
                firebase_admin.initialize_app(cred)
                self.logger.info("Firebase inicializado exitosamente")
            
            # Obtener cliente de Firestore
            self.db = firestore.client()
            return True
            
        except Exception as e:
            self.logger.error(f"Error inicializando Firebase: {e}")
            return False
    
    def get_client(self) -> Optional[firestore.client]:
        """
        Obtener cliente de Firestore
        
        Returns:
            firestore.client: Cliente de Firestore o None si hay error
        """
        if not self.db:
            self._initialize_firebase()
        return self.db
    
    def test_connection(self) -> bool:
        """
        Probar conexión a Firebase
        
        Returns:
            bool: True si la conexión es exitosa
        """
        try:
            if not self.db:
                return False
            
            # Intentar una operación simple
            collections = list(self.db.collections())
            self.logger.info(f"Conexión Firebase exitosa - {len(collections)} colecciones encontradas")
            return True
            
        except Exception as e:
            self.logger.error(f"Error probando conexión Firebase: {e}")
            return False
    
    def guardar_estudiante(self, matricola: str, datos_estudiante: dict) -> dict:
        """
        Guardar datos completos del estudiante en Firebase
        
        Args:
            matricola: Número de matrícula del estudiante
            datos_estudiante: Diccionario con todos los datos del estudiante
            
        Returns:
            dict: Resultado de la operación con success, message y timestamp
        """
        if not self.db:
            return {
                'success': False,
                'message': 'Error de conexión a Firebase',
                'error': 'Cliente de Firebase no disponible'
            }
        
        try:
            self.logger.info(f"Guardando datos para matrícula: {matricola[:2]}****")
            
            # Preparar documento principal del estudiante
            documento_principal = self._preparar_documento_principal(datos_estudiante, matricola)
            
            # Guardar documento principal
            doc_ref = self.db.collection('estudiantes').document(matricola)
            doc_ref.set(documento_principal, merge=True)
            self.logger.info(f"Documento principal guardado para {matricola}")
            
            # Guardar horario en subcolección
            if 'horario' in datos_estudiante and datos_estudiante['horario']:
                self._guardar_horario_estudiante(doc_ref, datos_estudiante['horario'])
            
            # Guardar materias en subcolección
            if 'materias' in datos_estudiante and datos_estudiante['materias']:
                self._guardar_materias_estudiante(doc_ref, datos_estudiante['materias'])
            
            # Guardar calificaciones si existen
            if 'calificaciones' in datos_estudiante and datos_estudiante['calificaciones']:
                self._guardar_calificaciones_estudiante(doc_ref, datos_estudiante['calificaciones'])
            
            return {
                'success': True,
                'message': f'Datos guardados exitosamente para {matricola}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error guardando estudiante {matricola}: {e}")
            return {
                'success': False,
                'message': f'Error guardando datos: {str(e)}',
                'error': str(e)
            }
    
    def _preparar_documento_principal(self, datos_estudiante: dict, matricola: str) -> dict:
        """
        Preparar documento principal del estudiante
        
        Args:
            datos_estudiante: Datos del estudiante
            matricola: Número de matrícula
            
        Returns:
            dict: Documento preparado para Firebase
        """
        perfil = datos_estudiante.get('perfil', {})
        
        return {
            'nome': perfil.get('nome', ''),
            'cognome': perfil.get('cognome', ''),
            'matricola': matricola,
            'email': perfil.get('email', f'{matricola}@unigre.it'),
            'telefono': perfil.get('telefono', 'No disponible'),
            'ultima_actualizacion': firestore.SERVER_TIMESTAMP,
            'estado_horarios': datos_estudiante.get('estado_horarios', 'no_disponible'),
            'fecha_extraccion': datetime.now().isoformat(),
            'version': '2.0'  # Versión de estructura de datos
        }
    
    def _guardar_horario_estudiante(self, doc_ref: firestore.DocumentReference, horario: List[dict]):
        """
        Guardar horario del estudiante en subcolección
        
        Args:
            doc_ref: Referencia al documento del estudiante
            horario: Lista de clases del horario
        """
        try:
            # Limpiar horario anterior
            horario_ref = doc_ref.collection('horario')
            self._clear_subcollection(horario_ref)
            
            # Guardar nuevo horario
            for i, clase in enumerate(horario):
                clase_doc = {
                    'materia': clase.get('materia', ''),
                    'profesor': clase.get('profesor', ''),
                    'dia': clase.get('dia', ''),
                    'bloque': clase.get('bloque', clase.get('hora', '')),
                    'aula': clase.get('aula', ''),
                    'info_clase': clase.get('info_clase', clase.get('materia', '')),
                    'orden': i + 1,
                    'timestamp': firestore.SERVER_TIMESTAMP
                }
                horario_ref.document(f'clase_{i+1:02d}').set(clase_doc)
            
            self.logger.info(f"Guardadas {len(horario)} clases en horario")
            
        except Exception as e:
            self.logger.error(f"Error guardando horario: {e}")
            raise
    
    def _guardar_materias_estudiante(self, doc_ref: firestore.DocumentReference, materias: List[dict]):
        """
        Guardar materias del estudiante en subcolección
        
        Args:
            doc_ref: Referencia al documento del estudiante
            materias: Lista de materias
        """
        try:
            materias_ref = doc_ref.collection('materias')
            self._clear_subcollection(materias_ref)
            
            for i, materia in enumerate(materias):
                materia_doc = {
                    'nombre': materia.get('name', materia.get('nombre', '')),
                    'codigo': materia.get('code', materia.get('codigo', '')),
                    'creditos': materia.get('credits', materia.get('creditos', '')),
                    'estado': materia.get('status', materia.get('estado', '')),
                    'semestre': materia.get('semester', materia.get('semestre', '')),
                    'ano': materia.get('year', materia.get('ano', '')),
                    'orden': i + 1,
                    'timestamp': firestore.SERVER_TIMESTAMP
                }
                materias_ref.document(f'materia_{i+1:02d}').set(materia_doc)
            
            self.logger.info(f"Guardadas {len(materias)} materias")
            
        except Exception as e:
            self.logger.error(f"Error guardando materias: {e}")
            raise
    
    def _guardar_calificaciones_estudiante(self, doc_ref: firestore.DocumentReference, calificaciones: List[dict]):
        """
        Guardar calificaciones del estudiante en subcolección
        
        Args:
            doc_ref: Referencia al documento del estudiante
            calificaciones: Lista de calificaciones
        """
        try:
            calificaciones_ref = doc_ref.collection('calificaciones')
            self._clear_subcollection(calificaciones_ref)
            
            for i, calificacion in enumerate(calificaciones):
                calificacion_doc = {
                    'materia': calificacion.get('materia', ''),
                    'nota': calificacion.get('nota', ''),
                    'fecha': calificacion.get('fecha', ''),
                    'tipo': calificacion.get('tipo', ''),
                    'orden': i + 1,
                    'timestamp': firestore.SERVER_TIMESTAMP
                }
                calificaciones_ref.document(f'nota_{i+1:02d}').set(calificacion_doc)
            
            self.logger.info(f"Guardadas {len(calificaciones)} calificaciones")
            
        except Exception as e:
            self.logger.error(f"Error guardando calificaciones: {e}")
            raise
    
    def _clear_subcollection(self, collection_ref: firestore.CollectionReference):
        """
        Limpiar una subcolección
        
        Args:
            collection_ref: Referencia a la colección a limpiar
        """
        try:
            docs = collection_ref.stream()
            for doc in docs:
                doc.reference.delete()
        except Exception as e:
            self.logger.warning(f"Error limpiando subcolección: {e}")
    
    def obtener_estudiante(self, matricola: str) -> Optional[dict]:
        """
        Obtener datos completos de un estudiante
        
        Args:
            matricola: Número de matrícula
            
        Returns:
            dict: Datos del estudiante o None si no existe
        """
        if not self.db:
            return None
        
        try:
            doc_ref = self.db.collection('estudiantes').document(matricola)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            datos_estudiante = doc.to_dict()
            
            # Obtener horario
            horario_ref = doc_ref.collection('horario')
            horario_docs = horario_ref.order_by('orden').stream()
            datos_estudiante['horario'] = [doc.to_dict() for doc in horario_docs]
            
            # Obtener materias
            materias_ref = doc_ref.collection('materias')
            materias_docs = materias_ref.order_by('orden').stream()
            datos_estudiante['materias'] = [doc.to_dict() for doc in materias_docs]
            
            # Obtener calificaciones
            calificaciones_ref = doc_ref.collection('calificaciones')
            calificaciones_docs = calificaciones_ref.order_by('orden').stream()
            datos_estudiante['calificaciones'] = [doc.to_dict() for doc in calificaciones_docs]
            
            return datos_estudiante
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estudiante {matricola}: {e}")
            return None
    
    def obtener_todos_estudiantes(self) -> dict:
        """
        Obtener datos de todos los estudiantes
        
        Returns:
            dict: Diccionario con datos de todos los estudiantes
        """
        if not self.db:
            return {}
        
        try:
            self.logger.info("Obteniendo datos de todos los estudiantes")
            estudiantes = {}
            
            estudiantes_ref = self.db.collection('estudiantes')
            for doc in estudiantes_ref.stream():
                matricola = doc.id
                datos_perfil = doc.to_dict()
                
                # Verificar datos básicos
                if not datos_perfil or 'nome' not in datos_perfil:
                    self.logger.warning(f"Estudiante {matricola} sin datos básicos - omitido")
                    continue
                
                estudiantes[matricola] = {
                    "nome": datos_perfil.get('nome', ''),
                    "cognome": datos_perfil.get('cognome', ''),
                    "email": datos_perfil.get('email', ''),
                    "ultima_actualizacion": datos_perfil.get('ultima_actualizacion'),
                    "estado_horarios": datos_perfil.get('estado_horarios', 'no_disponible'),
                    "horario": []
                }
                
                # Obtener horario
                horario_ref = doc.reference.collection('horario')
                for clase_doc in horario_ref.order_by('orden').stream():
                    estudiantes[matricola]['horario'].append(clase_doc.to_dict())
            
            self.logger.info(f"Obtenidos datos de {len(estudiantes)} estudiantes")
            return estudiantes
            
        except Exception as e:
            self.logger.error(f"Error obteniendo todos los estudiantes: {e}")
            return {}
    
    def eliminar_estudiante(self, matricola: str) -> bool:
        """
        Eliminar estudiante y todos sus datos asociados
        
        Args:
            matricola: Número de matrícula
            
        Returns:
            bool: True si la eliminación fue exitosa
        """
        if not self.db:
            return False
        
        try:
            doc_ref = self.db.collection('estudiantes').document(matricola)
            
            # Eliminar subcolecciones
            for subcollection_name in ['horario', 'materias', 'calificaciones']:
                subcollection_ref = doc_ref.collection(subcollection_name)
                self._clear_subcollection(subcollection_ref)
            
            # Eliminar documento principal
            doc_ref.delete()
            
            self.logger.info(f"Estudiante {matricola} eliminado exitosamente")
            return True
            
        except Exception as e:
            self.logger.error(f"Error eliminando estudiante {matricola}: {e}")
            return False
    
    def get_statistics(self) -> dict:
        """
        Obtener estadísticas del sistema
        
        Returns:
            dict: Estadísticas del sistema
        """
        try:
            if not self.db:
                return {}
            
            # Contar estudiantes
            estudiantes_count = len(list(self.db.collection('estudiantes').stream()))
            
            # Contar estudiantes con horarios
            estudiantes_con_horarios = 0
            for doc in self.db.collection('estudiantes').stream():
                horario_ref = doc.reference.collection('horario')
                if len(list(horario_ref.stream())) > 0:
                    estudiantes_con_horarios += 1
            
            return {
                'total_estudiantes': estudiantes_count,
                'estudiantes_con_horarios': estudiantes_con_horarios,
                'ultima_consulta': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo estadísticas: {e}")
            return {}

# Funciones de compatibilidad con el sistema anterior
def inicializar_firebase():
    """Función de compatibilidad"""
    firebase_manager = FirebaseManager()
    return firebase_manager.get_client()

def guardar_en_firebase(db, matricola: str, datos_estudiante: dict) -> dict:
    """Función de compatibilidad"""
    firebase_manager = FirebaseManager()
    return firebase_manager.guardar_estudiante(matricola, datos_estudiante)
