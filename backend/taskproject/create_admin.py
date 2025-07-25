#!/usr/bin/env python
"""
Script para crear un usuario administrador
Ejecutar con: python manage.py shell < create_admin.py
O copiar y pegar el contenido en: python manage.py shell
"""

import os
import django
from django.contrib.auth import get_user_model
from django.db import IntegrityError

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taskproject.settings')  # Cambiar por tu settings
django.setup()

User = get_user_model()

def create_admin_user():
    """Crear usuario administrador"""
    
    # Datos del administrador
    admin_data = {
        'username': 'admin',
        'email': 'admin@uni.edu.ec',
        'first_name': 'Administrador',
        'last_name': 'Sistema',
        'name': 'Administrador del Sistema',
        'phone': '0999999999',
        'dni': '1234567890',  # DNI dummy ya que quitaste la validación
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
        'is_active': True,
    }
    
    password = 'student123'
    
    try:
        # Verificar si el usuario ya existe
        if User.objects.filter(email=admin_data['email']).exists():
            print(f"❌ El usuario con email {admin_data['email']} ya existe.")
            return False
            
        if User.objects.filter(username=admin_data['username']).exists():
            print(f"❌ El usuario con username {admin_data['username']} ya existe.")
            return False
        
        # Crear el usuario administrador
        admin_user = User.objects.create_user(
            password=password,
            **admin_data
        )
        
        print("✅ Usuario administrador creado exitosamente!")
        print(f"📧 Email: {admin_user.email}")
        print(f"👤 Username: {admin_user.username}")
        print(f"🔑 Password: {password}")
        print(f"🎯 Rol: {admin_user.get_role_display()}")
        print(f"🆔 ID: {admin_user.id}")
        
        return True
        
    except IntegrityError as e:
        print(f"❌ Error de integridad: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def verify_admin_user():
    """Verificar que el usuario administrador fue creado correctamente"""
    try:
        admin = User.objects.get(email='admin@uni.edu.ec')
        print("\n🔍 Verificación del usuario creado:")
        print(f"📧 Email: {admin.email}")
        print(f"👤 Username: {admin.username}")
        print(f"📛 Nombre completo: {admin.display_name}")
        print(f"📱 Teléfono: {admin.phone}")
        print(f"🆔 DNI: {admin.dni}")
        print(f"🎯 Rol: {admin.get_role_display()}")
        print(f"👨‍💼 Es staff: {admin.is_staff}")
        print(f"🔧 Es superuser: {admin.is_superuser}")
        print(f"✅ Está activo: {admin.is_active}")
        
        # Verificar login
        from django.contrib.auth import authenticate
        user = authenticate(username='admin@uni.edu.ec', password='student123')
        if user:
            print("🔐 Autenticación exitosa!")
        else:
            print("❌ Error en autenticación!")
            
    except User.DoesNotExist:
        print("❌ El usuario administrador no fue encontrado.")

# Ejecutar el script
if __name__ == '__main__':
    print("🚀 Iniciando creación del usuario administrador...")
    print("=" * 50)
    
    success = create_admin_user()
    
    if success:
        verify_admin_user()
        print("\n" + "=" * 50)
        print("✅ Script completado exitosamente!")
        print("\n💡 Puedes iniciar sesión con:")
        print("   Email: admin@uni.edu.ec")
        print("   Password: student123")
    else:
        print("\n" + "=" * 50)
        print("❌ Error al crear el usuario administrador.")

# Si ejecutas directamente en el shell de Django, usa esto:
create_admin_user()
verify_admin_user()