from django import forms
from .models import Task, Delivery, SchoolClass, User

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['school_class', 'theme', 'instruction', 'delivery_date', 'delivery_time', 'attachment']
        widgets = {
            'school_class': forms.Select(attrs={'class': 'form-control'}),
            'theme': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tema de la tarea'}),
            'instruction': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Instrucciones detalladas...'}),
            'delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'delivery_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control', 
                'accept': '.pdf,.doc,.docx,.txt,.zip,.rar',
                'help_text': 'Archivos permitidos: PDF, DOC, DOCX, TXT, ZIP, RAR (máximo 10MB)'
            }),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Restrict school_class queryset to the teacher's assigned classes
        if user and user.is_authenticated and user.role == 'teacher':
            self.fields['school_class'].queryset = user.taught_classes.all()
        else:
            self.fields['school_class'].queryset = SchoolClass.objects.none()
    
    def clean_attachment(self):
        """Validar archivo adjunto"""
        attachment = self.cleaned_data.get('attachment')
        
        if attachment:
            # Validar tamaño (máximo 10MB)
            if attachment.size > 10 * 1024 * 1024:  # 10MB en bytes
                raise forms.ValidationError('El archivo no puede ser mayor a 10MB.')
            
            # Validar extensión
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']
            file_extension = attachment.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError(
                    'Tipo de archivo no permitido. Use: PDF, DOC, DOCX, TXT, ZIP, RAR'
                )
        
        return attachment

class DeliveryForm(forms.ModelForm):
    class Meta:
        model = Delivery
        fields = ['attachment']
        widgets = {
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.zip,.rar',
            }),
        }

    def clean_attachment(self):
        """Validar archivo adjunto de la entrega"""
        attachment = self.cleaned_data.get('attachment')
        
        if attachment:
            # Validar tamaño (máximo 10MB)
            if attachment.size > 10 * 1024 * 1024:  # 10MB en bytes
                raise forms.ValidationError('El archivo no puede ser mayor a 10MB.')
            
            # Validar extensión
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']
            file_extension = attachment.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError(
                    'Tipo de archivo no permitido. Use: PDF, DOC, DOCX, TXT, ZIP, RAR'
                )
        else:
            raise forms.ValidationError('Debe adjuntar un archivo para la entrega.')
        
        return attachment

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
    
    send_notification = forms.BooleanField(
        label="Enviar notificación al estudiante",
        help_text="Marcar para notificar al estudiante sobre la calificación",
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Delivery
        fields = ['grade', 'feedback', 'file_corrected_url', 'corrected_attachment']
        widgets = {
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Comentarios y retroalimentación...'}),
            'file_corrected_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL del archivo corregido (opcional)'}),
            'corrected_attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt,.zip,.rar',
            }),
        }
    
    def clean_corrected_attachment(self):
        """Validar archivo adjunto corregido"""
        attachment = self.cleaned_data.get('corrected_attachment')
        
        if attachment:
            # Validar tamaño (máximo 10MB)
            if attachment.size > 10 * 1024 * 1024:  # 10MB en bytes
                raise forms.ValidationError('El archivo no puede ser mayor a 10MB.')
            
            # Validar extensión
            allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.zip', '.rar']
            file_extension = attachment.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError(
                    'Tipo de archivo no permitido. Use: PDF, DOC, DOCX, TXT, ZIP, RAR'
                )
        
        return attachment