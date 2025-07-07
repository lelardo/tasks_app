from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    
    # URLs para tareas
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),
    
    # URLs para entregas
    path('tasks/<int:task_id>/deliver/', views.delivery_create, name='delivery_create'),
    path('deliveries/', views.delivery_list, name='delivery_list'),
    path('deliveries/<int:delivery_id>/grade/', views.delivery_grade, name='delivery_grade'),
]
