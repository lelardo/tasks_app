from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponseRedirect
from .models import SessionConfig
import json
import logging

logger = logging.getLogger(__name__)

class SessionTimeoutMiddleware:
    """Middleware para manejar el timeout de sesiones"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Solo procesar si el usuario está autenticado
        if request.user.is_authenticated:
            try:
                # Obtener configuración de sesión
                session_config = SessionConfig.get_config()
                
                if session_config and session_config.enable_session_timeout:
                    # Obtener timestamp de última actividad
                    last_activity = request.session.get('last_activity')
                    current_time = timezone.now().timestamp()
                    
                    # Si es la primera vez, establecer timestamp inicial
                    if not last_activity:
                        request.session['last_activity'] = current_time
                        request.session.modified = True
                    else:
                        # Calcular tiempo transcurrido en minutos
                        elapsed_minutes = (current_time - last_activity) / 60
                        
                        # Verificar si se ha excedido el timeout
                        if elapsed_minutes >= session_config.session_timeout_minutes:
                            # Cerrar sesión
                            logout(request)
                            messages.warning(request, f'Su sesión ha expirado por inactividad después de {session_config.session_timeout_minutes} minutos. Por favor, inicie sesión nuevamente.')
                            return HttpResponseRedirect('/login/')
                        
                        # Verificar si mostrar advertencia
                        warning_threshold = session_config.session_timeout_minutes - session_config.warning_time_minutes
                        if session_config.show_timeout_warning and elapsed_minutes >= warning_threshold:
                            # Agregar información de timeout a la sesión para JavaScript
                            remaining_minutes = session_config.session_timeout_minutes - int(elapsed_minutes)
                            request.session['show_timeout_warning'] = True
                            request.session['timeout_warning_minutes'] = max(1, remaining_minutes)
                            request.session.modified = True
                        else:
                            # Limpiar advertencia si no es necesario
                            request.session.pop('show_timeout_warning', None)
                            request.session.pop('timeout_warning_minutes', None)
                            request.session.modified = True
                    
                    # NO actualizar last_activity aquí - solo se actualiza cuando el usuario hace una acción consciente
                    
            except Exception as e:
                logger.error(f"Error en SessionTimeoutMiddleware: {str(e)}")
        
        response = self.get_response(request)
        return response