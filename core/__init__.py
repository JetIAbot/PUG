"""
Core - Módulo principal de PUG
Contiene la lógica central del sistema de agrupación de estudiantes
"""

from .student_scheduler import StudentScheduler
from .portal_extractor import PortalExtractor
from .demo_generator import DemoDataGenerator
from .obsidian_manager import ObsidianManager
from .data_processor import DataProcessor

__all__ = [
    'StudentScheduler',
    'PortalExtractor', 
    'DemoDataGenerator',
    'ObsidianManager',
    'DataProcessor'
]
