from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apptask.models import User, SchoolClass, Task, Delivery


class Command(BaseCommand):
    help = 'Crea datos de prueba para el sistema de tareas'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de prueba...')
        
        # Crear profesores
        teacher1, created = User.objects.get_or_create(
            username='prof_maria',
            defaults={
                'email': 'maria@school.com',
                'name': 'María García',
                'phone': '123456789',
                'dni': '12345678',
                'role': 'teacher',
                'password': 'pbkdf2_sha256$600000$dummy$dummy',
            }
        )
        
        teacher2, created = User.objects.get_or_create(
            username='prof_juan',
            defaults={
                'email': 'juan@school.com',
                'name': 'Juan Pérez',
                'phone': '987654321',
                'dni': '87654321',
                'role': 'teacher',
                'password': 'pbkdf2_sha256$600000$dummy$dummy',
            }
        )

        # Crear estudiantes
        students = []
        student_data = [
            ('ana_lopez', 'ana@student.com', 'Ana López', '555-0001', '10001'),
            ('carlos_ruiz', 'carlos@student.com', 'Carlos Ruiz', '555-0002', '10002'),
            ('sofia_martin', 'sofia@student.com', 'Sofía Martín', '555-0003', '10003'),
            ('diego_torres', 'diego@student.com', 'Diego Torres', '555-0004', '10004'),
            ('lucia_mendez', 'lucia@student.com', 'Lucía Méndez', '555-0005', '10005'),
        ]
        
        for username, email, name, phone, dni in student_data:
            student, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'name': name,
                    'phone': phone,
                    'dni': dni,
                    'role': 'student',
                    'password': 'pbkdf2_sha256$600000$dummy$dummy',
                }
            )
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
            theme='Ecuaciones Lineales',
            school_class=class1,
            defaults={
                'instruction': 'Resolver los ejercicios 1-10 del capítulo 3. Mostrar todo el proceso de resolución paso a paso.',
                'delivery_date': today + timedelta(days=7),
                'delivery_time': timezone.time(23, 59),
            }
        )

        task2, created = Task.objects.get_or_create(
            theme='Análisis de Texto',
            school_class=class2,
            defaults={
                'instruction': 'Leer el cuento "El Principito" y escribir un ensayo de 500 palabras sobre sus temas principales.',
                'delivery_date': today + timedelta(days=5),
                'delivery_time': timezone.time(18, 30),
            }
        )
        
        task3, created = Task.objects.get_or_create(
            theme='Geometría Plana',
            school_class=class1,
            defaults={
                'instruction': 'Calcular el área y perímetro de las figuras geométricas del ejercicio 5.2.',
                'delivery_date': today + timedelta(days=3),
                'delivery_time': timezone.time(15, 00),
            }
        )

        # Crear algunas entregas
        delivery1, created = Delivery.objects.get_or_create(
            task=task1,
            student=students[0],
            defaults={
                'revisor': teacher1,
                'date': today - timedelta(days=1),
                'delivery_time': timezone.time(14, 30),
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
                'delivery_time': timezone.time(16, 45),
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
                'delivery_time': timezone.time(17, 15),
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
