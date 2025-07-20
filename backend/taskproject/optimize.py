#!/usr/bin/env python
"""
Script para optimizar el rendimiento de la aplicación Django
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def optimize_app():
    """Ejecuta optimizaciones básicas"""
    print("🚀 Iniciando optimizaciones de rendimiento...")
    
    # Limpiar archivos de log grandes
    try:
        log_file = 'django.log'
        if os.path.exists(log_file):
            file_size = os.path.getsize(log_file) / (1024 * 1024)  # MB
            if file_size > 10:  # Si el log es mayor a 10MB
                print(f"📋 Limpiando log de {file_size:.1f}MB...")
                with open(log_file, 'w') as f:
                    f.write("")
    except Exception as e:
        print(f"❌ Error limpiando logs: {e}")
    
    # Recolectar archivos estáticos
    try:
        print("📦 Recolectando archivos estáticos...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    except Exception as e:
        print(f"❌ Error recolectando estáticos: {e}")
    
    # Comprimir archivos estáticos
    try:
        print("🗜️ Comprimiendo archivos estáticos...")
        execute_from_command_line(['manage.py', 'compress', '--force'])
    except Exception as e:
        print("⚠️ Comando compress no disponible, instalando django-compressor...")
    
    print("✅ Optimizaciones completadas!")
    print("\n📊 Recomendaciones adicionales:")
    print("1. Usar un servidor web como Nginx en producción")
    print("2. Configurar Redis para cache")
    print("3. Optimizar consultas SQL con django-debug-toolbar")
    print("4. Configurar un CDN para archivos estáticos")
    print("5. Usar gunicorn con múltiples workers")

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskproject.settings')
    django.setup()
    optimize_app()
