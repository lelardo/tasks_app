from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Task, Delivery, SchoolClass, User
from .forms import TaskForm, DeliveryForm, GradeDeliveryForm


def home(request):
    """Vista principal que muestra el dashboard"""
    tasks = Task.objects.all().order_by('-created_at')[:5]
    recent_deliveries = Delivery.objects.all().order_by('-date')[:5]
    
    context = {
        'tasks': tasks,
        'recent_deliveries': recent_deliveries,
    }
    return render(request, 'apptask/home.html', context)


def task_list(request):
    """Lista todas las tareas"""
    tasks = Task.objects.all().order_by('-created_at')
    return render(request, 'apptask/task_list.html', {'tasks': tasks})


def task_detail(request, task_id):
    """Detalle de una tarea específica"""
    task = get_object_or_404(Task, id=task_id)
    deliveries = task.delivery_list.all()
    return render(request, 'apptask/task_detail.html', {
        'task': task,
        'deliveries': deliveries
    })


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


def delivery_create(request, task_id):
    """Crear una nueva entrega para una tarea"""
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        form = DeliveryForm(request.POST, task=task)
        if form.is_valid():
            delivery = form.save(commit=False)
            delivery.task = task
            delivery.date = timezone.now().date()
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


def delivery_list(request):
    """Lista todas las entregas"""
    deliveries = Delivery.objects.all().order_by('-date')
    return render(request, 'apptask/delivery_list.html', {'deliveries': deliveries})
