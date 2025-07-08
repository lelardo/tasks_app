from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
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

# === VISTA PRINCIPAL SIN AUTENTICACIÓN REQUERIDA ===
def home(request):
    """Vista principal que redirige según autenticación"""
    if not request.user.is_authenticated:
        return redirect('login')
    
    tasks = Task.objects.all().order_by('-created_at')[:5]
    recent_deliveries = Delivery.objects.all().order_by('-date')[:5]
    
    context = {
        'tasks': tasks,
        'recent_deliveries': recent_deliveries,
        'user_role': request.user.role,
        'user_role_display': request.user.role_display,
    }
    return render(request, 'apptask/home.html', context)

# === VISTAS DE AUTENTICACIÓN WEB ===
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

# === RESTO DE VISTAS CON @login_required ===
@login_required
def task_list(request):
    """Lista todas las tareas"""
    tasks = Task.objects.all().order_by('-created_at')
    return render(request, 'apptask/task_list.html', {'tasks': tasks})

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
def task_create(request):
    """Crear una nueva tarea"""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Tarea "{task.theme}" creada exitosamente.')
            return redirect('task_detail', task_id=task.id)
    else:
        form = TaskForm()
    
    return render(request, 'apptask/task_form.html', {
        'form': form,
        'title': 'Crear Nueva Tarea'
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