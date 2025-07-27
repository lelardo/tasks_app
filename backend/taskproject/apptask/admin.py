from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SchoolClass, Task, Delivery, Group, SessionConfig


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'name', 'role', 'is_active', 'date_joined']
    list_filter = ['is_active', 'date_joined', 'is_staff']
    search_fields = ['email', 'name', 'username']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('name', 'username', 'first_name', 'last_name', 'phone', 'dni')}),
        ('Rol y Permisos', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'username', 'role', 'dni', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined']

@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ['identify', 'course', 'teacher']
    list_filter = ['teacher']
    search_fields = ['identify', 'course', 'teacher__name']
    filter_horizontal = ['student_list']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('teacher')

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'school_class', 'member_count', 'created_at']
    list_filter = ['school_class', 'created_at']
    search_fields = ['name', 'school_class__identify']
    filter_horizontal = ['students']
    ordering = ['school_class', 'name']
    
    def member_count(self, obj):
        return obj.students.count()
    member_count.short_description = 'Miembros'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('school_class').prefetch_related('students')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['theme', 'school_class', 'task_type', 'delivery_date', 'delivery_time', 'created_at']
    list_filter = ['school_class', 'is_group_task', 'delivery_date', 'created_at']
    search_fields = ['theme', 'instruction', 'school_class__identify']
    ordering = ['-created_at']
    date_hierarchy = 'delivery_date'
    
    fieldsets = (
        ('Información de la Tarea', {
            'fields': ('theme', 'instruction', 'school_class')
        }),
        ('Configuración de Grupo', {
            'fields': ('is_group_task', 'group'),
            'classes': ('collapse',)
        }),
        ('Fechas de Entrega', {
            'fields': ('delivery_date', 'delivery_time')
        }),
    )
    
    def task_type(self, obj):
        if obj.is_group_task:
            return f"Grupal ({obj.group.name if obj.group else 'Sin grupo'})"
        return "Individual"
    task_type.short_description = 'Tipo'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('school_class', 'school_class__teacher', 'group')

@admin.register(SessionConfig)
class SessionConfigAdmin(admin.ModelAdmin):
    list_display = ['session_timeout_minutes', 'enable_session_timeout', 'show_timeout_warning', 'warning_time_minutes', 'updated_at']
    list_editable = ['enable_session_timeout', 'show_timeout_warning']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Configuración de Timeout', {
            'fields': ('session_timeout_minutes', 'enable_session_timeout')
        }),
        ('Configuración de Advertencias', {
            'fields': ('show_timeout_warning', 'warning_time_minutes')
        }),
        ('Información del Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Solo permitir una instancia de configuración
        return not SessionConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuración
        return False

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['task', 'student', 'delivery_type', 'date', 'delivery_time', 'grade', 'grade_status']
    list_filter = ['task__school_class', 'is_group_delivery', 'date', 'grade']
    search_fields = ['task__theme', 'student__name', 'student__email']
    ordering = ['-date', '-delivery_time']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Información de la Entrega', {
            'fields': ('task', 'student', 'revisor')
        }),
        ('Configuración de Grupo', {
            'fields': ('is_group_delivery', 'group'),
            'classes': ('collapse',)
        }),
        ('Detalles de Entrega', {
            'fields': ('date', 'delivery_time', 'file_url')
        }),
        ('Calificación', {
            'fields': ('grade', 'feedback', 'file_corrected_url')
        }),
    )
    
    readonly_fields = ['grade_status']
    
    def delivery_type(self, obj):
        if obj.is_group_delivery:
            return f"Grupal ({obj.group.name if obj.group else 'Sin grupo'})"
        return "Individual"
    delivery_type.short_description = 'Tipo'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('task', 'student', 'revisor', 'task__school_class', 'group')
    
    def grade_status(self, obj):
        return obj.grade_status
    grade_status.short_description = 'Estado de Calificación'

# Personalización del sitio admin
admin.site.site_header = "Sistema de Gestión de Tareas"
admin.site.site_title = "Administración de Tareas"
admin.site.index_title = "Panel de Administración"