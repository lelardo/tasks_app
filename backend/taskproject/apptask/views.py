def student_required(user):
    """Verifica que el usuario sea estudiante"""
    return user.is_authenticated and user.role == 'student'

from django.utils.timezone import now
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

# ...existing code...

@login_required
@user_passes_test(student_required)
def student_task_report(request, task_id):
    """Genera un reporte sencillo de la tarea para el estudiante"""
    student = request.user
    task = get_object_or_404(Task, id=task_id, school_class__student_list=student)
    try:
        my_delivery = Delivery.objects.get(task=task, student=student)
    except Delivery.DoesNotExist:
        my_delivery = None
    context = {
        'task': task,
        'my_delivery': my_delivery,
        'report_date': now(),
    }
    return render(request, 'apptask/student/task_report.html', context)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db import models
from django.core.paginator import Paginator
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
from .models import Task, Delivery, SchoolClass, User
from .forms import TaskForm, DeliveryForm, GradeDeliveryForm
from django import forms
from django.db.models import Count, Avg, Q, F
from django.http import JsonResponse, HttpResponse
import csv
import json
from datetime import datetime, timedelta
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer,
    UserProfileSerializer,
    UserListSerializer
)
from django.contrib.auth.hashers import make_password
import secrets
import string
from django.core.exceptions import ValidationError
from apptask.models import SchoolClass

# class TaskForm(forms.ModelForm):
#     class Meta:
#         model = Task
#         fields = ['theme', 'instruction', 'school_class', 'delivery_date', 'delivery_time']
#         widgets = {
#             'delivery_date': forms.DateInput(attrs={'type': 'date'}),
#             'delivery_time': forms.TimeInput(attrs={'type': 'time'}),
#             'instruction': forms.Textarea(attrs={'rows': 5}),
#         }

# === DECORADORES PERSONALIZADOS ===
def admin_required(user):
    """Verifica que el usuario sea administrador"""
    return user.is_authenticated and user.role == 'admin'

def teacher_required(user):
    """Verifica que el usuario sea docente"""
    return user.is_authenticated and user.role == 'teacher'

def student_required(user):
    """Verifica que el usuario sea estudiante"""
    return user.is_authenticated and user.role == 'student'

def teacher_or_admin_required(user):
    """Verifica que el usuario sea docente o administrador"""
    return user.is_authenticated and user.role in ['teacher', 'admin']

# === VISTA PRINCIPAL CON REDIRECCIÓN POR ROL ===
def home(request):
    """Vista principal que redirige según autenticación y rol"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Redirigir según el rol del usuario
    if request.user.role == 'admin':
        return redirect('admin_dashboard')  # Ir directamente al panel completo
    elif request.user.role == 'teacher':
        return redirect('teacher_dashboard')
    elif request.user.role == 'student':
        return redirect('student_dashboard')
    elif request.user.role == 'observer':  # NUEVO
        return redirect('observer_dashboard')
    
    else:
        # Para usuarios sin rol específico, mostrar dashboard general
        context = {
            'user': request.user,
            'user_role': request.user.role if hasattr(request.user, 'role') else 'none',
        }
        return render(request, 'apptask/home.html', context)
    
# === VISTAS ESPECÍFICAS POR ROL ===

# DASHBOARDS POR ROL
@login_required
@user_passes_test(admin_required)
def admin_dashboard(request):
    """Dashboard para administradores - OPTIMIZADO"""
    # Usar agregación para obtener todos los contadores en una sola consulta
    from django.db.models import Count, Q
    
    # Estadísticas de usuarios optimizada con agregación
    user_stats = User.objects.aggregate(
        total_users=Count('id'),
        total_students=Count('id', filter=Q(role='student')),
        total_teachers=Count('id', filter=Q(role='teacher')),
        total_admins=Count('id', filter=Q(role='admin'))
    )
    
    # Contar clases y tareas
    total_classes = SchoolClass.objects.count()
    total_tasks = Task.objects.count()
    
    # Obtener datos recientes con select_related para evitar consultas adicionales
    recent_users = User.objects.select_related().order_by('-date_joined')[:5]
    recent_classes = SchoolClass.objects.select_related('teacher').order_by('-id')[:5]
    
    context = {
        'total_users': user_stats['total_users'] or 0,
        'total_students': user_stats['total_students'] or 0,
        'total_teachers': user_stats['total_teachers'] or 0,
        'total_admins': user_stats['total_admins'] or 0,
        'total_classes': total_classes,
        'total_tasks': total_tasks,
        'recent_users': recent_users,
        'recent_classes': recent_classes,
    }
    return render(request, 'apptask/admin/dashboard.html', context)

@login_required
@user_passes_test(teacher_required)
def create_task(request):
    """Crear una nueva tarea (solo docentes) - CON SOPORTE PARA ARCHIVOS"""
    if request.method == 'POST':
        form = TaskForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            try:
                task = form.save(commit=False)
                task.created_at = timezone.now()
                task.save()
                
                # Mensaje de éxito con información del archivo si se adjuntó
                if task.attachment:
                    messages.success(
                        request, 
                        f'Tarea creada exitosamente con archivo adjunto: {task.attachment_name}'
                    )
                else:
                    messages.success(request, 'Tarea creada exitosamente.')
                
                return redirect('teacher_task_list')
            except Exception as e:
                messages.error(request, f'Error al crear la tarea: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = TaskForm(user=request.user)
    
    # Check if the teacher has assigned classes for template compatibility
    assigned_classes = request.user.taught_classes.all()
    if not assigned_classes:
        messages.error(request, 'No tienes clases asignadas. Contacta al administrador.')
    
    return render(request, 'apptask/teacher/task_form.html', {
        'form': form,
        'title': 'Crear Nueva Tarea',
        'assigned_classes': assigned_classes,  # For template compatibility
    })

@login_required
@user_passes_test(teacher_required)
def teacher_dashboard(request):
    """Dashboard principal para docentes - OPTIMIZADO"""
    teacher = request.user
    
    # Optimizar consultas con select_related y prefetch_related
    # Obtener las clases del docente con estudiantes precargados
    my_classes = teacher.taught_classes.prefetch_related('student_list').all()
    
    # Obtener tareas del docente con clases precargadas
    teacher_tasks = Task.objects.filter(
        school_class__teacher=teacher
    ).select_related('school_class').order_by('-created_at')[:5]
    
    # Obtener entregas para revisar con datos relacionados precargados
    teacher_deliveries = Delivery.objects.filter(
        task__school_class__teacher=teacher
    ).select_related(
        'task', 'task__school_class', 'student'
    ).order_by('-date')[:10]
    
    # Optimizar estadísticas usando una sola consulta por tabla
    # Usar agregación para evitar múltiples consultas
    from django.db.models import Count, Q
    
    # Estadísticas de tareas
    task_stats = Task.objects.filter(
        school_class__teacher=teacher
    ).aggregate(
        total_tasks=Count('id')
    )
    
    # Estadísticas de entregas
    delivery_stats = Delivery.objects.filter(
        task__school_class__teacher=teacher
    ).aggregate(
        total_deliveries=Count('id'),
        pending_deliveries=Count('id', filter=Q(feedback='')),
        graded_deliveries=Count('id', filter=~Q(feedback=''))
    )
    
    context = {
        'my_classes': my_classes,
        'tasks': teacher_tasks,
        'recent_deliveries': teacher_deliveries,
        'total_tasks': task_stats['total_tasks'] or 0,
        'total_deliveries': delivery_stats['total_deliveries'] or 0,
        'pending_deliveries': delivery_stats['pending_deliveries'] or 0,
        'graded_deliveries': delivery_stats['graded_deliveries'] or 0,
    }
    
    # Usar el template específico para docentes
    return render(request, 'apptask/teacher/dashboard.html', context)

@login_required
@user_passes_test(student_required)
def student_dashboard(request):
    """Dashboard principal para estudiantes - OPTIMIZADO"""
    student = request.user
    
    # Obtener las clases en las que está inscrito el estudiante con teachers precargados
    my_classes = student.classes.select_related('teacher').all()
    
    # Obtener tareas disponibles para el estudiante con datos relacionados
    available_tasks = Task.objects.filter(
        school_class__student_list=student
    ).select_related('school_class', 'school_class__teacher').order_by('-created_at')
    
    # Obtener entregas del estudiante con datos relacionados precargados
    my_deliveries = Delivery.objects.filter(
        student=student
    ).select_related('task', 'task__school_class').order_by('-date')
    
    # Tareas pendientes optimizado - usar EXISTS para mejor rendimiento
    delivered_task_ids = list(my_deliveries.values_list('task_id', flat=True))
    pending_tasks = available_tasks.exclude(id__in=delivered_task_ids) if delivered_task_ids else available_tasks
    
    # Estadísticas optimizadas usando agregación y conteo eficiente
    from django.db.models import Count, Q
    
    # Contar solo una vez cada cosa
    total_classes = my_classes.count()
    total_available_tasks = available_tasks.count()
    
    # Estadísticas de entregas en una sola consulta
    delivery_stats = my_deliveries.aggregate(
        total_deliveries=Count('id'),
        graded_count=Count('id', filter=Q(grade__isnull=False))
    )
    
    total_deliveries = delivery_stats['total_deliveries'] or 0
    graded_count = delivery_stats['graded_count'] or 0
    pending_count = pending_tasks.count()
    
    # Calcular porcentaje de completado (evitar división por cero)
    completion_percentage = 0
    if total_available_tasks > 0:
        completion_percentage = round((graded_count * 100) / total_available_tasks, 1)
    
    # Obtener notificaciones no leídas del estudiante
    from .models import Notification
    unread_notifications = Notification.objects.filter(
        student=student,
        is_read=False
    ).order_by('-created_at')[:5]  # Últimas 5 notificaciones no leídas
    
    context = {
        'my_classes': my_classes,
        'available_tasks': available_tasks[:5],  # Últimas 5 tareas
        'pending_tasks': pending_tasks[:5],      # 5 tareas pendientes
        'my_deliveries': my_deliveries[:5],      # Últimas 5 entregas
        'unread_notifications': unread_notifications,  # Notificaciones no leídas
        'total_classes': total_classes,
        'total_available_tasks': total_available_tasks,
        'total_deliveries': total_deliveries,
        'pending_count': pending_count,
        'graded_count': graded_count,
        'completion_percentage': completion_percentage,
    }
    
    return render(request, 'apptask/student/dashboard.html', context)

@login_required
@user_passes_test(student_required)
def student_notifications(request):
    """Vista para mostrar todas las notificaciones del estudiante"""
    student = request.user
    from .models import Notification
    
    # Obtener todas las notificaciones del estudiante
    notifications = Notification.objects.filter(
        student=student
    ).order_by('-created_at')
    
    # Marcar todas como leídas cuando el estudiante las vea
    notifications.filter(is_read=False).update(is_read=True)
    
    context = {
        'notifications': notifications,
    }
    
    return render(request, 'apptask/student/notifications.html', context)

@login_required
@user_passes_test(student_required)
def mark_notification_read(request, notification_id):
    """Marcar una notificación específica como leída"""
    student = request.user
    from .models import Notification
    
    try:
        notification = Notification.objects.get(
            id=notification_id,
            student=student
        )
        notification.is_read = True
        notification.save()
    except Notification.DoesNotExist:
        pass
    
    return redirect('student_notifications')

@login_required
@user_passes_test(student_required)
def student_grades(request):
    """Vista para mostrar todas las calificaciones del estudiante organizadas por clase"""
    student = request.user
    from django.db.models import Avg, Count, Q
    
    # Obtener todas las clases del estudiante con estadísticas
    classes_with_grades = []
    for school_class in student.classes.all():
        # Obtener todas las tareas de esta clase
        class_tasks = Task.objects.filter(school_class=school_class)
        
        # Obtener entregas calificadas del estudiante en esta clase
        graded_deliveries = Delivery.objects.filter(
            student=student,
            task__school_class=school_class,
            grade__isnull=False
        ).select_related('task').order_by('-date')
        
        # Calcular estadísticas
        total_tasks = class_tasks.count()
        total_graded = graded_deliveries.count()
        
        # Calcular promedio
        avg_grade = graded_deliveries.aggregate(
            average=Avg('grade')
        )['average'] or 0
        
        # Calcular distribución de notas
        excellent_count = graded_deliveries.filter(grade__gte=9).count()
        good_count = graded_deliveries.filter(grade__gte=7, grade__lt=9).count()
        average_count = graded_deliveries.filter(grade__gte=5, grade__lt=7).count()
        poor_count = graded_deliveries.filter(grade__lt=5).count()
        
        # Calcular porcentaje de completado
        completion_rate = (total_graded / total_tasks * 100) if total_tasks > 0 else 0
        
        classes_with_grades.append({
            'class': school_class,
            'total_tasks': total_tasks,
            'total_graded': total_graded,
            'avg_grade': round(avg_grade, 2),
            'completion_rate': round(completion_rate, 1),
            'graded_deliveries': graded_deliveries[:10],  # Últimas 10 calificaciones
            'excellent_count': excellent_count,
            'good_count': good_count,
            'average_count': average_count,
            'poor_count': poor_count,
        })
    
    # Estadísticas generales del estudiante
    total_deliveries = Delivery.objects.filter(student=student, grade__isnull=False)
    overall_avg = total_deliveries.aggregate(avg=Avg('grade'))['avg'] or 0
    
    context = {
        'classes_with_grades': classes_with_grades,
        'overall_avg': round(overall_avg, 2),
        'total_classes': len(classes_with_grades),
    }
    
    return render(request, 'apptask/student/grades.html', context)

@login_required
@user_passes_test(student_required)
def student_class_grades(request, class_id):
    """Vista detallada de calificaciones para una clase específica"""
    student = request.user
    
    # Verificar que el estudiante esté inscrito en esta clase
    school_class = get_object_or_404(
        SchoolClass, 
        id=class_id, 
        student_list=student
    )
    
    # Obtener todas las tareas de esta clase
    class_tasks = Task.objects.filter(school_class=school_class).order_by('-created_at')
    
    # Obtener entregas del estudiante en esta clase
    deliveries_dict = {}
    for delivery in Delivery.objects.filter(student=student, task__school_class=school_class):
        deliveries_dict[delivery.task.id] = delivery
    
    # Crear lista con tareas y sus respectivas entregas
    tasks_with_deliveries = []
    for task in class_tasks:
        delivery = deliveries_dict.get(task.id)
        tasks_with_deliveries.append({
            'task': task,
            'delivery': delivery,
            'status': 'graded' if delivery and delivery.grade is not None else 
                     'submitted' if delivery else 'pending'
        })
    
    # Calcular estadísticas de la clase
    graded_deliveries = [d for d in deliveries_dict.values() if d.grade is not None]
    
    if graded_deliveries:
        grades = [d.grade for d in graded_deliveries]
        avg_grade = sum(grades) / len(grades)
        highest_grade = max(grades)
        lowest_grade = min(grades)
    else:
        avg_grade = highest_grade = lowest_grade = 0
    
    # Calcular tendencia (últimas 5 calificaciones)
    recent_grades = sorted(graded_deliveries, key=lambda x: x.date)[-5:]
    trend = "stable"
    if len(recent_grades) >= 3:
        first_half_avg = sum(d.grade for d in recent_grades[:len(recent_grades)//2]) / len(recent_grades[:len(recent_grades)//2])
        second_half_avg = sum(d.grade for d in recent_grades[len(recent_grades)//2:]) / len(recent_grades[len(recent_grades)//2:])
        
        if second_half_avg > first_half_avg + 0.5:
            trend = "improving"
        elif second_half_avg < first_half_avg - 0.5:
            trend = "declining"
    
    context = {
        'school_class': school_class,
        'tasks_with_deliveries': tasks_with_deliveries,
        'total_tasks': len(tasks_with_deliveries),
        'graded_count': len(graded_deliveries),
        'avg_grade': round(avg_grade, 2),
        'highest_grade': highest_grade,
        'lowest_grade': lowest_grade,
        'completion_rate': round((len(graded_deliveries) / len(tasks_with_deliveries) * 100), 1) if tasks_with_deliveries else 0,
        'trend': trend,
        'recent_grades': recent_grades,
    }
    
    return render(request, 'apptask/student/class_grades.html', context)

@login_required
@user_passes_test(student_required)
def student_grade_report(request, class_id):
    """Generar reporte de rendimiento del estudiante en una clase específica"""
    student = request.user
    from django.http import HttpResponse
    from datetime import datetime
    import json
    
    # Verificar que el estudiante esté inscrito en esta clase
    school_class = get_object_or_404(
        SchoolClass, 
        id=class_id, 
        student_list=student
    )
    
    # Obtener todas las entregas calificadas del estudiante en esta clase
    graded_deliveries = Delivery.objects.filter(
        student=student,
        task__school_class=school_class,
        grade__isnull=False
    ).select_related('task').order_by('date')
    
    if request.GET.get('format') == 'json':
        # Retornar datos en JSON para gráficos
        data = {
            'class_info': {
                'name': school_class.identify,
                'course': school_class.course,
                'teacher': school_class.teacher.display_name,
            },
            'student_info': {
                'name': student.display_name,
                'email': student.email,
            },
            'grades': [
                {
                    'task': delivery.task.theme,
                    'grade': float(delivery.grade),
                    'date': delivery.date.strftime('%Y-%m-%d'),
                    'feedback': delivery.feedback,
                }
                for delivery in graded_deliveries
            ],
            'statistics': {
                'total_graded': len(graded_deliveries),
                'average': round(sum(d.grade for d in graded_deliveries) / len(graded_deliveries), 2) if graded_deliveries else 0,
                'highest': max(d.grade for d in graded_deliveries) if graded_deliveries else 0,
                'lowest': min(d.grade for d in graded_deliveries) if graded_deliveries else 0,
            }
        }
        return HttpResponse(json.dumps(data), content_type='application/json')
    
    # Generar reporte HTML
    context = {
        'student': student,
        'school_class': school_class,
        'graded_deliveries': graded_deliveries,
        'report_date': datetime.now(),
    }
    
    return render(request, 'apptask/student/grade_report.html', context)

@login_required
@user_passes_test(student_required)
def student_class_detail(request, class_id):
    """Vista detallada de una clase específica para estudiantes"""
    student = request.user
    
    # Verificar que el estudiante esté inscrito en esta clase
    school_class = get_object_or_404(
        SchoolClass, 
        id=class_id, 
        student_list=student
    )
    
    # Obtener todas las tareas de esta clase
    tasks = Task.objects.filter(school_class=school_class).order_by('-created_at')
    
    # Obtener entregas del estudiante para esta clase
    deliveries = Delivery.objects.filter(
        student=student,
        task__school_class=school_class
    ).select_related('task')
    
    # Crear un diccionario para mapear tareas con entregas
    delivery_map = {delivery.task.id: delivery for delivery in deliveries}
    
    # Crear lista combinada de tareas con información de entrega
    tasks_with_delivery = []
    for task in tasks:
        delivery = delivery_map.get(task.id)
        tasks_with_delivery.append({
            'task': task,
            'delivery': delivery,
            'has_delivered': delivery is not None,
            'is_graded': delivery and delivery.grade is not None,
            'is_late': delivery and delivery.is_late if delivery else False,
        })
    
    # Calcular estadísticas de la clase
    total_tasks = tasks.count()
    delivered_tasks = deliveries.count()
    graded_deliveries = deliveries.filter(grade__isnull=False)
    graded_count = graded_deliveries.count()
    
    # Calcular promedio de calificaciones
    avg_grade = graded_deliveries.aggregate(
        average=models.Avg('grade')
    )['average'] or 0
    
    # Calcular distribución de notas
    excellent_count = graded_deliveries.filter(grade__gte=9).count()
    good_count = graded_deliveries.filter(grade__gte=7, grade__lt=9).count()
    average_count = graded_deliveries.filter(grade__gte=5, grade__lt=7).count()
    poor_count = graded_deliveries.filter(grade__lt=5).count()
    
    # Tareas pendientes (no entregadas y no vencidas)
    pending_tasks = []
    for task in tasks:
        if task.id not in delivery_map and not task.is_overdue:
            pending_tasks.append(task)
    
    # Tareas próximas a vencer (en los próximos 3 días)
    upcoming_tasks = []
    for task in pending_tasks:
        days_until_due = (task.delivery_date - timezone.now().date()).days
        if 0 <= days_until_due <= 3:
            upcoming_tasks.append({
                'task': task,
                'days_until_due': days_until_due
            })
    
    context = {
        'school_class': school_class,
        'tasks_with_delivery': tasks_with_delivery,
        'total_tasks': total_tasks,
        'delivered_tasks': delivered_tasks,
        'graded_count': graded_count,
        'avg_grade': round(avg_grade, 2),
        'completion_rate': round((delivered_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1),
        'grading_rate': round((graded_count / delivered_tasks * 100) if delivered_tasks > 0 else 0, 1),
        'pending_tasks': pending_tasks[:5],  # Mostrar solo las 5 más recientes
        'upcoming_tasks': upcoming_tasks,
        'excellent_count': excellent_count,
        'good_count': good_count,
        'average_count': average_count,
        'poor_count': poor_count,
        'graded_deliveries': graded_deliveries.order_by('-date')[:10],  # Últimas 10 calificaciones
    }
    
    return render(request, 'apptask/student/class_detail.html', context)

@login_required
@user_passes_test(student_required)
def student_task_detail(request, task_id):
    """Vista de detalle de tarea específica para estudiantes"""
    student = request.user
    
    # Verificar que el estudiante esté inscrito en la clase de esta tarea
    task = get_object_or_404(
        Task, 
        id=task_id, 
        school_class__student_list=student
    )
    
    # Verificar si el estudiante ya entregó esta tarea
    try:
        my_delivery = Delivery.objects.get(task=task, student=student)
    except Delivery.DoesNotExist:
        my_delivery = None
    
    # Obtener todas las entregas (solo para ver estadísticas)
    all_deliveries = task.delivery_list.all()
    
    context = {
        'task': task,
        'my_delivery': my_delivery,
        'total_deliveries': all_deliveries.count(),
        'total_students': task.school_class.student_list.count(),
        'can_deliver': not my_delivery and not task.is_overdue,
        'can_edit': my_delivery and not task.is_overdue,  # Nueva variable
    }
    
    return render(request, 'apptask/student/task_detail.html', context)

@login_required
@user_passes_test(student_required)
@login_required
@user_passes_test(student_required)
def student_delivery_create(request, task_id):
    """Crear entrega para una tarea específica (solo estudiantes)"""
    student = request.user
    
    # Verificar que el estudiante esté inscrito en la clase
    task = get_object_or_404(
        Task, 
        id=task_id, 
        school_class__student_list=student
    )
    
    # Verificar que no haya entregado ya
    if Delivery.objects.filter(task=task, student=student).exists():
        messages.error(request, 'Ya has entregado esta tarea.')
        return redirect('student_task_detail', task_id=task.id)
    
    # Verificar que la tarea no esté vencida
    if task.is_overdue:
        messages.error(request, 'Esta tarea ya está vencida.')
        return redirect('student_task_detail', task_id=task.id)
    
    if request.method == 'POST':
        form = DeliveryForm(request.POST, request.FILES)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.task = task
            delivery.student = student
            delivery.revisor = task.school_class.teacher
            delivery.date = timezone.now().date()
            delivery.delivery_time = timezone.now().time()
            delivery.save()
            
            messages.success(request, f'Tarea "{task.theme}" entregada exitosamente.')
            return redirect('student_task_detail', task_id=task.id)
    else:
        form = DeliveryForm()
    
    return render(request, 'apptask/student/delivery_form.html', {
        'task': task,
        'form': form,
        'title': 'Entregar Tarea'
    })

@login_required
@user_passes_test(student_required)
def student_delivery_edit(request, delivery_id):
    """Editar entrega de un estudiante (solo archivos)"""
    student = request.user
    
    # Verificar que la entrega pertenezca al estudiante
    delivery = get_object_or_404(
        Delivery, 
        id=delivery_id, 
        student=student
    )
    
    # Verificar que la tarea no esté vencida
    if delivery.task.is_overdue:
        messages.error(request, 'No puedes modificar entregas de tareas vencidas.')
        return redirect('student_task_detail', task_id=delivery.task.id)
    
    if request.method == 'POST':
        form = DeliveryForm(request.POST, request.FILES, instance=delivery)
        if form.is_valid():
            # Actualizar fecha y hora de entrega
            delivery = form.save(commit=False)
            delivery.date = timezone.now().date()
            delivery.delivery_time = timezone.now().time()
            delivery.save()
            
            messages.success(request, f'Entrega actualizada exitosamente.')
            return redirect('student_task_detail', task_id=delivery.task.id)
    else:
        form = DeliveryForm(instance=delivery)
    
    return render(request, 'apptask/student/delivery_edit.html', {
        'delivery': delivery,
        'task': delivery.task,
        'form': form,
        'title': 'Modificar Entrega'
    })

@login_required
@user_passes_test(teacher_required)
def student_delivery_list(request):
    """Lista de entregas del estudiante"""
    student = request.user
    
    # Obtener todas las entregas del estudiante
    deliveries = Delivery.objects.filter(student=student).order_by('-date', '-delivery_time')
    
    # Filtros
    status_filter = request.GET.get('status')
    if status_filter == 'graded':
        deliveries = deliveries.exclude(feedback='')
    elif status_filter == 'pending':
        deliveries = deliveries.filter(feedback='')
    
    # Estadísticas
    total_deliveries = deliveries.count()
    graded_deliveries = deliveries.exclude(feedback='').count()
    pending_deliveries = deliveries.filter(feedback='').count()
    
    context = {
        'deliveries': deliveries,
        'current_status': status_filter,
        'total_deliveries': total_deliveries,
        'graded_deliveries': graded_deliveries,
        'pending_deliveries': pending_deliveries,
    }
    
    return render(request, 'apptask/student/delivery_list.html', context)

@login_required
@user_passes_test(teacher_required)
def teacher_delivery_list(request):
    """Lista de entregas para el docente"""
    teacher = request.user
    
    # Obtener todas las entregas de las tareas asignadas al docente
    deliveries = Delivery.objects.filter(task__school_class__teacher=teacher).order_by('-date', '-delivery_time')
    
    # Filtros
    status_filter = request.GET.get('status')
    if status_filter == 'pending':
        deliveries = deliveries.filter(feedback='')
    elif status_filter == 'graded':
        deliveries = deliveries.exclude(feedback='')
    
    context = {
        'deliveries': deliveries,
        'current_status': status_filter,
    }
    return render(request, 'apptask/teacher/delivery_list.html', context)

@login_required
@user_passes_test(teacher_required)
def teacher_delivery_grade(request, delivery_id):
    """Calificar entrega (solo docentes)"""
    teacher = request.user
    delivery = get_object_or_404(
        Delivery, 
        id=delivery_id, 
        task__school_class__teacher=teacher
    )
    
    if request.method == 'POST':
        form = GradeDeliveryForm(request.POST, request.FILES, instance=delivery)
        if form.is_valid():
            # Verificar si es una modificación de calificación existente
            was_previously_graded = delivery.grade is not None
            
            delivery = form.save()
            
            # Crear notificación si el switch está marcado
            send_notification = form.cleaned_data.get('send_notification', False)
            if send_notification:
                from .models import Notification
                
                if was_previously_graded:
                    message = f"Tu calificación para '{delivery.task.theme}' ha sido modificada. Nueva calificación: {delivery.grade}/10"
                else:
                    message = f"Tu entrega para '{delivery.task.theme}' ha sido calificada. Calificación: {delivery.grade}/10"
                
                # Crear la notificación
                Notification.objects.create(
                    student=delivery.student,
                    delivery=delivery,
                    message=message
                )
            
            messages.success(request, f'Entrega de {delivery.student.display_name} calificada exitosamente.')
            return redirect('teacher_task_detail', task_id=delivery.task.id)
    else:
        form = GradeDeliveryForm(instance=delivery)
    
    return render(request, 'apptask/teacher/grade_delivery.html', {
        'form': form,
        'delivery': delivery,
        'title': 'Calificar Entrega',
        'is_edit': bool(delivery.feedback)
    })

# === GESTIÓN DE USUARIOS (SOLO ADMIN) ===
@login_required
@user_passes_test(admin_required)
def admin_user_list(request):
    """Lista de usuarios para administradores"""
    users = User.objects.all().order_by('-date_joined')
    
    # Filtros
    role_filter = request.GET.get('role')
    search = request.GET.get('search')
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if search:
        users = users.filter(
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search) |
            models.Q(name__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    context = {
        'users': users,
        'role_choices': User.ROLE_CHOICES,
        'current_role': role_filter,
        'current_search': search,
    }
    return render(request, 'apptask/admin/user_list.html', context)

@login_required
@user_passes_test(admin_required)
def admin_user_create(request):
    """Crear nuevo usuario (solo admin)"""
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        name = request.POST.get('name')
        username = request.POST.get('username')
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        dni = request.POST.get('dni')
        password = request.POST.get('password')
        
        # Validaciones
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Ya existe un usuario con este email.')
            return render(request, 'apptask/admin/user_form.html', {
                'role_choices': User.ROLE_CHOICES,
                'form_data': request.POST
            })
        
        if not email.endswith('@uni.edu.ec'):
            messages.error(request, 'El email debe ser del dominio @uni.edu.ec')
            return render(request, 'apptask/admin/user_form.html', {
                'role_choices': User.ROLE_CHOICES,
                'form_data': request.POST
            })
        
        try:
            user = User.objects.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                name=name or first_name,
                username=username,
                role=role,
                phone=phone,
                dni=dni,
                is_active=True
            )
            user.set_password(password)
            user.save()
            
            messages.success(request, f'Usuario {user.email} creado exitosamente.')
            return redirect('admin_user_list')
            
        except Exception as e:
            messages.error(request, f'Error al crear usuario: {str(e)}')
    
    context = {
        'role_choices': User.ROLE_CHOICES,
        'title': 'Crear Nuevo Usuario'
    }
    return render(request, 'apptask/admin/user_form.html', context)

# === GESTIÓN DE CLASES (SOLO ADMIN) ===
@login_required
@user_passes_test(admin_required)
def admin_class_list(request):
    """Lista de clases para administradores"""
    classes = SchoolClass.objects.all().order_by('-id')
    
    # Calcular estadísticas correctamente
    total_students = 0
    total_tasks = 0
    unique_teachers = set()
    
    for school_class in classes:
        total_students += school_class.student_list.count()
        total_tasks += school_class.tasks.count()
        unique_teachers.add(school_class.teacher.id)
    
    total_teachers = len(unique_teachers)
    
    context = {
        'classes': classes,
        'total_students': total_students,
        'total_tasks': total_tasks,
        'total_teachers': total_teachers,
    }
    return render(request, 'apptask/admin/class_list.html', context)

@login_required
@user_passes_test(admin_required)
def admin_class_list(request):
    """Lista de clases para administradores"""
    classes = SchoolClass.objects.all().order_by('-id')
    
    # Contar estudiantes únicos en el sistema
    from apptask.models import User
    total_students = User.objects.filter(role='student').count()
    
    # Contar docentes únicos
    total_teachers = User.objects.filter(role='teacher').count()
    
    # Contar tareas totales
    total_tasks = 0
    for school_class in classes:
        total_tasks += school_class.tasks.count()
    
    context = {
        'classes': classes,
        'total_students': total_students,  # Total de estudiantes en el sistema
        'total_tasks': total_tasks,
        'total_teachers': total_teachers,
    }
    return render(request, 'apptask/admin/class_list.html', context)

@login_required
@user_passes_test(admin_required)
def admin_class_edit(request, class_id):
    """Editar clase existente (solo admin)"""
    school_class = get_object_or_404(SchoolClass, id=class_id)
    
    if request.method == 'POST':
        identify = request.POST.get('identify')
        course = request.POST.get('course')
        teacher_id = request.POST.get('teacher')
        student_ids = request.POST.getlist('students')
        
        # Validar que no exista otra clase con el mismo identificador
        if SchoolClass.objects.filter(identify=identify).exclude(id=class_id).exists():
            messages.error(request, 'Ya existe otra clase con este identificador.')
            teachers = User.objects.filter(role='teacher')
            students = User.objects.filter(role='student').order_by('first_name', 'last_name')
            return render(request, 'apptask/admin/class_form.html', {
                'teachers': teachers,
                'students': students,
                'school_class': school_class,
                'form_data': request.POST,
                'title': f'Editar Clase: {school_class.identify}'
            })
        
        try:
            teacher = User.objects.get(id=teacher_id, role='teacher')
            
            # Actualizar la clase
            school_class.identify = identify
            school_class.course = course
            school_class.teacher = teacher
            school_class.save()
            
            # Actualizar estudiantes
            school_class.student_list.clear()  # Remover todos los estudiantes actuales
            if student_ids:
                students = User.objects.filter(id__in=student_ids, role='student')
                school_class.student_list.add(*students)
            
            messages.success(request, f'Clase {school_class.identify} actualizada exitosamente.')
            return redirect('admin_class_list')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar clase: {str(e)}')
    
    teachers = User.objects.filter(role='teacher')
    students = User.objects.filter(role='student').order_by('first_name', 'last_name')
    
    # Preparar datos para el formulario
    form_data = {
        'identify': school_class.identify,
        'course': school_class.course,
        'teacher': school_class.teacher.id,
        'students': list(school_class.student_list.values_list('id', flat=True))
    }
    
    context = {
        'teachers': teachers,
        'students': students,
        'school_class': school_class,
        'form_data': form_data,
        'title': f'Editar Clase: {school_class.identify}'
    }
    return render(request, 'apptask/admin/class_form.html', context)

@login_required
@user_passes_test(admin_required)
def admin_class_delete(request, class_id):
    """Eliminar clase (solo admin)"""
    school_class = get_object_or_404(SchoolClass, id=class_id)
    
    if request.method == 'POST':
        class_name = school_class.identify
        
        # Verificar si la clase tiene tareas asociadas
        if school_class.tasks.exists():
            messages.error(request, f'No se puede eliminar la clase {class_name} porque tiene tareas asociadas.')
            return redirect('admin_class_list')
        
        try:
            school_class.delete()
            messages.success(request, f'Clase {class_name} eliminada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al eliminar la clase: {str(e)}')
    
    return redirect('admin_class_list')


@login_required
@user_passes_test(admin_required)
def admin_system_config(request):
    """Configuración del sistema (solo admin)"""
    from django.conf import settings
    from django.core.management import call_command
    import os
    import sys
    from datetime import datetime
    import json
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'clear_logs':
            try:
                log_files = ['django.log', 'error.log', 'access.log']
                cleared_files = []
                
                for log_file in log_files:
                    log_path = os.path.join(settings.BASE_DIR, log_file)
                    if os.path.exists(log_path):
                        with open(log_path, 'w') as f:
                            f.write('')
                        cleared_files.append(log_file)
                
                if cleared_files:
                    messages.success(request, f'Logs limpiados: {", ".join(cleared_files)}')
                else:
                    messages.info(request, 'No se encontraron archivos de log.')
            except Exception as e:
                messages.error(request, f'Error al limpiar logs: {str(e)}')
        
        elif action == 'backup_db':
            try:
                # Crear directorio de backups
                backup_dir = os.path.join(settings.BASE_DIR, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
                
                # Crear nombre del archivo con timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_filename = f'backup_{timestamp}.json'
                backup_path = os.path.join(backup_dir, backup_filename)
                
                # Crear el backup usando dumpdata
                with open(backup_path, 'w', encoding='utf-8') as backup_file:
                    call_command('dumpdata', 
                               '--natural-foreign', 
                               '--natural-primary',
                               '--indent=2',
                               stdout=backup_file)
                
                # Verificar que el archivo se creó correctamente
                if os.path.exists(backup_path):
                    file_size = os.path.getsize(backup_path)
                    file_size_mb = file_size / (1024 * 1024)
                    
                    messages.success(request, 
                        f'Backup creado exitosamente: {backup_filename} ({file_size_mb:.2f} MB)')
                else:
                    messages.error(request, 'Error: No se pudo crear el archivo de backup.')
                    
            except Exception as e:
                messages.error(request, f'Error al crear backup: {str(e)}')
        
        elif action == 'update_settings':
            # Actualizar configuraciones
            messages.success(request, 'Configuraciones actualizadas exitosamente.')
        
        return redirect('admin_system_config')
    
    # Obtener información del sistema
    system_info = {
        'python_version': sys.version,
        'django_version': '5.2.4',
        'debug_mode': settings.DEBUG,
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'time_zone': settings.TIME_ZONE,
        'language_code': settings.LANGUAGE_CODE,
        'installed_apps_count': len(settings.INSTALLED_APPS),
        'secret_key_set': bool(settings.SECRET_KEY),
    }
    
    # Estadísticas del sistema
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_classes': SchoolClass.objects.count(),
        'total_tasks': Task.objects.count(),
        'total_deliveries': Delivery.objects.count(),
    }
    
    # Información de logs
    log_info = {'log_file_exists': False}
    try:
        log_file = os.path.join(settings.BASE_DIR, 'django.log')
        if os.path.exists(log_file):
            log_info['log_file_exists'] = True
            log_info['log_file_size'] = os.path.getsize(log_file)
    except Exception as e:
        log_info['error'] = str(e)
    
    # Usuarios por rol
    roles_stats = {
        'admins': User.objects.filter(role='admin').count(),
        'teachers': User.objects.filter(role='teacher').count(),
        'students': User.objects.filter(role='student').count(),
        'observers': User.objects.filter(role='observer').count(),
    }
    
    # Información de backups
    backup_info = {
        'backup_files': [],
        'backup_count': 0,
        'backup_total_size': 0
    }
    
    try:
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if os.path.exists(backup_dir):
            backup_files = []
            for filename in os.listdir(backup_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(backup_dir, filename)
                    file_stat = os.stat(file_path)
                    backup_files.append({
                        'filename': filename,
                        'size': file_stat.st_size,
                        'date': datetime.fromtimestamp(file_stat.st_mtime),
                        'path': file_path
                    })
            
            # Ordenar por fecha (más reciente primero)
            backup_files.sort(key=lambda x: x['date'], reverse=True)
            
            backup_info['backup_files'] = backup_files
            backup_info['backup_count'] = len(backup_files)
            backup_info['backup_total_size'] = sum(f['size'] for f in backup_files)
    except Exception as e:
        backup_info['error'] = str(e)
    
    # Actividad reciente
    recent_activity = {
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_tasks': Task.objects.order_by('-created_at')[:5],
        'recent_deliveries': Delivery.objects.order_by('-date')[:5],
    }
    
    context = {
        'system_info': system_info,
        'stats': stats,
        'log_info': log_info,
        'roles_stats': roles_stats,
        'backup_info': backup_info,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'apptask/admin/system_config.html', context)

@login_required
@user_passes_test(admin_required)
def admin_download_backup(request, filename):
    """Descargar archivo de backup"""
    from django.http import HttpResponse, Http404
    from django.conf import settings
    import os
    import mimetypes
    
    # Verificar que el archivo existe y es seguro
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    file_path = os.path.join(backup_dir, filename)
    
    # Verificar que el archivo existe y está en el directorio correcto
    if not os.path.exists(file_path) or not file_path.startswith(backup_dir):
        raise Http404("Archivo no encontrado")
    
    # Verificar que es un archivo JSON
    if not filename.endswith('.json'):
        raise Http404("Archivo no válido")
    
    try:
        with open(file_path, 'rb') as backup_file:
            response = HttpResponse(backup_file.read(), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    except Exception as e:
        messages.error(request, f'Error al descargar backup: {str(e)}')
        return redirect('admin_system_config')

# === GESTIÓN DE TAREAS (SOLO DOCENTES) ===
@login_required
@user_passes_test(teacher_required)
def teacher_task_create(request):
    """Crear una nueva tarea para docentes - CON SOPORTE PARA ARCHIVOS"""
    if request.method == 'POST':
        form = TaskForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            try:
                task = form.save(commit=False)
                task.created_at = timezone.now()
                task.save()
                
                # Mensaje de éxito con información del archivo si se adjuntó
                if task.attachment:
                    messages.success(
                        request, 
                        f'Tarea creada exitosamente con archivo adjunto: {task.attachment_name}'
                    )
                else:
                    messages.success(request, 'Tarea creada exitosamente.')
                
                return redirect('teacher_task_list')
            except Exception as e:
                messages.error(request, f'Error al crear la tarea: {str(e)}')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = TaskForm(user=request.user)
    
    assigned_classes = request.user.taught_classes.all()
    if not assigned_classes:
        messages.error(request, 'No tienes clases asignadas. Contacta al administrador.')
    
    return render(request, 'apptask/teacher/task_form.html', {
        'form': form,
        'title': 'Crear Nueva Tarea',
        'assigned_classes': assigned_classes,
    })

@login_required
@user_passes_test(teacher_required)
def teacher_task_detail(request, task_id):
    """Vista de detalle de tarea específica para docentes"""
    teacher = request.user
    task = get_object_or_404(Task, id=task_id, school_class__teacher=teacher)
    
    # Obtener entregas de esta tarea
    deliveries = task.delivery_list.all().order_by('-date', '-delivery_time')
    
    # Estadísticas de la tarea
    total_students = task.school_class.student_list.count()
    total_deliveries = deliveries.count()
    graded_deliveries = deliveries.filter(grade__isnull=False).count()
    pending_deliveries = deliveries.filter(grade__isnull=True).count()
    
    # Estudiantes que no han entregado
    students_delivered = deliveries.values_list('student_id', flat=True)
    students_not_delivered = task.school_class.student_list.exclude(id__in=students_delivered)
    
    context = {
        'task': task,
        'deliveries': deliveries,
        'total_students': total_students,
        'total_deliveries': total_deliveries,
        'graded_deliveries': graded_deliveries,
        'pending_deliveries': pending_deliveries,
        'students_not_delivered': students_not_delivered,
    }
    
    return render(request, 'apptask/teacher/task_detail.html', context)

@login_required
@user_passes_test(teacher_required)
def teacher_task_list(request):
    """Lista de tareas del docente - OPTIMIZADA"""
    teacher = request.user
    
    # Consulta optimizada con select_related
    tasks = Task.objects.filter(
        school_class__teacher=teacher
    ).select_related('school_class').order_by('-created_at')
    
    # Filtros
    class_filter = request.GET.get('class')
    if class_filter:
        tasks = tasks.filter(school_class_id=class_filter)
    
    # Paginación para mejorar rendimiento
    from django.core.paginator import Paginator
    paginator = Paginator(tasks, 10)  # 10 tareas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener clases con una sola consulta
    my_classes = teacher.taught_classes.all()
    
    context = {
        'page_obj': page_obj,
        'tasks': page_obj,  # Para compatibilidad con template
        'my_classes': my_classes,
        'current_class': class_filter,
        'is_paginated': paginator.num_pages > 1,
    }
    return render(request, 'apptask/teacher/task_list.html', context)

# === VISTAS PARA ESTUDIANTES ===
@login_required
@user_passes_test(student_required)
def student_task_list(request):
    """Lista de tareas disponibles para el estudiante - OPTIMIZADA"""
    student = request.user
    
    # Obtener todas las tareas de las clases en las que está inscrito con datos precargados
    available_tasks = Task.objects.filter(
        school_class__student_list=student
    ).select_related('school_class', 'school_class__teacher').order_by('-created_at')
    
    # Obtener las entregas del estudiante con datos precargados
    my_deliveries = Delivery.objects.filter(
        student=student
    ).select_related('task').prefetch_related('task__school_class')
    
    # Crear un set de IDs de tareas entregadas para consulta rápida
    delivered_task_ids = set(my_deliveries.values_list('task_id', flat=True))
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(available_tasks, 10)  # 10 tareas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'available_tasks': page_obj,  # Para compatibilidad
        'my_deliveries': my_deliveries,
        'delivered_task_ids': delivered_task_ids,  # Para verificar entregas en template
        'is_paginated': paginator.num_pages > 1,
    }
    return render(request, 'apptask/student/task_list.html', context)

# === VISTAS DE AUTENTICACIÓN (mantener como están) ===
def user_login_page(request):
    """Página de login"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                login(request, user)
                messages.success(request, f'Bienvenido/a {user.display_name}')
                return redirect('home')
            else:
                messages.error(request, 'Credenciales incorrectas')
        except User.DoesNotExist:
            messages.error(request, 'Usuario no encontrado')
    
    return render(request, 'apptask/auth/login.html')

def user_logout_view(request):
    """Cerrar sesión"""
    logout(request)
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('login')

@login_required
def task_detail(request, task_id):
    """Detalle de una tarea específica"""
    task = get_object_or_404(Task, id=task_id)
    deliveries = task.delivery_list.all()
    return render(request, 'apptask/task_detail.html', {
        'task': task,
        'deliveries': deliveries
    })

@login_required
@user_passes_test(teacher_required)
def task_edit(request, task_id):
    """Editar una tarea existente - CON SOPORTE PARA ARCHIVOS"""
    task = get_object_or_404(Task, id=task_id, school_class__teacher=request.user)
    
    if request.method == 'POST':
        form = TaskForm(user=request.user, data=request.POST, files=request.FILES, instance=task)
        if form.is_valid():
            updated_task = form.save()
            
            # Mensaje de éxito con información del archivo
            if updated_task.attachment:
                messages.success(
                    request, 
                    f'Tarea "{task.theme}" actualizada exitosamente con archivo: {updated_task.attachment_name}'
                )
            else:
                messages.success(request, f'Tarea "{task.theme}" actualizada exitosamente.')
            
            return redirect('teacher_task_detail', task_id=task.id)
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = TaskForm(user=request.user, instance=task)
    
    context = {
        'form': form,
        'task': task,
        'title': f'Editar Tarea: {task.theme}',
    }
    return render(request, 'apptask/teacher/task_form.html', context)

@login_required
@user_passes_test(teacher_required)
def task_delete(request, task_id):
    """Eliminar una tarea"""
    task = get_object_or_404(Task, id=task_id, school_class__teacher=request.user)
    
    if request.method == 'POST':
        task_name = task.theme
        task.delete()
        messages.success(request, f'Tarea "{task_name}" eliminada exitosamente.')
        return redirect('teacher_task_list')
    
    return redirect('teacher_task_detail', task_id=task.id)

@login_required
def delivery_create(request, task_id):
    """Crear una nueva entrega para una tarea"""
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        form = DeliveryForm(request.POST, request.FILES)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.task = task
            delivery.student = request.user
            delivery.date = timezone.now().date()
            delivery.delivery_time = timezone.now().time()
            # Por ahora asignamos un profesor por defecto como revisor
            delivery.revisor = User.objects.filter(role='teacher').first()
            delivery.save()
            messages.success(request, 'Entrega realizada exitosamente.')
            return redirect('task_detail', task_id=task.id)
    else:
        form = DeliveryForm()
    
    return render(request, 'apptask/delivery_form.html', {
        'form': form,
        'task': task,
        'title': 'Nueva Entrega'
    })

@login_required
def delivery_grade(request, delivery_id):
    """Calificar una entrega"""
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    if request.method == 'POST':
        form = GradeDeliveryForm(request.POST, instance=delivery)
        if form.is_valid():
            delivery = form.save()
            messages.success(request, f'Entrega de {delivery.student.name} calificada exitosamente.')
            return redirect('task_detail', task_id=delivery.task.id)
    else:
        form = GradeDeliveryForm(instance=delivery)
    
    return render(request, 'apptask/grade_form.html', {
        'form': form,
        'delivery': delivery,
        'title': 'Calificar Entrega'
    })

@login_required
def delivery_edit_grade(request, delivery_id):
    """Editar la calificación de una entrega existente"""
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    if request.method == 'POST':
        form = GradeDeliveryForm(request.POST, instance=delivery)
        if form.is_valid():
            delivery = form.save()
            messages.success(request, f'Calificación de {delivery.student.name} actualizada exitosamente.')
            return redirect('task_detail', task_id=delivery.task.id)
    else:
        form = GradeDeliveryForm(instance=delivery)
    
    return render(request, 'apptask/grade_form.html', {
        'form': form,
        'delivery': delivery,
        'title': 'Editar Calificación',
        'is_edit': True
    })

@login_required
def delivery_list(request):
    """Lista todas las entregas"""
    deliveries = Delivery.objects.all().order_by('-date')
    return render(request, 'apptask/delivery_list.html', {'deliveries': deliveries})

# === API VIEWS (mantener todas como están) ===
class UserRegistrationView(APIView):
    """Registro de nuevos usuarios"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Usuario registrado exitosamente',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )

class UserLoginView(APIView):
    """Autenticación de usuarios"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generar tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Inicio de sesión exitoso',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class UserLogoutView(APIView):
    """Cerrar sesión (blacklist token)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Sesión cerrada exitosamente'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Token inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserProfileView(APIView):
    """Perfil del usuario autenticado"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Perfil actualizado exitosamente',
                'user': serializer.data
            })
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class UserListView(APIView):
    """Lista de usuarios (solo admin)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Verificar permisos de admin
        if not request.user.has_role('admin'):
            return Response(
                {'error': 'No tiene permisos para esta acción'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        users = User.objects.all().order_by('-date_joined')
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)

# === PERMISOS PERSONALIZADOS ===
class IsTeacherOrAdmin(permissions.BasePermission):
    """Permiso para docentes y administradores"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role in ['teacher', 'admin']
        )

class IsAdmin(permissions.BasePermission):
    """Permiso solo para administradores"""
    
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and 
            request.user.role == 'admin'
        )

# === VISTAS WEB ADICIONALES ===
def user_register_page(request):
    """Página de registro"""
    if request.method == 'POST':
        # Implementar lógica de registro
        pass
    
    return render(request, 'apptask/auth/register.html')

@login_required
def user_profile_page(request):
    """Página de perfil de usuario"""
    user = request.user
    
    # Calcular estadísticas según el rol
    context = {'user': user}
    
    if user.role == 'teacher':
        # Estadísticas para docentes
        total_tasks = Task.objects.filter(school_class__teacher=user).count()
        total_deliveries = Delivery.objects.filter(task__school_class__teacher=user).count()
        context.update({
            'total_tasks': total_tasks,
            'total_deliveries': total_deliveries,
        })
    
    if request.method == 'POST':
        # Actualizar datos del perfil
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.name = request.POST.get('name', user.name)
        user.username = request.POST.get('username', user.username)
        user.phone = request.POST.get('phone', user.phone)
        user.dni = request.POST.get('dni', user.dni)
        
        try:
            user.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')
        
        return redirect('profile')
    
    return render(request, 'apptask/auth/profile.html', context)

@login_required
def change_password_view(request):
    """Cambiar contraseña del usuario"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verificar contraseña actual
        if not request.user.check_password(current_password):
            messages.error(request, 'La contraseña actual es incorrecta.')
            return redirect('profile')
        
        # Verificar que las nuevas contraseñas coincidan
        if new_password != confirm_password:
            messages.error(request, 'Las nuevas contraseñas no coinciden.')
            return redirect('profile')
         
        # Verificar longitud mínima
        if len(new_password) < 8:
            messages.error(request, 'La nueva contraseña debe tener al menos 8 caracteres.')
            return redirect('profile')
        
        # Cambiar contraseña
        try:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Contraseña cambiada exitosamente. Por favor, inicia sesión nuevamente.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error al cambiar la contraseña: {str(e)}')
    
    return redirect('profile')

# === DECORADORES PERSONALIZADOS ===
def observer_required(user):
    """Verifica que el usuario sea observador"""
    return user.is_authenticated and user.role == 'observer'

def observer_or_admin_required(user):
    """Verifica que el usuario sea observador o administrador"""
    return user.is_authenticated and user.role in ['observer', 'admin']

# === VISTAS PARA OBSERVADORES ===
@login_required
@user_passes_test(observer_required)
def observer_dashboard(request):
    """Dashboard principal para observadores"""
    # Estadísticas generales del sistema
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_classes = SchoolClass.objects.count()
    total_tasks = Task.objects.count()
    total_deliveries = Delivery.objects.count()
    
    # Estadísticas de entregas
    pending_deliveries = Delivery.objects.filter(feedback='').count()
    graded_deliveries = Delivery.objects.exclude(feedback='').count()
    
    # Calcular porcentajes (evitar división por cero)
    graded_percentage = 0
    pending_percentage = 0
    if total_deliveries > 0:
        graded_percentage = (graded_deliveries * 100) / total_deliveries
        pending_percentage = (pending_deliveries * 100) / total_deliveries
    
    # Actividad reciente
    recent_tasks = Task.objects.order_by('-created_at')[:5]
    recent_deliveries = Delivery.objects.order_by('-date')[:5]
    
    # Promedio general de calificaciones
    from django.db.models import Avg
    avg_grade = Delivery.objects.filter(grade__isnull=False).aggregate(
        average=Avg('grade')
    )['average']
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_tasks': total_tasks,
        'total_deliveries': total_deliveries,
        'pending_deliveries': pending_deliveries,
        'graded_deliveries': graded_deliveries,
        'graded_percentage': graded_percentage,
        'pending_percentage': pending_percentage,
        'recent_tasks': recent_tasks,
        'recent_deliveries': recent_deliveries,
        'avg_grade': avg_grade,
    }
    
    return render(request, 'apptask/observer/dashboard.html', context)

@login_required
@user_passes_test(observer_required)
def observer_reports(request):
    """Centro de reportes detallados para observadores"""
    from django.db.models import Avg, Count, Q, Max, Min
    from datetime import datetime, timedelta
    
    # Filtros de fecha
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Query base para entregas
    deliveries_query = Delivery.objects.all()
    if date_from:
        deliveries_query = deliveries_query.filter(date__gte=date_from)
    if date_to:
        deliveries_query = deliveries_query.filter(date__lte=date_to)
    
    # === ESTADÍSTICAS GENERALES ===
    delivery_stats = {
        'total': deliveries_query.count(),
        'graded': deliveries_query.exclude(feedback='').count(),
        'pending': deliveries_query.filter(feedback='').count(),
        'on_time': deliveries_query.filter(
            date__lte=models.F('task__delivery_date')
        ).count(),
        'late': deliveries_query.filter(
            date__gt=models.F('task__delivery_date')
        ).count(),
    }
    
    # Calcular porcentajes
    total = delivery_stats['total']
    if total > 0:
        delivery_stats['graded_percentage'] = (delivery_stats['graded'] * 100) / total
        delivery_stats['pending_percentage'] = (delivery_stats['pending'] * 100) / total
        delivery_stats['on_time_percentage'] = (delivery_stats['on_time'] * 100) / total
        delivery_stats['late_percentage'] = (delivery_stats['late'] * 100) / total
    else:
        delivery_stats['graded_percentage'] = 0
        delivery_stats['pending_percentage'] = 0
        delivery_stats['on_time_percentage'] = 0
        delivery_stats['late_percentage'] = 0
    
    # === ESTADÍSTICAS POR CLASE ===
    class_averages = []
    for school_class in SchoolClass.objects.all():
        class_deliveries = deliveries_query.filter(task__school_class=school_class)
        
        avg_grade = class_deliveries.filter(
            grade__isnull=False
        ).aggregate(average=Avg('grade'))['average']
        
        total_students = school_class.student_list.count()
        total_tasks = school_class.tasks.count()
        expected_deliveries = total_students * total_tasks
        actual_deliveries = class_deliveries.count()
        
        completion_rate = 0
        if expected_deliveries > 0:
            completion_rate = (actual_deliveries * 100) / expected_deliveries
        
        class_averages.append({
            'class': school_class,
            'average_grade': round(avg_grade, 2) if avg_grade else 0,
            'total_deliveries': actual_deliveries,
            'expected_deliveries': expected_deliveries,
            'completion_rate': round(completion_rate, 1),
            'graded_count': class_deliveries.exclude(feedback='').count(),
            'pending_count': class_deliveries.filter(feedback='').count(),
        })
    
    # Ordenar por promedio descendente
    class_averages.sort(key=lambda x: x['average_grade'], reverse=True)
    
    # === RENDIMIENTO POR ESTUDIANTE ===
    student_performance = []
    for student in User.objects.filter(role='student'):
        student_deliveries = deliveries_query.filter(student=student)
        
        avg_grade = student_deliveries.filter(
            grade__isnull=False
        ).aggregate(average=Avg('grade'))['average']
        
        # Contar tareas asignadas al estudiante
        assigned_tasks = Task.objects.filter(
            school_class__student_list=student
        ).count()
        
        completion_rate = 0
        if assigned_tasks > 0:
            completion_rate = (student_deliveries.count() * 100) / assigned_tasks
        
        student_performance.append({
            'student': student,
            'total_deliveries': student_deliveries.count(),
            'graded_deliveries': student_deliveries.exclude(feedback='').count(),
            'average_grade': round(avg_grade, 2) if avg_grade else 0,
            'assigned_tasks': assigned_tasks,
            'completion_rate': round(completion_rate, 1),
            'on_time_deliveries': student_deliveries.filter(
                date__lte=models.F('task__delivery_date')
            ).count(),
            'late_deliveries': student_deliveries.filter(
                date__gt=models.F('task__delivery_date')
            ).count(),
        })
    
    # Ordenar por promedio descendente
    student_performance.sort(key=lambda x: x['average_grade'], reverse=True)
    
    # === ACTIVIDAD POR DOCENTE ===
    teacher_activity = []
    for teacher in User.objects.filter(role='teacher'):
        teacher_deliveries = deliveries_query.filter(task__school_class__teacher=teacher)
        
        teacher_activity.append({
            'teacher': teacher,
            'classes_count': teacher.taught_classes.count(),
            'tasks_created': Task.objects.filter(school_class__teacher=teacher).count(),
            'total_deliveries': teacher_deliveries.count(),
            'deliveries_reviewed': teacher_deliveries.exclude(feedback='').count(),
            'pending_reviews': teacher_deliveries.filter(feedback='').count(),
            'avg_response_time': 'N/A',  # Puedes implementar esto si tienes timestamps
        })
    
    # === ESTADÍSTICAS DE CALIFICACIONES ===
    graded_deliveries = deliveries_query.exclude(grade__isnull=True)
    grade_distribution = {
        'excellent': graded_deliveries.filter(grade__gte=9).count(),  # 9-10
        'good': graded_deliveries.filter(grade__gte=7, grade__lt=9).count(),  # 7-8.99
        'average': graded_deliveries.filter(grade__gte=5, grade__lt=7).count(),  # 5-6.99
        'poor': graded_deliveries.filter(grade__lt=5).count(),  # 0-4.99
    }
    
    total_graded = graded_deliveries.count()
    if total_graded > 0:
        grade_distribution['excellent_percentage'] = (grade_distribution['excellent'] * 100) / total_graded
        grade_distribution['good_percentage'] = (grade_distribution['good'] * 100) / total_graded
        grade_distribution['average_percentage'] = (grade_distribution['average'] * 100) / total_graded
        grade_distribution['poor_percentage'] = (grade_distribution['poor'] * 100) / total_graded
    
    # === TENDENCIAS TEMPORALES (últimos 30 días) ===
    thirty_days_ago = datetime.now().date() - timedelta(days=30)
    daily_deliveries = []
    
    for i in range(30):
        day = thirty_days_ago + timedelta(days=i)
        count = deliveries_query.filter(date=day).count()
        daily_deliveries.append({
            'date': day,
            'count': count
        })
    
    context = {
        'delivery_stats': delivery_stats,
        'class_averages': class_averages,
        'student_performance': student_performance[:20],  # Top 20
        'teacher_activity': teacher_activity,
        'grade_distribution': grade_distribution,
        'daily_deliveries': daily_deliveries,
        'date_from': date_from,
        'date_to': date_to,
        'total_graded': total_graded,
    }
    
    return render(request, 'apptask/observer/reports.html', context)

@login_required
@user_passes_test(observer_required)
def observer_academic_overview(request):
    """Vista académica detallada para observadores"""
    # Todas las clases con estadísticas completas
    classes_data = []
    for school_class in SchoolClass.objects.all():
        tasks = school_class.tasks.all()
        students = school_class.student_list.all()
        deliveries = Delivery.objects.filter(task__school_class=school_class)
        
        # Calcular estadísticas
        total_possible_deliveries = tasks.count() * students.count()
        actual_deliveries = deliveries.count()
        graded_deliveries = deliveries.exclude(feedback='').count()
        
        avg_grade = deliveries.filter(
            grade__isnull=False
        ).aggregate(average=Avg('grade'))['average']
        
        completion_rate = 0
        if total_possible_deliveries > 0:
            completion_rate = (actual_deliveries / total_possible_deliveries) * 100
        
        classes_data.append({
            'class': school_class,
            'teacher': school_class.teacher,
            'tasks_count': tasks.count(),
            'students_count': students.count(),
            'total_deliveries': actual_deliveries,
            'graded_deliveries': graded_deliveries,
            'pending_deliveries': actual_deliveries - graded_deliveries,
            'avg_grade': round(avg_grade, 2) if avg_grade else 0,
            'completion_rate': round(completion_rate, 1),
            'total_possible': total_possible_deliveries,
        })
    
    # Estadísticas globales
    global_stats = {
        'total_classes': SchoolClass.objects.count(),
        'total_students': User.objects.filter(role='student').count(),
        'total_teachers': User.objects.filter(role='teacher').count(),
        'total_tasks': Task.objects.count(),
        'total_deliveries': Delivery.objects.count(),
        'global_avg': Delivery.objects.filter(
            grade__isnull=False
        ).aggregate(avg=Avg('grade'))['avg'] or 0,
    }
    
    context = {
        'classes_data': classes_data,
        'global_stats': global_stats,
    }
    
    return render(request, 'apptask/observer/academic_overview.html', context)

@login_required
@user_passes_test(observer_required)
def observer_export_report(request):
    """Exportar reportes en formato CSV"""
    import csv
    from django.http import HttpResponse
    from datetime import datetime
    
    report_type = request.GET.get('type', 'deliveries')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Crear respuesta HTTP con header CSV
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="reporte_{report_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Filtrar por fechas si se proporcionan
    deliveries_query = Delivery.objects.all()
    if date_from:
        deliveries_query = deliveries_query.filter(date__gte=date_from)
    if date_to:
        deliveries_query = deliveries_query.filter(date__lte=date_to)
    
    if report_type == 'deliveries':
        # Reporte de entregas
        writer.writerow([
            'Estudiante', 'Email', 'Tarea', 'Clase', 'Docente', 
            'Fecha Entrega', 'Hora Entrega', 'Calificación', 'Estado', 
            'Retroalimentación', 'Entrega Tardía'
        ])
        
        for delivery in deliveries_query.select_related(
            'student', 'task', 'task__school_class', 'task__school_class__teacher'
        ).order_by('-date'):
            writer.writerow([
                delivery.student.display_name or delivery.student.name,
                delivery.student.email,
                delivery.task.theme,
                delivery.task.school_class.identify,
                delivery.task.school_class.teacher.display_name or delivery.task.school_class.teacher.name,
                delivery.date.strftime('%Y-%m-%d'),
                delivery.delivery_time.strftime('%H:%M:%S'),
                delivery.grade if delivery.grade else 'Sin calificar',
                'Calificada' if delivery.feedback else 'Pendiente',
                delivery.feedback[:100] if delivery.feedback else '',  # Limitar texto
                'Sí' if delivery.is_late else 'No'
            ])
    
    elif report_type == 'students':
        # Reporte de estudiantes
        writer.writerow([
            'Estudiante', 'Email', 'Clases Inscritas', 'Entregas Realizadas', 
            'Entregas Calificadas', 'Promedio General', 'Entregas A Tiempo', 
            'Entregas Tardías', 'Porcentaje Completado'
        ])
        
        for student in User.objects.filter(role='student').order_by('first_name'):
            student_deliveries = deliveries_query.filter(student=student)
            graded_deliveries = student_deliveries.exclude(feedback='')
            
            avg_grade = graded_deliveries.aggregate(
                avg=Avg('grade')
            )['avg'] or 0
            
            # Calcular tareas asignadas
            assigned_tasks = Task.objects.filter(
                school_class__student_list=student
            ).count()
            
            completion_rate = 0
            if assigned_tasks > 0:
                completion_rate = (student_deliveries.count() * 100) / assigned_tasks
            
            writer.writerow([
                student.display_name or student.name,
                student.email,
                student.classes.count(),
                student_deliveries.count(),
                graded_deliveries.count(),
                round(avg_grade, 2),
                student_deliveries.filter(
                    date__lte=models.F('task__delivery_date')
                ).count(),
                student_deliveries.filter(
                    date__gt=models.F('task__delivery_date')
                ).count(),
                round(completion_rate, 1)
            ])
    
    elif report_type == 'classes':
        # Reporte de clases
        writer.writerow([
            'Clase', 'Curso', 'Docente', 'Email Docente', 'Estudiantes', 
            'Tareas Asignadas', 'Total Entregas', 'Entregas Calificadas', 
            'Promedio Clase', 'Porcentaje Completado'
        ])
        
        for school_class in SchoolClass.objects.all().order_by('identify'):
            class_deliveries = deliveries_query.filter(task__school_class=school_class)
            graded_deliveries = class_deliveries.exclude(feedback='')
            
            avg_grade = graded_deliveries.aggregate(
                avg=Avg('grade')
            )['avg'] or 0
            
            students_count = school_class.student_list.count()
            tasks_count = school_class.tasks.count()
            expected_deliveries = students_count * tasks_count
            
            completion_rate = 0
            if expected_deliveries > 0:
                completion_rate = (class_deliveries.count() * 100) / expected_deliveries
            
            writer.writerow([
                school_class.identify,
                school_class.course,
                school_class.teacher.display_name or school_class.teacher.name,
                school_class.teacher.email,
                students_count,
                tasks_count,
                class_deliveries.count(),
                graded_deliveries.count(),
                round(avg_grade, 2),
                round(completion_rate, 1)
            ])
    
    elif report_type == 'teachers':
        # Reporte de docentes
        writer.writerow([
            'Docente', 'Email', 'Clases Asignadas', 'Tareas Creadas', 
            'Entregas Recibidas', 'Entregas Calificadas', 'Entregas Pendientes',
            'Promedio Calificaciones Otorgadas', 'Porcentaje Revisión'
        ])
        
        for teacher in User.objects.filter(role='teacher').order_by('first_name'):
            teacher_deliveries = deliveries_query.filter(task__school_class__teacher=teacher)
            graded_deliveries = teacher_deliveries.exclude(feedback='')
            
            avg_grade_given = graded_deliveries.aggregate(
                avg=Avg('grade')
            )['avg'] or 0
            
            review_rate = 0
            if teacher_deliveries.count() > 0:
                review_rate = (graded_deliveries.count() * 100) / teacher_deliveries.count()
            
            writer.writerow([
                teacher.display_name or teacher.name,
                teacher.email,
                teacher.taught_classes.count(),
                Task.objects.filter(school_class__teacher=teacher).count(),
                teacher_deliveries.count(),
                graded_deliveries.count(),
                teacher_deliveries.filter(feedback='').count(),
                round(avg_grade_given, 2),
                round(review_rate, 1)
            ])
    
    return response

def user_forgot_password(request):
    """Vista para recuperar contraseña usando cédula"""
    if request.method == 'POST':
        dni = request.POST.get('dni', '').strip()
        
        if not dni:
            messages.error(request, 'Por favor, ingresa tu número de cédula.')
            return render(request, 'apptask/auth/forgot_password.html')
        
        try:
            # Buscar usuario por cédula
            user = User.objects.get(dni=dni)
            
            # Generar nueva contraseña temporal
            new_password = generate_temporary_password()
            
            # Actualizar contraseña del usuario
            user.password = make_password(new_password)
            user.save()
            
            # Aquí podrías enviar email, pero por ahora mostraremos en pantalla
            messages.success(request, 
                f'Contraseña restablecida exitosamente. Tu nueva contraseña temporal es: {new_password}')
            messages.info(request, 
                'Por favor, cambia tu contraseña temporal después de iniciar sesión.')
            
            return redirect('login')
            
        except User.DoesNotExist:
            messages.error(request, 'No se encontró un usuario con esa cédula.')
            return render(request, 'apptask/auth/forgot_password.html')
        
        except Exception as e:
            messages.error(request, 'Ocurrió un error al procesar tu solicitud. Intenta nuevamente.')
            return render(request, 'apptask/auth/forgot_password.html')
    
    return render(request, 'apptask/auth/forgot_password.html')

def generate_temporary_password():
    """Genera una contraseña temporal segura"""
    # Generar contraseña de 8 caracteres con letras y números
    characters = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(characters) for _ in range(8))
    
    # Asegurar que tenga al menos una mayúscula, una minúscula y un número
    if not any(c.isupper() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_uppercase)
    if not any(c.islower() for c in password):
        password = password[:-1] + secrets.choice(string.ascii_lowercase)
    if not any(c.isdigit() for c in password):
        password = password[:-1] + secrets.choice(string.digits)
    
    return password

def user_change_password(request):
    """Vista para cambiar contraseña (usuarios logueados o recuperación)"""
    user = request.user
    # Si viene de recuperación, busca el usuario por sesión
    if not user.is_authenticated and request.session.get('password_reset_user_id'):
        try:
            user = User.objects.get(id=request.session['password_reset_user_id'])
        except User.DoesNotExist:
            messages.error(request, 'Usuario no válido para recuperación.')
            return redirect('login')
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not new_password or not confirm_password:
            messages.error(request, 'Por favor completa todos los campos.')
            return render(request, 'apptask/auth/change_password.html')
        
        if new_password != confirm_password:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'apptask/auth/change_password.html')
        
        if len(new_password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'apptask/auth/change_password.html')
        
        user.set_password(new_password)
        user.save()
        # Limpia la sesión si venía de recuperación
        request.session.pop('password_reset_user_id', None)
        messages.success(request, 'Contraseña cambiada exitosamente. Puedes iniciar sesión.')
        return redirect('login')
    
    return render(request, 'apptask/auth/change_password.html')

def forgot_password(request):
    """Vista para solicitar recuperación de contraseña"""
    if request.method == 'POST':
        cedula = request.POST.get('cedula', '').strip()
        email = request.POST.get('email', '').strip()
        
        if not cedula or not email:
            messages.error(request, 'Por favor ingresa tu cédula y email.')
            return render(request, 'apptask/auth/forgot_password.html')
        
        try:
            user = User.objects.get(dni=cedula, email=email)
            # Autentica al usuario para permitirle cambiar la contraseña
            request.session['password_reset_user_id'] = user.id
            return redirect('change_password')
        except User.DoesNotExist:
            messages.error(request, 'No se encontró un usuario con esa cédula y email.')
            return render(request, 'apptask/auth/forgot_password.html')
    return render(request, 'apptask/auth/forgot_password.html')

def reset_password(request, token):
    """Vista para restablecer contraseña con token"""
    try:
        # Buscar usuario por token
        user = User.objects.get(password_reset_token=token)
        
        # Verificar que el token no haya expirado
        if not user.is_password_reset_token_valid(token):
            messages.error(request, 'El token ha expirado o no es válido.')
            return redirect('forgot_password')
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if not new_password or not confirm_password:
                messages.error(request, 'Por favor completa todos los campos.')
                return render(request, 'apptask/auth/reset_password.html', {'token': token})
            
            if new_password != confirm_password:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'apptask/auth/reset_password.html', {'token': token})
            
            if len(new_password) < 6:
                messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
                return render(request, 'apptask/auth/reset_password.html', {'token': token})
            
            # Cambiar contraseña
            user.set_password(new_password)
            user.clear_password_reset_token()
            
            messages.success(request, 'Contraseña cambiada exitosamente. Puedes iniciar sesión.')
            return redirect('login')
        
        return render(request, 'apptask/auth/reset_password.html', {'token': token})
        
    except User.DoesNotExist:
        messages.error(request, 'Token inválido.')
        return redirect('forgot_password')

@login_required
@user_passes_test(admin_required)
def admin_user_edit(request, user_id):
    """Editar un usuario existente (solo admin)"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        name = request.POST.get('name')
        username = request.POST.get('username')
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        dni = request.POST.get('dni')
        password = request.POST.get('password')
        class_ids = request.POST.getlist('classes')  # Para permitir edición de clases
        
        # Validaciones
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            messages.error(request, 'Ya existe otro usuario con este email.')
            return render(request, 'apptask/admin/user_form.html', {
                'role_choices': User.ROLE_CHOICES,
                'form_data': request.POST,
                'user': user,
                'title': f'Editar Usuario: {user.email}',
                'is_edit': True,
                'assigned_classes': user.taught_classes.all() if user.role == 'teacher' else [],
                'all_classes': SchoolClass.objects.all()  # Updated to SchoolClass
            })
        
        if not email.endswith('@uni.edu.ec'):
            messages.error(request, 'El email debe ser del dominio @uni.edu.ec')
            return render(request, 'apptask/admin/user_form.html', {
                'role_choices': User.ROLE_CHOICES,
                'form_data': request.POST,
                'user': user,
                'title': f'Editar Usuario: {user.email}',
                'is_edit': True,
                'assigned_classes': user.taught_classes.all() if user.role == 'teacher' else [],
                'all_classes': SchoolClass.objects.all()  # Updated to SchoolClass
            })
        
        try:
            # Actualizar los campos del usuario
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.name = name or first_name
            user.username = username
            user.role = role
            user.phone = phone
            user.dni = dni
            
            # Actualizar la contraseña solo si se proporciona
            if password:
                if len(password) < 8:
                    messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
                    return render(request, 'apptask/admin/user_form.html', {
                        'role_choices': User.ROLE_CHOICES,
                        'form_data': request.POST,
                        'user': user,
                        'title': f'Editar Usuario: {user.email}',
                        'is_edit': True,
                        'assigned_classes': user.taught_classes.all() if user.role == 'teacher' else [],
                        'all_classes': SchoolClass.objects.all()  # Updated to SchoolClass
                    })
                user.set_password(password)
            
            user.save()
            
            # Actualizar clases asignadas si es docente y se proporcionaron class_ids
            if user.role == 'teacher' and class_ids:
                # Para ForeignKey, actualizamos el campo teacher en las clases seleccionadas
                SchoolClass.objects.filter(id__in=class_ids).update(teacher=user)
                # Desasignar clases no seleccionadas
                SchoolClass.objects.filter(teacher=user).exclude(id__in=class_ids).update(teacher=None)
            
            messages.success(request, f'Usuario {user.email} actualizado exitosamente.')
            return redirect('admin_user_list')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar usuario: {str(e)}')
            return render(request, 'apptask/admin/user_form.html', {
                'role_choices': User.ROLE_CHOICES,
                'form_data': request.POST,
                'user': user,
                'title': f'Editar Usuario: {user.email}',
                'is_edit': True,
                'assigned_classes': user.taught_classes.all() if user.role == 'teacher' else [],
                'all_classes': SchoolClass.objects.all()  # Updated to SchoolClass
            })
    
    # Preparar datos para el formulario
    form_data = {
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'name': user.name,
        'username': user.username,
        'role': user.role,
        'phone': user.phone,
        'dni': user.dni,
    }
    
    # Obtener las clases asignadas y todas las clases disponibles
    assigned_classes = user.taught_classes.all() if user.role == 'teacher' else []
    all_classes = SchoolClass.objects.all()

# === VISTA PARA DESCARGAR ARCHIVOS DE TAREAS ===
@login_required
def download_task_attachment(request, task_id):
    """Permite descargar el archivo adjunto de una tarea"""
    task = get_object_or_404(Task, id=task_id)
    
    # Verificar permisos: solo estudiantes de la clase o el docente pueden descargar
    user = request.user
    has_permission = False
    
    if user.role == 'teacher' and task.school_class.teacher == user:
        has_permission = True
    elif user.role == 'student' and user in task.school_class.student_list.all():
        has_permission = True
    elif user.role == 'admin':
        has_permission = True
    
    if not has_permission:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permisos para descargar este archivo.")
    
    # Verificar que la tarea tiene archivo adjunto
    if not task.attachment:
        from django.http import Http404
        raise Http404("Esta tarea no tiene archivo adjunto.")
    
    # Servir el archivo
    import os
    from django.http import HttpResponse, Http404
    from django.conf import settings
    
    try:
        file_path = task.attachment.path
        
        if not os.path.exists(file_path):
            raise Http404("El archivo no se encuentra en el servidor.")
        
        # Obtener el tipo de contenido
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        
        # Crear la respuesta HTTP
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{task.attachment_name}"'
            response['Content-Length'] = os.path.getsize(file_path)
            return response
            
    except Exception as e:
        from django.http import Http404
        raise Http404(f"Error al descargar el archivo: {str(e)}")

@login_required
def download_delivery_attachment(request, delivery_id):
    """Permite descargar el archivo adjunto de una entrega"""
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    # Verificar permisos: solo el estudiante que entregó, el docente de la clase o admin pueden descargar
    user = request.user
    has_permission = False
    
    if user.role == 'teacher' and delivery.task.school_class.teacher == user:
        has_permission = True
    elif user.role == 'student' and delivery.student == user:
        has_permission = True
    elif user.role == 'admin':
        has_permission = True
    
    if not has_permission:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("No tienes permisos para descargar este archivo.")
    
    # Verificar que la entrega tiene archivo adjunto
    if not delivery.attachment:
        from django.http import Http404
        raise Http404("Esta entrega no tiene archivo adjunto.")
    
    # Servir el archivo
    import os
    from django.http import HttpResponse, Http404
    from django.conf import settings
    
    try:
        file_path = delivery.attachment.path
        
        if not os.path.exists(file_path):
            raise Http404("El archivo no se encuentra en el servidor.")
        
        # Obtener el tipo de contenido
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_path)
        
        # Crear la respuesta HTTP
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{delivery.attachment_name}"'
            response['Content-Length'] = os.path.getsize(file_path)
            return response
            
    except Exception as e:
        from django.http import Http404
        raise Http404(f"Error al descargar el archivo: {str(e)}")

@login_required

def download_corrected_attachment(request, delivery_id):

    """Permite descargar el archivo corregido de una entrega"""

    delivery = get_object_or_404(Delivery, id=delivery_id)

    

    # Verificar permisos: solo el estudiante que entreg��, el docente de la clase o admin pueden descargar

    user = request.user

    has_permission = False

    

    if user.role == 'teacher' and delivery.task.school_class.teacher == user:

        has_permission = True

    elif user.role == 'student' and delivery.student == user:

        has_permission = True

    elif user.role == 'admin':

        has_permission = True

    

    if not has_permission:

        from django.http import HttpResponseForbidden

        return HttpResponseForbidden("No tienes permisos para descargar este archivo.")

    

    # Verificar que la entrega tiene archivo corregido

    if not delivery.corrected_attachment:

        from django.http import Http404

        raise Http404("Esta entrega no tiene archivo corregido.")

    

    # Servir el archivo

    import os

    from django.http import HttpResponse, Http404

    from django.conf import settings

    

    try:

        file_path = delivery.corrected_attachment.path

        

        if not os.path.exists(file_path):

            raise Http404("El archivo no se encuentra en el servidor.")

        

        # Obtener el tipo de contenido

        import mimetypes

        content_type, _ = mimetypes.guess_type(file_path)

        

        # Crear la respuesta HTTP

        with open(file_path, 'rb') as f:

            response = HttpResponse(f.read(), content_type=content_type)

            response['Content-Disposition'] = f'attachment; filename="{delivery.corrected_attachment_name}"'

            response['Content-Length'] = os.path.getsize(file_path)

            return response

            

    except Exception as e:

        from django.http import Http404

        raise Http404(f"Error al descargar el archivo: {str(e)}")

