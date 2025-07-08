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
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer,
    UserProfileSerializer,
    UserListSerializer
)

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
        return redirect('admin_dashboard')
    elif request.user.role == 'teacher':
        return redirect('teacher_dashboard')
    elif request.user.role == 'student':
        return redirect('student_dashboard')
    else:
        # Para usuarios sin rol específico, mostrar dashboard general
        tasks = Task.objects.all().order_by('-created_at')[:5]
        recent_deliveries = Delivery.objects.all().order_by('-date')[:5]
        
        context = {
            'tasks': tasks,
            'recent_deliveries': recent_deliveries,
            'user_role': request.user.role,
            'user_role_display': request.user.role_display,
        }
        return render(request, 'apptask/home.html', context)

# === VISTAS ESPECÍFICAS POR ROL ===

# DASHBOARDS POR ROL
@login_required
@user_passes_test(admin_required)
def admin_dashboard(request):
    """Dashboard para administradores"""
    total_users = User.objects.count()
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_admins = User.objects.filter(role='admin').count()
    total_classes = SchoolClass.objects.count()
    total_tasks = Task.objects.count()
    
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_classes = SchoolClass.objects.order_by('-id')[:5]
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_admins': total_admins,
        'total_classes': total_classes,
        'total_tasks': total_tasks,
        'recent_users': recent_users,
        'recent_classes': recent_classes,
    }
    return render(request, 'apptask/admin/dashboard.html', context)

@login_required
@user_passes_test(teacher_required)
def teacher_dashboard(request):
    """Dashboard para docentes"""
    teacher = request.user
    my_classes = teacher.taught_classes.all()
    my_tasks = Task.objects.filter(school_class__teacher=teacher)
    pending_deliveries = Delivery.objects.filter(
        task__school_class__teacher=teacher,
        grade__isnull=True
    )
    recent_deliveries = Delivery.objects.filter(
        task__school_class__teacher=teacher
    ).order_by('-date')[:5]
    
    context = {
        'my_classes': my_classes,
        'my_tasks': my_tasks,
        'pending_deliveries': pending_deliveries,
        'recent_deliveries': recent_deliveries,
        'total_classes': my_classes.count(),
        'total_tasks': my_tasks.count(),
        'pending_count': pending_deliveries.count(),
    }
    return render(request, 'apptask/teacher/dashboard.html', context)

@login_required
@user_passes_test(student_required)
def student_dashboard(request):
    """Dashboard para estudiantes"""
    student = request.user
    my_classes = student.classes.all()
    available_tasks = Task.objects.filter(school_class__in=my_classes)
    my_deliveries = student.deliveries.all()
    pending_tasks = available_tasks.exclude(
        id__in=my_deliveries.values_list('task_id', flat=True)
    )
    
    context = {
        'my_classes': my_classes,
        'available_tasks': available_tasks,
        'my_deliveries': my_deliveries,
        'pending_tasks': pending_tasks,
        'total_classes': my_classes.count(),
        'total_deliveries': my_deliveries.count(),
        'pending_count': pending_tasks.count(),
    }
    return render(request, 'apptask/student/dashboard.html', context)

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
    
    context = {
        'classes': classes,
    }
    return render(request, 'apptask/admin/class_list.html', context)

@login_required
@user_passes_test(admin_required)
def admin_class_create(request):
    """Crear nueva clase (solo admin)"""
    if request.method == 'POST':
        identify = request.POST.get('identify')
        course = request.POST.get('course')
        teacher_id = request.POST.get('teacher')
        student_ids = request.POST.getlist('students')  # getlist para múltiples checkboxes
        
        # Validar que no exista una clase con el mismo identificador
        if SchoolClass.objects.filter(identify=identify).exists():
            messages.error(request, 'Ya existe una clase con este identificador.')
            teachers = User.objects.filter(role='teacher')
            students = User.objects.filter(role='student')
            return render(request, 'apptask/admin/class_form.html', {
                'teachers': teachers,
                'students': students,
                'form_data': request.POST,
                'title': 'Crear Nueva Clase'
            })
        
        try:
            teacher = User.objects.get(id=teacher_id, role='teacher')
            school_class = SchoolClass.objects.create(
                identify=identify,
                course=course,
                teacher=teacher
            )
            
            # Agregar estudiantes a la clase
            if student_ids:
                students = User.objects.filter(id__in=student_ids, role='student')
                school_class.student_list.add(*students)
            
            messages.success(request, f'Clase {school_class.identify} creada exitosamente con {len(student_ids)} estudiantes.')
            return redirect('admin_class_list')
            
        except Exception as e:
            messages.error(request, f'Error al crear clase: {str(e)}')
    
    teachers = User.objects.filter(role='teacher')
    students = User.objects.filter(role='student').order_by('first_name', 'last_name')
    
    context = {
        'teachers': teachers,
        'students': students,
        'title': 'Crear Nueva Clase'
    }
    return render(request, 'apptask/admin/class_form.html', context)

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

# === GESTIÓN DE TAREAS (SOLO DOCENTES) ===
@login_required
@user_passes_test(teacher_required)
def task_list(request):
    """Lista de tareas del docente"""
    teacher = request.user
    tasks = Task.objects.filter(school_class__teacher=teacher).order_by('-created_at')
    
    context = {
        'tasks': tasks,
    }
    return render(request, 'apptask/teacher/task_list.html', context)

@login_required
@user_passes_test(teacher_required)
def task_create(request):
    """Crear nueva tarea (solo docentes)"""
    teacher = request.user
    
    if request.method == 'POST':
        form = TaskForm(request.POST)
        # Filtrar solo las clases del docente
        form.fields['school_class'].queryset = teacher.taught_classes.all()
        
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Tarea "{task.theme}" creada exitosamente.')
            return redirect('task_detail', task_id=task.id)
    else:
        form = TaskForm()
        # Filtrar solo las clases del docente
        form.fields['school_class'].queryset = teacher.taught_classes.all()
    
    return render(request, 'apptask/teacher/task_form.html', {
        'form': form,
        'title': 'Crear Nueva Tarea'
    })

# === VISTAS PARA ESTUDIANTES ===
@login_required
@user_passes_test(student_required)
def student_task_list(request):
    """Lista de tareas disponibles para el estudiante"""
    student = request.user
    available_tasks = Task.objects.filter(school_class__in=student.classes.all())
    
    context = {
        'tasks': available_tasks,
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
def task_edit(request, task_id):
    """Editar una tarea existente"""
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Tarea "{task.theme}" actualizada exitosamente.')
            return redirect('task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'apptask/task_form.html', {
        'form': form,
        'title': 'Editar Tarea',
        'task': task
    })

@login_required
def delivery_create(request, task_id):
    """Crear una nueva entrega para una tarea"""
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        form = DeliveryForm(request.POST, task=task)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.task = task
            delivery.date = timezone.now().date()
            delivery.delivery_time = timezone.now().time()
            # Por ahora asignamos un profesor por defecto como revisor
            delivery.revisor = User.objects.filter(role='teacher').first()
            delivery.save()
            messages.success(request, 'Entrega realizada exitosamente.')
            return redirect('task_detail', task_id=task.id)
    else:
        form = DeliveryForm(task=task)
    
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