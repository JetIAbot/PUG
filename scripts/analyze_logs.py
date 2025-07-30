#!/usr/bin/env python3
"""
Script de análisis de logs de seguridad para PUG
Uso: python scripts/analyze_logs.py --log-file logs/security.log --hours 24
"""

import json
import re
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path

class LogAnalyzer:
    """Analizador de logs de seguridad"""
    
    def __init__(self, log_file: str):
        self.log_file = log_file
        self.events = []
        self.load_logs()
    
    def load_logs(self):
        """Cargar eventos de los logs"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        # Extraer JSON del mensaje de log
                        json_match = re.search(r'\{.*\}', line)
                        if json_match:
                            event_data = json.loads(json_match.group())
                            self.events.append(event_data)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"❌ Archivo de log no encontrado: {self.log_file}")
            print("💡 Asegúrate de que la aplicación esté ejecutándose y generando logs")
            return
    
    def analyze_login_attempts(self, hours: int = 24):
        """Analizar intentos de login en las últimas N horas"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        login_events = [
            e for e in self.events 
            if e.get('event_type') == 'login_attempt'
            and datetime.fromisoformat(e['timestamp']) > cutoff
        ]
        
        total_attempts = len(login_events)
        if total_attempts == 0:
            print(f"\n📊 === Análisis de Logins (últimas {hours} horas) ===")
            print("ℹ️  No se encontraron intentos de login en el período especificado")
            return {'total': 0, 'successful': 0, 'failed': 0, 'suspicious_ips': []}
        
        successful = len([e for e in login_events if e['details']['success']])
        failed = total_attempts - successful
        
        # Detectar patrones sospechosos
        ip_attempts = Counter(e['ip_address'] for e in login_events if e.get('ip_address'))
        user_attempts = Counter(e['user_id'] for e in login_events if e.get('user_id'))
        
        print(f"\n📊 === Análisis de Logins (últimas {hours} horas) ===")
        print(f"📈 Total intentos: {total_attempts}")
        print(f"✅ Exitosos: {successful}")
        print(f"❌ Fallidos: {failed}")
        
        if total_attempts > 0:
            success_rate = (successful/total_attempts*100)
            print(f"📊 Tasa de éxito: {success_rate:.1f}%")
        
        # IPs con muchos intentos fallidos
        suspicious_ips = []
        if ip_attempts:
            print(f"\n🌐 IPs más activas:")
            for ip, count in ip_attempts.most_common(5):
                ip_events = [e for e in login_events if e.get('ip_address') == ip]
                failed_from_ip = len([e for e in ip_events if not e['details']['success']])
                
                print(f"  🔗 {ip}: {count} intentos ({failed_from_ip} fallos)")
                
                if failed_from_ip > 5:  # Threshold
                    suspicious_ips.append((ip, failed_from_ip, count))
        
        if suspicious_ips:
            print(f"\n⚠️  IPs sospechosas (>5 fallos):")
            for ip, failed, total in suspicious_ips:
                print(f"  🚨 {ip}: {failed}/{total} fallos")
        
        # Usuarios con más intentos
        if user_attempts:
            print(f"\n👤 Usuarios más activos:")
            for user, count in user_attempts.most_common(5):
                user_events = [e for e in login_events if e.get('user_id') == user]
                failed_from_user = len([e for e in user_events if not e['details']['success']])
                print(f"  👨‍💼 {user}: {count} intentos ({failed_from_user} fallos)")
        
        return {
            'total': total_attempts,
            'successful': successful,
            'failed': failed,
            'suspicious_ips': suspicious_ips
        }
    
    def analyze_data_extractions(self, hours: int = 24):
        """Analizar extracciones de datos"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        extraction_events = [
            e for e in self.events 
            if e.get('event_type') == 'data_extraction'
            and datetime.fromisoformat(e['timestamp']) > cutoff
        ]
        
        total_extractions = len(extraction_events)
        if total_extractions == 0:
            print(f"\n🔄 === Análisis de Extracciones (últimas {hours} horas) ===")
            print("ℹ️  No se encontraron extracciones de datos en el período especificado")
            return
        
        successful = len([e for e in extraction_events if e['details']['success']])
        
        # Estadísticas de duración
        durations = [
            e['details'].get('duration_seconds', 0) 
            for e in extraction_events 
            if e['details']['success'] and e['details'].get('duration_seconds')
        ]
        
        print(f"\n🔄 === Análisis de Extracciones (últimas {hours} horas) ===")
        print(f"📈 Total extracciones: {total_extractions}")
        print(f"✅ Exitosas: {successful}")
        print(f"❌ Fallidas: {total_extractions - successful}")
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            print(f"⏱️  Duración promedio: {avg_duration:.2f} segundos")
            print(f"⏱️  Duración máxima: {max(durations):.2f} segundos")
            print(f"⏱️  Duración mínima: {min(durations):.2f} segundos")
        
        # Errores más comunes
        failed_events = [e for e in extraction_events if not e['details']['success']]
        if failed_events:
            error_types = Counter()
            for event in failed_events:
                error = event['details'].get('error', 'Unknown error')
                error_types[error] += 1
            
            print(f"\n❌ Errores más comunes:")
            for error, count in error_types.most_common(3):
                print(f"  🔸 {error}: {count} veces")
    
    def analyze_admin_actions(self, hours: int = 24):
        """Analizar acciones de administradores"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        admin_events = [
            e for e in self.events 
            if e.get('event_type') == 'admin_action'
            and datetime.fromisoformat(e['timestamp']) > cutoff
        ]
        
        if not admin_events:
            print(f"\n👥 === Análisis de Acciones Admin (últimas {hours} horas) ===")
            print("ℹ️  No se encontraron acciones de administrador en el período especificado")
            return
        
        action_counts = Counter(e['details']['action'] for e in admin_events)
        admin_counts = Counter(e['user_id'] for e in admin_events if e.get('user_id'))
        
        print(f"\n👥 === Análisis de Acciones Admin (últimas {hours} horas) ===")
        print(f"📈 Total acciones: {len(admin_events)}")
        
        if action_counts:
            print("\n⚡ Acciones más frecuentes:")
            for action, count in action_counts.most_common(5):
                print(f"  🔸 {action}: {count}")
        
        if admin_counts:
            print("\n👑 Admins más activos:")
            for admin, count in admin_counts.most_common(5):
                print(f"  👨‍💼 {admin}: {count} acciones")
    
    def analyze_security_events(self, hours: int = 24):
        """Analizar eventos de seguridad generales"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        security_events = [
            e for e in self.events 
            if datetime.fromisoformat(e['timestamp']) > cutoff
        ]
        
        event_types = Counter(e.get('event_type', 'unknown') for e in security_events)
        
        print(f"\n🔐 === Resumen de Eventos de Seguridad (últimas {hours} horas) ===")
        for event_type, count in event_types.most_common():
            emoji = {
                'login_attempt': '🔑',
                'data_extraction': '📥',
                'admin_action': '👑',
                'request_received': '📡',
                'request_completed': '✅',
                'invalid_form_submission': '⚠️',
                'unauthorized_admin_attempt': '🚨'
            }.get(event_type, '📋')
            
            print(f"  {emoji} {event_type}: {count}")
    
    def generate_security_report(self, hours: int = 24):
        """Generar reporte completo de seguridad"""
        print("=" * 80)
        print(f"🔒 REPORTE DE SEGURIDAD PUG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        if not self.events:
            print("❌ No se encontraron eventos en los logs.")
            print("💡 Verifica que:")
            print("   - La aplicación esté ejecutándose")
            print("   - El sistema de logging esté configurado")
            print("   - Los archivos de log tengan los permisos correctos")
            return
        
        print(f"📊 Analizando {len(self.events)} eventos totales")
        
        login_analysis = self.analyze_login_attempts(hours)
        self.analyze_data_extractions(hours)
        self.analyze_admin_actions(hours)
        self.analyze_security_events(hours)
        
        # Alertas de seguridad
        alerts = []
        
        if login_analysis['suspicious_ips']:
            alerts.append(f"🚨 {len(login_analysis['suspicious_ips'])} IPs con actividad sospechosa")
        
        if login_analysis['total'] > 0 and login_analysis['failed'] > login_analysis['successful'] * 2:
            alerts.append(f"⚠️  Muchos logins fallidos: {login_analysis['failed']} vs {login_analysis['successful']}")
        
        # Verificar eventos recientes de seguridad críticos
        recent_security_events = [
            e for e in self.events 
            if e.get('event_type') in ['unauthorized_admin_attempt', 'invalid_form_submission']
            and datetime.fromisoformat(e['timestamp']) > datetime.utcnow() - timedelta(hours=1)
        ]
        
        if recent_security_events:
            alerts.append(f"🔴 {len(recent_security_events)} eventos de seguridad críticos en la última hora")
        
        print(f"\n{'='*80}")
        if alerts:
            print(f"🔔 ALERTAS DE SEGURIDAD:")
            for alert in alerts:
                print(f"  {alert}")
        else:
            print(f"✅ No se detectaron alertas de seguridad críticas")
        
        print(f"\n📝 Reporte generado desde: {self.log_file}")
        print(f"⏰ Período analizado: últimas {hours} horas")
        print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description='Analizar logs de seguridad de PUG')
    parser.add_argument('--log-file', default='logs/security.log', 
                       help='Archivo de log a analizar (default: logs/security.log)')
    parser.add_argument('--hours', type=int, default=24, 
                       help='Horas a analizar hacia atrás (default: 24)')
    parser.add_argument('--create-sample', action='store_true',
                       help='Crear logs de ejemplo para testing')
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_logs()
        return
    
    # Verificar que el archivo existe
    log_path = Path(args.log_file)
    if not log_path.exists():
        print(f"❌ El archivo {args.log_file} no existe.")
        print(f"💡 Asegúrate de que:")
        print(f"   1. La aplicación PUG esté ejecutándose")
        print(f"   2. El directorio 'logs' exista")
        print(f"   3. El sistema de logging esté configurado")
        print(f"\n🔧 Para crear logs de ejemplo, ejecuta:")
        print(f"   python {__file__} --create-sample")
        return
    
    analyzer = LogAnalyzer(args.log_file)
    analyzer.generate_security_report(args.hours)

def create_sample_logs():
    """Crear logs de ejemplo para testing"""
    import os
    
    # Crear directorio de logs si no existe
    os.makedirs('logs', exist_ok=True)
    
    sample_events = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "login_attempt",
            "user_id": "admin123",
            "ip_address": "192.168.1.100",
            "details": {"matricola": "admin123", "success": True, "user_agent": "Mozilla/5.0"}
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            "event_type": "data_extraction",
            "user_id": "123456",
            "details": {"success": True, "duration_seconds": 45.2}
        },
        {
            "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
            "event_type": "login_attempt",
            "user_id": "hacker",
            "ip_address": "203.0.113.1",
            "details": {"matricola": "hacker", "success": False, "user_agent": "Bot"}
        }
    ]
    
    with open('logs/security.log', 'w', encoding='utf-8') as f:
        for event in sample_events:
            log_line = f"2024-01-01 12:00:00 - security - WARNING - {json.dumps(event)}\n"
            f.write(log_line)
    
    print("✅ Logs de ejemplo creados en logs/security.log")
    print("🔍 Ahora puedes ejecutar: python scripts/analyze_logs.py")

if __name__ == '__main__':
    main()
