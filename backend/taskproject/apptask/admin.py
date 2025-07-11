from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SchoolClass, Task, Delivery

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
            'fields': ('email', 'name', 'username', 'role', 'password1', 'password2'),
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

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['theme', 'school_class', 'delivery_date', 'delivery_time', 'created_at']
    list_filter = ['school_class', 'delivery_date', 'created_at']
    search_fields = ['theme', 'instruction', 'school_class__identify']
    ordering = ['-created_at']
    date_hierarchy = 'delivery_date'
    
    fieldsets = (
        ('Información de la Tarea', {
            'fields': ('theme', 'instruction', 'school_class')
        }),
        ('Fechas de Entrega', {
            'fields': ('delivery_date', 'delivery_time')
        }),
    )
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('school_class', 'school_class__teacher')

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['task', 'student', 'date', 'delivery_time', 'grade', 'grade_status']
    list_filter = ['task__school_class', 'date', 'grade']
    search_fields = ['task__theme', 'student__name', 'student__email']
    ordering = ['-date', '-delivery_time']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Información de la Entrega', {
            'fields': ('task', 'student', 'revisor')
        }),
        ('Detalles de Entrega', {
            'fields': ('date', 'delivery_time', 'file_url')
        }),
        ('Calificación', {
            'fields': ('grade', 'feedback', 'file_corrected_url')
        }),
    )
    
    readonly_fields = ['grade_status']
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('task', 'student', 'revisor', 'task__school_class')
    
    def grade_status(self, obj):
        return obj.grade_status
    grade_status.short_description = 'Estado de Calificación'

# Personalización del sitio admin
admin.site.site_header = "Sistema de Gestión de Tareas"
admin.site.site_title = "Administración de Tareas"
admin.site.index_title = "Panel de Administración"