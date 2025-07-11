from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apptask.models import User, SchoolClass, Task, Delivery

class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de tareas y usuarios'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de prueba...')
        
        # Crear administrador
        admin, created = User.objects.get_or_create(
            email='admin@uni.edu.ec',
            defaults={
                'username': 'admin',
                'first_name': 'Administrador',
                'name': 'Administrador Sistema',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(f'Administrador creado: {admin.email}')
        
        # Crear profesores
        teacher1, created = User.objects.get_or_create(
            email='maria.garcia@uni.edu.ec',
            defaults={
                'username': 'prof_maria',
                'first_name': 'María García',
                'name': 'María García',
                'role': 'teacher',
                'phone': '123456789',
                'dni': '12345678',
            }
        )
        if created:
            teacher1.set_password('teacher123')
            teacher1.save()
            self.stdout.write(f'Profesor creado: {teacher1.email}')
        
        teacher2, created = User.objects.get_or_create(
            email='juan.perez@uni.edu.ec',
            defaults={
                'username': 'prof_juan',
                'first_name': 'Juan Pérez',
                'name': 'Juan Pérez',
                'role': 'teacher',
                'phone': '987654321',
                'dni': '87654321',
            }
        )
        if created:
            teacher2.set_password('teacher123')
            teacher2.save()
            self.stdout.write(f'Profesor creado: {teacher2.email}')
        
        # Crear estudiantes
        students = []
        student_data = [
            ('ana.lopez@uni.edu.ec', 'ana_lopez', 'Ana López'),
            ('carlos.ruiz@uni.edu.ec', 'carlos_ruiz', 'Carlos Ruiz'),
            ('sofia.martin@uni.edu.ec', 'sofia_martin', 'Sofía Martín'),
            ('diego.torres@uni.edu.ec', 'diego_torres', 'Diego Torres'),
            ('lucia.mendez@uni.edu.ec', 'lucia_mendez', 'Lucía Méndez'),
        ]
        
        for email, username, name in student_data:
            student, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': name,
                    'name': name,
                    'role': 'student',
                }
            )
            if created:
                student.set_password('student123')
                student.save()
                self.stdout.write(f'Estudiante creado: {student.email}')
            students.append(student)
        
        self.stdout.write(
            self.style.SUCCESS('¡Datos de prueba creados exitosamente!')
        )
        self.stdout.write(f'- 1 administrador: admin@uni.edu.ec / admin123')
        self.stdout.write(f'- 2 profesores: [email] / teacher123')
        self.stdout.write(f'- {len(students)} estudiantes: [email] / student123')