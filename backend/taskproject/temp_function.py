@login_required
def download_corrected_attachment(request, delivery_id):
    """Permite descargar el archivo corregido de una entrega"""
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
