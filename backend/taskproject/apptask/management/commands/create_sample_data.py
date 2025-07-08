from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, time  # Agregar time aquí
from decimal import Decimal
from apptask.models import User, SchoolClass, Task, Delivery


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de tareas'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de prueba...')
        
        # Crear administrador
        admin, created = User.objects.get_or_create(
            email='admin@uni.edu.ec',
            defaults={
                'username': 'admin',
                'first_name': 'Administrador',
                'name': 'Administrador Sistema',
                'role': 'admin',  # Agregar este campo
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
                'role': 'teacher',  # Agregar este campo
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
                'role': 'teacher',  # Agregar este campo
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
                    'role': 'student',  # Agregar este campo
                }
            )
            if created:
                student.set_password('student123')
                student.save()
                self.stdout.write(f'Estudiante creado: {student.email}')
            students.append(student)
        
        
        # Crear clases
        class1, created = SchoolClass.objects.get_or_create(
            identify='MAT-101',
            defaults={
                'course': 'Matemáticas Básicas',
                'teacher': teacher1,
            }
        )
        class1.student_list.set(students[:3])  # Primeros 3 estudiantes

        class2, created = SchoolClass.objects.get_or_create(
            identify='ESP-201',
            defaults={
                'course': 'Español Avanzado',
                'teacher': teacher2,
            }
        )
        class2.student_list.set(students[2:])  # Últimos 3 estudiantes (con overlap)

        # Crear tareas
        today = timezone.now().date()
        
        task1, created = Task.objects.get_or_create(
            theme='Ejercicios de Python',
            defaults={
                'instruction': 'Resolver los ejercicios 1-10 del libro de texto',
                'delivery_date': timezone.now().date() + timedelta(days=7),
                'delivery_time': time(23, 59),  # Cambiar esta línea
                'school_class': class1,
            }
        )
        if created:
            self.stdout.write(f'Tarea creada: {task1.theme}')
        
        task2, created = Task.objects.get_or_create(
            theme='Diseño de Base de Datos',
            defaults={
                'instruction': 'Crear un modelo ER para un sistema de biblioteca',
                'delivery_date': timezone.now().date() + timedelta(days=10),
                'delivery_time': time(23, 59),  # Cambiar esta línea
                'school_class': class2,
            }
        )
        
        task3, created = Task.objects.get_or_create(
            theme='Geometría Plana',
            school_class=class1,
            defaults={
                'instruction': 'Calcular el área y perímetro de las figuras geométricas del ejercicio 5.2.',
                'delivery_date': today + timedelta(days=3),
                'delivery_time': time(15, 00),
            }
        )

        # Crear algunas entregas
        delivery1, created = Delivery.objects.get_or_create(
            task=task1,
            student=students[0],
            defaults={
                'revisor': teacher1,
                'date': today - timedelta(days=1),
                'delivery_time': time(14, 30),
                'file_url': 'https://drive.google.com/file/d/ejemplo1',
                'feedback': 'Excelente trabajo. Los pasos están bien explicados.',
                'grade': Decimal('9.50'),
            }
        )

        delivery2, created = Delivery.objects.get_or_create(
            task=task1,
            student=students[1],
            defaults={
                'revisor': teacher1,
                'date': today,
                'delivery_time': time(16, 45),
                'file_url': 'https://drive.google.com/file/d/ejemplo2',
                # Sin feedback aún (pendiente de calificar)
            }
        )

        delivery3, created = Delivery.objects.get_or_create(
            task=task2,
            student=students[2],
            defaults={
                'revisor': teacher2,
                'date': today - timedelta(days=2),
                'delivery_time': time(17, 15),
                'file_url': 'https://drive.google.com/file/d/ejemplo3',
                'feedback': 'Buen análisis, pero podría profundizar más en el tema central.',
                'grade': Decimal('7.80'),
            }
        )

        self.stdout.write(
            self.style.SUCCESS('Datos de prueba creados exitosamente!')
        )
        self.stdout.write(f'- {len(students)} estudiantes creados')
        self.stdout.write(f'- 2 profesores creados')
        self.stdout.write(f'- 2 clases creadas')
        self.stdout.write(f'- 3 tareas creadas')
        self.stdout.write(f'- 3 entregas creadas')
