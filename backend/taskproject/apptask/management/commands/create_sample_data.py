from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apptask.models import SchoolClass, Task, Delivery
from datetime import date, time, datetime
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample data for testing'

    def handle(self, *args, **options):
        # Crear usuarios
        teacher, created = User.objects.get_or_create(
            email='teacher@test.com',
            defaults={
                'username': 'teacher1',
                'name': 'Prof. María García',
                'phone': '987654321',
                'dni': '12345678',
                'role': 'teacher'
            }
        )
        if created:
            teacher.set_password('password123')
            teacher.save()
            self.stdout.write(f'Profesor creado: {teacher.name}')

        students = []
        student_data = [
            ('student1@test.com', 'student1', 'Juan Pérez', '987654322', '12345679'),
            ('student2@test.com', 'student2', 'Ana López', '987654323', '12345680'),
            ('student3@test.com', 'student3', 'Carlos Ruiz', '987654324', '12345681'),
        ]

        for email, username, name, phone, dni in student_data:
            student, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'name': name,
                    'phone': phone,
                    'dni': dni,
                    'role': 'student'
                }
            )
            if created:
                student.set_password('password123')
                student.save()
                self.stdout.write(f'Estudiante creado: {student.name}')
            students.append(student)

        # Crear clase
        school_class, created = SchoolClass.objects.get_or_create(
            identify='MAT-101',
            defaults={
                'course': 'Matemáticas Básicas',
                'teacher': teacher
            }
        )
        if created:
            school_class.student_list.set(students)
            self.stdout.write(f'Clase creada: {school_class.identify}')

        # Crear tareas
        tasks_data = [
            ('Ejercicios de Álgebra', 'Resolver los ejercicios del capítulo 3', date(2025, 7, 15), time(23, 59)),
            ('Geometría Básica', 'Calcular áreas y perímetros', date(2025, 7, 20), time(18, 0)),
            ('Estadística Descriptiva', 'Analizar el conjunto de datos proporcionado', date(2025, 7, 25), time(23, 59)),
        ]

        tasks = []
        for theme, instruction, delivery_date, delivery_time in tasks_data:
            task, created = Task.objects.get_or_create(
                theme=theme,
                school_class=school_class,
                defaults={
                    'instruction': instruction,
                    'delivery_date': delivery_date,
                    'delivery_time': delivery_time
                }
            )
            if created:
                self.stdout.write(f'Tarea creada: {task.theme}')
            tasks.append(task)

        # Crear algunas entregas
        deliveries_data = [
            (tasks[0], students[0], date(2025, 7, 14), time(20, 30), 'http://example.com/file1.pdf', Decimal('8.5')),
            (tasks[0], students[1], date(2025, 7, 15), time(22, 0), 'http://example.com/file2.pdf', Decimal('9.2')),
            (tasks[1], students[0], date(2025, 7, 19), time(16, 45), 'http://example.com/file3.pdf', Decimal('7.8')),
        ]

        for task, student, delivery_date, delivery_time, file_url, grade in deliveries_data:
            delivery, created = Delivery.objects.get_or_create(
                task=task,
                student=student,
                defaults={
                    'revisor': teacher,
                    'date': delivery_date,
                    'delivery_time': delivery_time,
                    'file_url': file_url,
                    'feedback': f'Buen trabajo en {task.theme}',
                    'grade': grade
                }
            )
            if created:
                self.stdout.write(f'Entrega creada: {task.theme} - {student.name}')

        self.stdout.write(self.style.SUCCESS('Datos de prueba creados exitosamente!'))