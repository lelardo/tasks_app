from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # === URLs BÁSICAS ===
    path('login/', views.user_login_page, name='login'),
    path('logout/', views.user_logout_view, name='logout'),
    path('', views.home, name='home'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('change-password/', views.user_change_password, name='change_password'),
    path('profile/', views.user_profile_page, name='profile'),  # Agregar esta línea
    
    
    # === URLs DE ADMINISTRACIÓN ===
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_user_list, name='admin_user_list'),
    path('admin-panel/users/create/', views.admin_user_create, name='admin_user_create'),
    path('admin-panel/classes/', views.admin_class_list, name='admin_class_list'),
    path('admin-panel/config/', views.admin_system_config, name='admin_system_config'),
    path('admin-panel/backup/download/<str:filename>/', views.admin_download_backup, name='admin_download_backup'),  # Nueva URL
    # === URLs DE ADMINISTRACIÓN ===
    path('admin-panel/users/edit/<int:user_id>/', views.admin_user_edit, name='admin_user_edit'),
    #path('admin-panel/classes/create/', views.admin_class_create, name='admin_class_create'),
    
    # === URLs PARA DOCENTES ===
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/tasks/', views.teacher_task_list, name='teacher_task_list'),
    path('teacher/tasks/create/', views.teacher_task_create, name='teacher_task_create'),
    path('teacher/tasks/<int:task_id>/', views.teacher_task_detail, name='teacher_task_detail'),
    path('teacher/deliveries/', views.teacher_delivery_list, name='teacher_delivery_list'),
    path('teacher/deliveries/<int:delivery_id>/grade/', views.teacher_delivery_grade, name='teacher_delivery_grade'),
    
    
    # === URLs PARA ESTUDIANTES ===
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('tasks/', views.student_task_list, name='student_task_list'),
    path('student/tasks/<int:task_id>/', views.student_task_detail, name='student_task_detail'),
    path('student/tasks/<int:task_id>/deliver/', views.student_delivery_create, name='delivery_create'),
    path('student/deliveries/', views.student_delivery_list, name='student_delivery_list'),
    path('student/deliveries/<int:delivery_id>/edit/', views.student_delivery_edit, name='delivery_edit'),
    path('student/notifications/', views.student_notifications, name='student_notifications'),
    path('student/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    # === URLs PARA TAREAS ===
    path('tasks/<int:task_id>/edit/', views.task_edit, name='task_edit'),   
    path('tasks/<int:task_id>/delete/', views.task_delete, name='task_delete'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/download/', views.download_task_attachment, name='download_task_attachment'),
    path('deliveries/<int:delivery_id>/download/', views.download_delivery_attachment, name='download_delivery_attachment'),
    path('deliveries/<int:delivery_id>/download-corrected/', views.download_corrected_attachment, name='download_corrected_attachment'),
    path('deliveries/<int:delivery_id>/grade/', views.delivery_grade, name='delivery_grade'),
    path('deliveries/<int:delivery_id>/edit-grade/', views.delivery_edit_grade, name='delivery_edit_grade'),
    
    path('api/auth/register/', views.UserRegistrationView.as_view(), name='api_register'),
    path('api/auth/login/', views.UserLoginView.as_view(), name='api_login'),
    path('api/auth/logout/', views.UserLogoutView.as_view(), name='api_logout'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/auth/profile/', views.UserProfileView.as_view(), name='api_profile'),
    path('api/users/', views.UserListView.as_view(), name='api_users'),

    # === URLs PARA OBSERVADORES ===
    path('observer/', views.observer_dashboard, name='observer_dashboard'),
    path('observer/reports/', views.observer_reports, name='observer_reports'),
    path('observer/academic/', views.observer_academic_overview, name='observer_academic_overview'),
    path('observer/export/', views.observer_export_report, name='observer_export_report'),
]