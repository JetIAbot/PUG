"""
Script específico para verificar que el TEXTO de los labels sea visible
"""

import requests
from bs4 import BeautifulSoup
import re

def test_label_text_visibility():
    """Verificar que el texto específico de los labels sea visible"""
    print("🔍 VERIFICANDO TEXTO ESPECÍFICO DE LABELS")
    print("=" * 60)
    
    # Página de administradores
    print("\n📋 PÁGINA DE ADMINISTRADORES:")
    try:
        response = requests.get("http://127.0.0.1:5000/admin/login")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            content = response.text
            
            # Verificar presencia del texto específico
            if 'Usuario Administrador' in content:
                print("✅ Texto 'Usuario Administrador' presente en HTML")
            else:
                print("❌ Texto 'Usuario Administrador' NO presente en HTML")
            
            if 'Contraseña de Administrador' in content:
                print("✅ Texto 'Contraseña de Administrador' presente en HTML")
            else:
                print("❌ Texto 'Contraseña de Administrador' NO presente en HTML")
            
            # Verificar estructura con span
            if '<span class="label-text">' in content:
                print("✅ Estructura con span.label-text implementada")
            else:
                print("❌ Estructura con span.label-text NO implementada")
            
            # Verificar CSS específico
            if 'label-text' in content and 'color: #2c3e50' in content:
                print("✅ CSS específico para label-text aplicado")
            else:
                print("⚠️ CSS específico para label-text no detectado")
                
    except Exception as e:
        print(f"❌ Error verificando admin: {e}")
    
    # Página de estudiantes
    print("\n👨‍🎓 PÁGINA DE ESTUDIANTES:")
    try:
        response = requests.get("http://127.0.0.1:5000/")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            content = response.text
            
            # Verificar presencia del texto específico
            if 'Número de Matrícula' in content:
                print("✅ Texto 'Número de Matrícula' presente en HTML")
            else:
                print("❌ Texto 'Número de Matrícula' NO presente en HTML")
            
            if 'Contraseña' in content:
                print("✅ Texto 'Contraseña' presente en HTML")
            else:
                print("❌ Texto 'Contraseña' NO presente en HTML")
            
            # Verificar estructura con span
            if '<span class="label-text">' in content:
                print("✅ Estructura con span.label-text implementada")
            else:
                print("❌ Estructura con span.label-text NO implementada")
                
    except Exception as e:
        print(f"❌ Error verificando estudiantes: {e}")

def test_css_specific_rules():
    """Verificar reglas CSS específicas para label-text"""
    print("\n🎨 VERIFICANDO CSS ESPECÍFICO:")
    try:
        # Verificar admin
        response = requests.get("http://127.0.0.1:5000/admin/login")
        if response.status_code == 200:
            content = response.text
            
            css_rules = [
                '.label-text',
                'background-color: rgba(255,255,255,0.8)',
                'text-shadow: 0 1px 2px rgba(0,0,0,0.1)',
                'font-weight: 700'
            ]
            
            for rule in css_rules:
                if rule in content:
                    print(f"✅ Regla CSS '{rule}' encontrada")
                else:
                    print(f"❌ Regla CSS '{rule}' no encontrada")
                    
    except Exception as e:
        print(f"❌ Error verificando CSS: {e}")

def extract_label_html():
    """Extraer el HTML exacto de los labels para debug"""
    print("\n🔬 ESTRUCTURA HTML DE LABELS:")
    try:
        response = requests.get("http://127.0.0.1:5000/admin/login")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontrar todos los labels
            labels = soup.find_all('label', class_='form-label')
            
            for i, label in enumerate(labels, 1):
                print(f"\nLabel {i}:")
                print(f"HTML: {label}")
                print(f"Texto visible: '{label.get_text().strip()}'")
                
                # Verificar si tiene span
                span = label.find('span', class_='label-text')
                if span:
                    print(f"Span encontrado: '{span.get_text().strip()}'")
                else:
                    print("Sin span label-text")
                    
    except Exception as e:
        print(f"❌ Error extrayendo HTML: {e}")

def main():
    """Función principal"""
    test_label_text_visibility()
    test_css_specific_rules()
    extract_label_html()
    
    print("\n" + "=" * 60)
    print("🎯 RESUMEN DE CORRECCIONES APLICADAS:")
    print("1. ✅ Texto envuelto en <span class='label-text'>")
    print("2. ✅ CSS específico para .label-text")
    print("3. ✅ Fondo semitransparente para labels")
    print("4. ✅ Text-shadow para mejor legibilidad")
    print("5. ✅ Font-weight 700 (extra negrilla)")
    print("\n🌐 Verifica visualmente en:")
    print("- Admin: http://127.0.0.1:5000/admin/login")
    print("- Estudiantes: http://127.0.0.1:5000/")

if __name__ == "__main__":
    main()
