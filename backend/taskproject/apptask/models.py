from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    dni = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    ROLE_CHOICES = [
        ("teacher", "Teacher"),
        ("student", "Student"),
        ("observer", "Observer"),
        ("admin", "Admin"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    
    # Agregar related_name para evitar conflictos
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "name", "phone", "dni"]

class SchoolClass(models.Model):
    identify = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    teacher = models.ForeignKey(
        User,
        limit_choices_to={"role": "teacher"},
        on_delete=models.CASCADE,
        related_name="taught_classes",
    )
    student_list = models.ManyToManyField(
        User, limit_choices_to={"role": "student"}, related_name="classes", blank=True
    )


class Task(models.Model):
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE, related_name="tasks"
    )
    theme = models.CharField(max_length=200)
    instruction = models.TextField(blank=True)
    delivery_date = models.DateField()
    delivery_time = models.TimeField(help_text="Hora límite de entrega", default="23:59")
    created_at = models.DateTimeField(auto_now_add=True)



class Delivery(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="delivery_list"
    )
    student = models.ForeignKey(
        User,
        limit_choices_to={"role": "student"},
        on_delete=models.CASCADE,
        related_name="deliveries"
    )
    revisor = models.ForeignKey(
        User,
        limit_choices_to={"role": "teacher"},
        on_delete=models.CASCADE,
        related_name="reviewed_deliveries"
    )
    date = models.DateField()
    delivery_time = models.TimeField(help_text="Hora de entrega", default="12:00")
    file_url = models.CharField(max_length=255)
    feedback = models.TextField(blank=True)
    file_corrected_url = models.CharField(max_length=255, blank=True)
    grade = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True, 
        blank=True, 
        help_text="Calificación numérica (0.00 - 10.00)"
    )
    
    def __str__(self):
        return f"{self.task.theme} - {self.student.name}"
    
    @property
    def is_late(self):
        """Verifica si la entrega fue tardía"""
        from datetime import datetime, time
        delivery_datetime = datetime.combine(self.date, self.delivery_time)
        deadline_datetime = datetime.combine(self.task.delivery_date, self.task.delivery_time)
        return delivery_datetime > deadline_datetime
    
    @property
    def grade_status(self):
        """Obtiene el estado de la calificación"""
        if self.grade is None:
            return "Sin calificar"
        elif self.grade >= 7.0:
            return "Aprobado"
        else:
            return "Reprobado"
    
    class Meta:
        ordering = ['-date', '-delivery_time']

