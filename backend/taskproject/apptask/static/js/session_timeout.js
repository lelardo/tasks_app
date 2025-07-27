// Script para manejar advertencias de timeout de sesión
document.addEventListener('DOMContentLoaded', function() {
    console.log('Session timeout script loaded');
    
    // Verificar si hay advertencia de timeout en la sesión
    if (typeof sessionTimeoutWarning !== 'undefined' && sessionTimeoutWarning) {
        console.log('Showing timeout warning for', sessionTimeoutWarningMinutes, 'minutes');
        showTimeoutWarning(sessionTimeoutWarningMinutes);
    }

    // Función para mostrar contador de tiempo restante
    function showTimeCounter(minutes) {
        // Remover contador existente si hay uno
        const existingCounter = document.getElementById('session-time-counter');
        if (existingCounter) {
            existingCounter.remove();
        }
        
        const counterDiv = document.createElement('div');
        counterDiv.id = 'session-time-counter';
        counterDiv.className = 'position-fixed';
        counterDiv.style.cssText = 'top: 20px; left: 20px; z-index: 9998; background: rgba(0,0,0,0.8); color: white; padding: 10px; border-radius: 5px; font-size: 14px;';
        
        let timeLeft = minutes * 60; // Convertir a segundos
        
        function updateCounter() {
            const minutesLeft = Math.floor(timeLeft / 60);
            const secondsLeft = timeLeft % 60;
            counterDiv.innerHTML = `
                <i class="bi bi-clock"></i> 
                Sesión expira en: <strong>${minutesLeft}:${secondsLeft.toString().padStart(2, '0')}</strong>
            `;
            
            if (timeLeft <= 0) {
                counterDiv.remove();
                return;
            }
            
            timeLeft--;
            setTimeout(updateCounter, 1000);
        }
        
        document.body.appendChild(counterDiv);
        updateCounter();
    }
    
    // Función para mostrar advertencia de timeout
    function showTimeoutWarning(minutes) {
        // Remover advertencia existente si hay una
        const existingWarning = document.getElementById('session-timeout-warning');
        if (existingWarning) {
            existingWarning.remove();
        }
        
        const warningDiv = document.createElement('div');
        warningDiv.id = 'session-timeout-warning';
        warningDiv.className = 'alert alert-warning alert-dismissible fade show position-fixed';
        warningDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);';
        warningDiv.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-exclamation-triangle-fill me-2" style="font-size: 1.2em; color: #ffc107;"></i>
                <div>
                    <strong>Advertencia de Sesión</strong><br>
                    Su sesión expirará en <strong>${minutes} minutos</strong> por inactividad.
                </div>
            </div>
            <div class="mt-2">
                <button type="button" class="btn btn-sm btn-outline-warning me-2" onclick="extendSession()">
                    <i class="bi bi-arrow-clockwise"></i> Extender Sesión
                </button>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.appendChild(warningDiv);
        
        // Auto-ocultar después de 30 segundos
        setTimeout(() => {
            if (warningDiv.parentNode) {
                warningDiv.remove();
            }
        }, 30000);
        
        console.log('Timeout warning displayed:', minutes, 'minutes remaining');
    }
    
    // Función para extender la sesión (global para que pueda ser llamada desde el botón)
    window.extendSession = function() {
        fetch('/extend-session/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Sesión extendida exitosamente');
                // Remover advertencia
                const warningDiv = document.getElementById('session-timeout-warning');
                if (warningDiv) {
                    warningDiv.remove();
                }
                // Mostrar mensaje de éxito
                showSuccessMessage('Sesión extendida exitosamente');
                // Recargar la página para actualizar las variables de sesión
                setTimeout(() => {
                    location.reload();
                }, 2000);
            }
        })
        .catch(error => {
            console.error('Error al extender sesión:', error);
            showErrorMessage('Error al extender la sesión');
        });
    };
    
    // Función para mostrar mensaje de éxito
    function showSuccessMessage(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
        successDiv.style.cssText = 'top: 80px; right: 20px; z-index: 9999; max-width: 300px;';
        successDiv.innerHTML = `
            <i class="bi bi-check-circle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(successDiv);
        
        setTimeout(() => {
            if (successDiv.parentNode) {
                successDiv.remove();
            }
        }, 5000);
    }
    
    // Función para mostrar mensaje de error
    function showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        errorDiv.style.cssText = 'top: 80px; right: 20px; z-index: 9999; max-width: 300px;';
        errorDiv.innerHTML = `
            <i class="bi bi-exclamation-circle"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    // Función para obtener cookie CSRF
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // NO extender automáticamente la sesión con movimientos del mouse
    // Solo extender cuando el usuario hace clic en el botón "Extender Sesión"
    
    // Debug: mostrar información de la sesión
    console.log('Session timeout variables:', {
        sessionTimeoutWarning: typeof sessionTimeoutWarning !== 'undefined' ? sessionTimeoutWarning : 'undefined',
        sessionTimeoutWarningMinutes: typeof sessionTimeoutWarningMinutes !== 'undefined' ? sessionTimeoutWarningMinutes : 'undefined'
    });
});