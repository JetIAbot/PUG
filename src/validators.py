import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Excepción personalizada para errores de validación"""
    pass

class DataValidator:
    """Clase para validar datos de entrada del usuario"""
    
    # Patrones de validación
    MATRICOLA_PATTERN = r'^[0-9]{6,8}$'
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    PHONE_PATTERN = r'^\+?[1-9]\d{1,14}$'
    
    @staticmethod
    def validate_matricola(matricola: str) -> Dict[str, any]:
        """
        Valida número de matrícula universitaria
        
        Args:
            matricola: Número de matrícula a validar
            
        Returns:
            Dict con resultado de validación
        """
        result = {'valid': False, 'errors': []}
        
        if not matricola:
            result['errors'].append('La matrícula es obligatoria')
            return result
            
        # Limpiar espacios
        matricola = matricola.strip()
        
        if not re.match(DataValidator.MATRICOLA_PATTERN, matricola):
            result['errors'].append('La matrícula debe tener entre 6 y 8 dígitos')
            return result
            
        result['valid'] = True
        result['cleaned_value'] = matricola
        return result
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, any]:
        """
        Valida fortaleza de contraseña
        
        Args:
            password: Contraseña a validar
            
        Returns:
            Dict con resultado y detalles de validación
        """
        result = {
            'valid': False,
            'errors': [],
            'strength_score': 0,
            'checks': {}
        }
        
        if not password:
            result['errors'].append('La contraseña es obligatoria')
            return result
        
        # Verificaciones de fortaleza
        checks = {
            'length': len(password) >= 8,
            'uppercase': bool(re.search(r'[A-Z]', password)),
            'lowercase': bool(re.search(r'[a-z]', password)),
            'numbers': bool(re.search(r'\d', password)),
            'special': bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        }
        
        result['checks'] = checks
        result['strength_score'] = sum(checks.values())
        
        # Validación mínima
        if not checks['length']:
            result['errors'].append('La contraseña debe tener al menos 8 caracteres')
        
        if result['strength_score'] < 3:
            result['errors'].append('La contraseña es demasiado débil')
        
        if not result['errors']:
            result['valid'] = True
            
        return result
    
    @staticmethod
    def validate_license_data(license_type: str, expiry_date: str) -> Dict[str, any]:
        """
        Valida datos de licencia de conducir
        
        Args:
            license_type: Tipo de licencia (A, B, C, etc.)
            expiry_date: Fecha de vencimiento (YYYY-MM-DD)
            
        Returns:
            Dict con resultado de validación
        """
        result = {'valid': False, 'errors': []}
        
        # Tipos válidos de licencia
        valid_types = ['A1', 'A2', 'A', 'B', 'C1', 'C', 'D1', 'D', 'BE', 'CE', 'DE']
        
        if license_type and license_type.upper() not in valid_types:
            result['errors'].append(f'Tipo de licencia inválido. Válidos: {", ".join(valid_types)}')
        
        if expiry_date:
            try:
                expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
                if expiry <= datetime.now():
                    result['errors'].append('La licencia no puede estar vencida')
            except ValueError:
                result['errors'].append('Formato de fecha inválido. Use YYYY-MM-DD')
        
        if not result['errors']:
            result['valid'] = True
            result['cleaned_values'] = {
                'license_type': license_type.upper() if license_type else None,
                'expiry_date': expiry_date
            }
            
        return result
    
    @staticmethod
    def validate_schedule_data(schedule: List[Dict]) -> Dict[str, any]:
        """
        Valida datos de horario académico
        
        Args:
            schedule: Lista de clases con dia, hora, info
            
        Returns:
            Dict con resultado de validación
        """
        result = {'valid': False, 'errors': [], 'warnings': []}
        
        if not schedule or not isinstance(schedule, list):
            result['errors'].append('Horario debe ser una lista no vacía')
            return result
        
        valid_days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        
        for i, clase in enumerate(schedule):
            if not isinstance(clase, dict):
                result['errors'].append(f'Clase {i+1}: debe ser un objeto válido')
                continue
                
            # Validar día
            if 'dia' not in clase or clase['dia'] not in valid_days:
                result['errors'].append(f'Clase {i+1}: día inválido')
            
            # Validar hora
            if 'hora' not in clase or not re.match(time_pattern, clase.get('hora', '')):
                result['errors'].append(f'Clase {i+1}: hora inválida (formato HH:MM)')
            
            # Validar información de clase
            if 'info_clase' not in clase or not clase.get('info_clase', '').strip():
                result['warnings'].append(f'Clase {i+1}: información de clase vacía')
        
        if not result['errors']:
            result['valid'] = True
            
        return result

class FormValidator:
    """Validador específico para formularios web"""
    
    @staticmethod
    def validate_student_form(form_data: Dict) -> Dict[str, any]:
        """
        Valida formulario de estudiante completo
        
        Args:
            form_data: Datos del formulario
            
        Returns:
            Dict con resultados de validación
        """
        result = {
            'valid': True,
            'errors': {},
            'warnings': {},
            'cleaned_data': {}
        }
        
        # Validar matrícula
        matricola_result = DataValidator.validate_matricola(
            form_data.get('matricola', '')
        )
        if not matricola_result['valid']:
            result['errors']['matricola'] = matricola_result['errors']
            result['valid'] = False
        else:
            result['cleaned_data']['matricola'] = matricola_result['cleaned_value']
        
        # Validar contraseña (más flexible para portal universitario)
        password = form_data.get('password', '')
        if not password:
            result['errors']['password'] = ['La contraseña es obligatoria']
            result['valid'] = False
        elif len(password) < 3:
            result['errors']['password'] = ['La contraseña es demasiado corta']
            result['valid'] = False
        
        # Validar datos de licencia si están presentes
        if form_data.get('tiene_licencia') == 'true':
            license_result = DataValidator.validate_license_data(
                form_data.get('tipo_licencia'),
                form_data.get('vencimiento_licencia')
            )
            if not license_result['valid']:
                result['errors']['license'] = license_result['errors']
                result['valid'] = False
            else:
                result['cleaned_data'].update(license_result['cleaned_values'])
        
        return result
    
    @staticmethod
    def validate_admin_form(form_data: Dict) -> Dict[str, any]:
        """Valida formulario de administrador"""
        result = {'valid': True, 'errors': {}}
        
        # Validar matrícula de admin
        matricola_result = DataValidator.validate_matricola(
            form_data.get('matricola', '')
        )
        if not matricola_result['valid']:
            result['errors']['matricola'] = matricola_result['errors']
            result['valid'] = False
        
        # La contraseña de admin puede ser menos estricta
        if not form_data.get('password'):
            result['errors']['password'] = ['La contraseña es obligatoria']
            result['valid'] = False
        
        return result
    
    @staticmethod
    def validate_admin_login(form_data: Dict) -> List[str]:
        """Valida datos de login de administrador (versión simplificada)"""
        errors = []
        
        matricola = form_data.get('matricola', '').strip()
        password = form_data.get('password', '').strip()
        
        if not matricola:
            errors.append('La matrícula es obligatoria')
        
        if not password:
            errors.append('La contraseña es obligatoria')
            
        return errors
