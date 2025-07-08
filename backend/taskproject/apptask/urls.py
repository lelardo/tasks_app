from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # === URLs DE AUTENTICACIÓN (primero) ===
    path('login/', views.user_login_page, name='login'),
    path('logout/', views.user_logout_view, name='logout'),
    path('register/', views.user_register_page, name='register'),  # Agregar esta línea
    path('profile/', views.user_profile_page, name='profile'),  # Agregar esta línea
    path('change-password/', views.change_password_view, name='change_password'),  # Agregar esta línea
    
    
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
    path('deliveries/<int:delivery_id>/edit-grade/', views.delivery_edit_grade, name='delivery_edit_grade'),

    # === NUEVAS URLs API USUARIOS ===
    path('api/auth/register/', views.UserRegistrationView.as_view(), name='api_register'),
    path('api/auth/login/', views.UserLoginView.as_view(), name='api_login'),
    path('api/auth/logout/', views.UserLogoutView.as_view(), name='api_logout'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/auth/profile/', views.UserProfileView.as_view(), name='api_profile'),
    path('api/users/', views.UserListView.as_view(), name='api_users'),
    
]
