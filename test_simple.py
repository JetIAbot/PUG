"""
Script simple para probar imports básicos
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Probando imports básicos...")

try:
    print("1. Probando utils.constants...")
    from utils.constants import ORDEN_BLOQUES
    print(f"   ✅ ORDEN_BLOQUES: {len(ORDEN_BLOQUES)} elementos")
except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    print("2. Probando config...")
    from config import get_config
    config = get_config()
    print(f"   ✅ Config cargado: {config.__name__}")
except Exception as e:
    print(f"   ❌ Error: {e}")

try:
    print("3. Probando core.demo_generator...")
    from core.demo_generator import DemoDataGenerator
    generator = DemoDataGenerator()
    print(f"   ✅ DemoDataGenerator creado")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("Prueba completada.")
