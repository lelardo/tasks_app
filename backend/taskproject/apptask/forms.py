from django import forms
from .models import Task, Delivery, SchoolClass, User

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['school_class', 'theme', 'instruction', 'delivery_date', 'delivery_time']
        widgets = {
            'school_class': forms.Select(attrs={'class': 'form-control'}),
            'theme': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tema de la tarea'}),
            'instruction': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Instrucciones detalladas...'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'delivery_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
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
    grade = forms.DecimalField(
        min_value=0.00,
        max_value=10.00,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'max': '10',
            'placeholder': 'Ej: 8.75'
        }),
        help_text="Calificación del 0.00 al 10.00",
        required=False
    )
    
    class Meta:
        model = Delivery
        fields = ['grade', 'feedback', 'file_corrected_url']
        widgets = {
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Comentarios y retroalimentación...'}),
            'file_corrected_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL del archivo corregido (opcional)'}),
        }