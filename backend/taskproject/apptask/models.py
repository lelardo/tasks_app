from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import bcrypt

def validate_cedula_ecuatoriana(value):
    """Validador para cédula ecuatoriana"""
    if not value or len(value) != 10:
        raise ValidationError('La cédula debe tener exactamente 10 dígitos.')
    
    if not value.isdigit():
        raise ValidationError('La cédula solo debe contener números.')
    
    # Algoritmo de validación de cédula ecuatoriana
    cedula = [int(d) for d in value]
    provincia = int(value[:2])
    
    if provincia < 1 or provincia > 24:
        raise ValidationError('Los dos primeros dígitos deben corresponder a una provincia válida (01-24).')
    
    # Validar dígito verificador
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
    
    for i in range(9):
        producto = cedula[i] * coeficientes[i]
        if producto > 9:
            producto -= 9
        suma += producto
    
    digito_verificador = (10 - (suma % 10)) % 10
    
    if cedula[9] != digito_verificador:
        raise ValidationError('La cédula ingresada no es válida.')
    
    return value


class User(AbstractUser):
    # Campos existentes
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    dni = models.CharField(
        max_length=10, 
        unique=True,
        # validators=[validate_cedula_ecuatoriana],  # Quitar esta línea
        help_text='Cédula de 10 dígitos'  # Cambiar texto
    )

    ROLE_CHOICES = [
        ("student", "Estudiante"),
        ("teacher", "Docente"), 
        ("admin", "Administrador"),
        ("observer", "Observador"),
    ]

    email = models.EmailField(max_length=254, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    
    # Campos para recuperación de contraseña
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_expires = models.DateTimeField(blank=True, null=True)
    
    # Validador para email institucional
    email_validator = RegexValidator(
        regex=r'^[a-zA-Z0-9._%+-]+@uni\.edu\.ec$',
        message='El email debe ser del dominio @uni.edu.ec'
    )
    
    
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "dni"]
    
    class Meta:
        db_table = 'apptask_user'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def clean(self):
        super().clean()
        # Validar email institucional
        if self.email and not self.email.endswith('@uni.edu.ec'):
            raise ValidationError({'email': 'El email debe ser del dominio @uni.edu.ec'})
        
        # Quitar validación de cédula
        # if self.dni:
        #     validate_cedula_ecuatoriana(self.dni)
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def display_name(self):
        return self.name or f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def role_display(self):
        return dict(self.ROLE_CHOICES).get(self.role, 'Sin rol')
    
    def generate_password_reset_token(self):
        """Genera token para recuperación de contraseña"""
        import secrets
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        token = secrets.token_urlsafe(32)
        self.password_reset_token = token
        self.password_reset_expires = timezone.now() + timedelta(hours=1)  # Expira en 1 hora
        self.save()
        return token
    
    def is_password_reset_token_valid(self, token):
        """Verifica si el token de recuperación es válido"""
        from django.utils import timezone
        
        return (
            self.password_reset_token == token and
            self.password_reset_expires and
            timezone.now() < self.password_reset_expires
        )
    
    def clear_password_reset_token(self):
        """Limpia el token de recuperación"""
        self.password_reset_token = None
        self.password_reset_expires = None
        self.save()

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