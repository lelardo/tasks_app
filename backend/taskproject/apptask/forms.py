from django import forms
from .models import Task, Delivery, SchoolClass, User


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['school_class', 'theme', 'instruction', 'delivery_date']
        widgets = {
            'school_class': forms.Select(attrs={'class': 'form-control'}),
            'theme': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tema de la tarea'}),
            'instruction': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Instrucciones detalladas...'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = ['student', 'file_url']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'file_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL del archivo entregado'}),
        }

    def __init__(self, *args, **kwargs):
        task = kwargs.pop('task', None)
        super().__init__(*args, **kwargs)
        if task:
            # Filtrar solo estudiantes de la clase de la tarea
            self.fields['student'].queryset = task.school_class.student_list.all()


class GradeDeliveryForm(forms.ModelForm):
    GRADE_CHOICES = [
        ('', 'Seleccionar calificación'),
        ('A', 'Excelente (A)'),
        ('B', 'Bueno (B)'),
        ('C', 'Regular (C)'),
        ('D', 'Necesita mejorar (D)'),
        ('F', 'Insuficiente (F)'),
    ]
    
    grade = forms.ChoiceField(
        choices=GRADE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = Delivery
        fields = ['feedback', 'file_corrected_url']
        widgets = {
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comentarios y retroalimentación...'}),
            'file_corrected_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL del archivo corregido (opcional)'}),
        }
