from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
import bcrypt

class User(AbstractUser):
    
    # Campos que YA EXISTEN en la base de datos
    name = models.CharField(max_length=100)  # Campo real en BD
    phone = models.CharField(max_length=15)  # Campo real en BD
    dni = models.CharField(max_length=20)    # Campo real en BD
    email = models.EmailField(max_length=254, unique=True)  # Campo real en BD
    role = models.CharField(max_length=20, default='student')  # Campo REAL en BD, no property
    
    # Validador para email institucional (solo para nuevos usuarios)
    email_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9._%+-]+@uni\.edu\.ec$',
        message='El email debe ser del dominio @uni.edu.ec'
    )
    
    ROLE_CHOICES = [
        ("student", "Estudiante"),
        ("teacher", "Docente"), 
        ("admin", "Administrador"),
        ("observer", "Observador"),
    ]
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name"]
    
    @property
    def is_institutional_email(self):
        """Verifica si el email es institucional"""
        return self.email.endswith('@uni.edu.ec') if self.email else False
    
    @property
    def role_display(self):
        """Retorna el rol en español"""
        return dict(self.ROLE_CHOICES).get(self.role, self.role)
    
    def has_role(self, role):
        """Verifica si el usuario tiene un rol específico"""
        return self.role == role
    
    @property
    def display_name(self):
        """Usar name si first_name está vacío"""
        return self.first_name or self.name or self.username
    
    def __str__(self):
        return f"{self.display_name} ({self.email}) - {self.role_display}"
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

# Mantener los modelos existentes exactamente como están
class SchoolClass(models.Model):
    identify = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='taught_classes',
        limit_choices_to={'role': 'teacher'}
    )
    student_list = models.ManyToManyField(
        User, 
        related_name='classes', 
        blank=True,
        limit_choices_to={'role': 'student'}
    )
    # Remover created_at porque no existe en la BD
    
    def __str__(self):
        return f"{self.identify} - {self.course}"
    
    class Meta:
        verbose_name = "Clase"
        verbose_name_plural = "Clases"
        # Remover ordering porque no hay created_at

class Task(models.Model):
    theme = models.CharField(max_length=200)
    instruction = models.TextField(blank=True)
    delivery_date = models.DateField()
    delivery_time = models.TimeField(default='23:59', help_text='Hora límite de entrega')
    school_class = models.ForeignKey(
        SchoolClass, 
        on_delete=models.CASCADE, 
        related_name='tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Este campo SÍ existe en la BD
    
    def __str__(self):
        return f"{self.theme} - {self.school_class.identify}"
    
    @property
    def is_overdue(self):
        now = timezone.now()
        delivery_datetime = timezone.datetime.combine(
            self.delivery_date, 
            self.delivery_time
        )
        delivery_datetime = timezone.make_aware(delivery_datetime)
        return now > delivery_datetime
    
    class Meta:
        verbose_name = "Tarea"
        verbose_name_plural = "Tareas"
        ordering = ['-created_at']

class Delivery(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='delivery_list')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deliveries')
    revisor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviewed_deliveries')
    date = models.DateField()
    delivery_time = models.TimeField(default='12:00')
    file_url = models.CharField(max_length=255)
    feedback = models.TextField(blank=True)
    grade = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    file_corrected_url = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"{self.task.theme} - {self.student.display_name}"
    
    @property
    def is_graded(self):
        return self.grade is not None
    
    @property
    def is_late(self):
        delivery_datetime = timezone.datetime.combine(self.date, self.delivery_time)
        task_datetime = timezone.datetime.combine(self.task.delivery_date, self.task.delivery_time)
        return delivery_datetime > task_datetime
    
    class Meta:
        verbose_name = "Entrega"
        verbose_name_plural = "Entregas"
        unique_together = ['task', 'student']