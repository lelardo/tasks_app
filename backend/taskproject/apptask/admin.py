from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SchoolClass, Task, Delivery


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'name')
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('name', 'phone', 'dni', 'role')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {
            'fields': ('name', 'phone', 'dni', 'role', 'email')
        }),
    )


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('identify', 'course', 'teacher', 'student_count')
    list_filter = ('course', 'teacher')
    search_fields = ('identify', 'course', 'teacher__name')
    filter_horizontal = ('student_list',)
    
    def student_count(self, obj):
        return obj.student_list.count()
    student_count.short_description = 'Estudiantes'


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('theme', 'school_class', 'delivery_date', 'created_at', 'delivery_count')
    list_filter = ('school_class', 'delivery_date', 'created_at')
    search_fields = ('theme', 'instruction', 'school_class__identify')
    date_hierarchy = 'delivery_date'
    
    def delivery_count(self, obj):
        return obj.delivery_list.count()
    delivery_count.short_description = 'Entregas'


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('task', 'student', 'date', 'has_feedback', 'revisor')
    list_filter = ('date', 'task__school_class', 'revisor')
    search_fields = ('task__theme', 'student__name', 'feedback')
    date_hierarchy = 'date'
    
    def has_feedback(self, obj):
        return bool(obj.feedback)
    has_feedback.boolean = True
    has_feedback.short_description = 'Calificada'
