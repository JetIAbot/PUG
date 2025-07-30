class FormValidator {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.errors = {};
        this.init();
    }
    
    init() {
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
            this.addRealTimeValidation();
        }
    }
    
    addRealTimeValidation() {
        const inputs = this.form.querySelectorAll('input[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
            input.addEventListener('input', () => this.clearFieldError(input));
        });
    }
    
    validateField(input) {
        const fieldName = input.name;
        const value = input.value.trim();
        
        // Limpiar errores previos
        this.clearFieldError(input);
        
        switch(fieldName) {
            case 'matricola':
                return this.validateMatricola(input, value);
            case 'password':
            case 'contrasena':
                return this.validatePassword(input, value);
            case 'vencimiento_licencia':
                return this.validateExpiryDate(input, value);
            default:
                return true;
        }
    }
    
    validateMatricola(input, value) {
        const pattern = /^[0-9]{6,8}$/;
        
        if (!value) {
            this.addFieldError(input, 'La matrícula es obligatoria');
            return false;
        }
        
        if (!pattern.test(value)) {
            this.addFieldError(input, 'La matrícula debe tener entre 6 y 8 dígitos');
            return false;
        }
        
        this.addFieldSuccess(input);
        return true;
    }
    
    validatePassword(input, value) {
        if (!value) {
            this.addFieldError(input, 'La contraseña es obligatoria');
            return false;
        }
        
        if (value.length < 3) {
            this.addFieldError(input, 'La contraseña es demasiado corta');
            return false;
        }
        
        this.addFieldSuccess(input);
        return true;
    }
    
    validateExpiryDate(input, value) {
        if (value) {
            const date = new Date(value);
            const today = new Date();
            
            if (date <= today) {
                this.addFieldError(input, 'La fecha de vencimiento debe ser futura');
                return false;
            }
            
            this.addFieldSuccess(input);
        }
        
        return true;
    }
    
    addFieldError(input, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        
        input.classList.add('error');
        input.classList.remove('success');
        input.parentNode.appendChild(errorDiv);
        
        this.errors[input.name] = message;
    }
    
    addFieldSuccess(input) {
        input.classList.add('success');
        input.classList.remove('error');
        delete this.errors[input.name];
    }
    
    clearFieldError(input) {
        input.classList.remove('error', 'success');
        const errorDiv = input.parentNode.querySelector('.field-error');
        if (errorDiv) {
            errorDiv.remove();
        }
        delete this.errors[input.name];
    }
    
    handleSubmit(e) {
        console.log('Form submit triggered');
        
        // Validar todos los campos
        const inputs = this.form.querySelectorAll('input[required]');
        let isValid = true;
        
        console.log('Found inputs:', inputs.length);
        
        inputs.forEach(input => {
            const fieldValid = this.validateField(input);
            console.log(`Field ${input.name}: ${fieldValid ? 'valid' : 'invalid'}`);
            if (!fieldValid) {
                isValid = false;
            }
        });
        
        console.log('Overall form valid:', isValid);
        
        if (!isValid) {
            e.preventDefault();
            this.showGeneralError('Por favor, corrige los errores en el formulario');
            return false;
        }
        
        // Mostrar indicador de carga
        this.showLoadingIndicator();
        return true;
    }
    
    showGeneralError(message) {
        const existingError = document.querySelector('.form-general-error');
        if (existingError) {
            existingError.remove();
        }
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'form-general-error alert alert-danger';
        errorDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            ${message}
        `;
        
        this.form.insertBefore(errorDiv, this.form.firstChild);
        
        // Scroll al error
        errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    showLoadingIndicator() {
        const submitButton = this.form.querySelector('button[type="submit"]');
        if (submitButton) {
            const originalText = submitButton.innerHTML;
            submitButton.innerHTML = `
                <span class="spinner-border spinner-border-sm" role="status"></span>
                Procesando...
            `;
            submitButton.disabled = true;
            
            // Guardar texto original para posible restauración
            submitButton.dataset.originalText = originalText;
        }
        
        // Mostrar indicador de progreso si existe
        const progressIndicator = document.getElementById('loadingIndicator');
        if (progressIndicator) {
            progressIndicator.classList.add('active');
        }
    }
}

// Utilidades adicionales
class ProgressTracker {
    constructor() {
        this.progressBar = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
    }
    
    updateProgress(percentage, text) {
        if (this.progressBar) {
            this.progressBar.style.width = `${percentage}%`;
        }
        
        if (this.progressText && text) {
            this.progressText.textContent = text;
        }
    }
    
    simulateProgress() {
        let progress = 0;
        const messages = [
            'Conectando al portal universitario...',
            'Autenticando credenciales...',
            'Extrayendo datos personales...',
            'Procesando horarios académicos...',
            'Finalizando extracción...'
        ];
        
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                this.updateProgress(progress, 'Completado');
            } else {
                const messageIndex = Math.floor((progress / 100) * messages.length);
                this.updateProgress(progress, messages[messageIndex] || 'Procesando...');
            }
        }, 1000);
    }
}

// Inicializar validadores cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Formulario principal de estudiantes
    const studentForm = document.getElementById('studentForm');
    if (studentForm) {
        const validator = new FormValidator('studentForm');
        
        // Inicializar tracking de progreso si está en página de extracción
        if (window.location.pathname === '/revisar') {
            const tracker = new ProgressTracker();
            tracker.simulateProgress();
        }
    }
    
    // Formulario de admin
    const adminForm = document.getElementById('adminForm');
    if (adminForm) {
        new FormValidator('adminForm');
    }
    
    // Mejorar mensajes flash
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        // Auto-dismiss después de 5 segundos para mensajes de éxito
        if (message.classList.contains('alert-success')) {
            setTimeout(() => {
                message.style.opacity = '0';
                setTimeout(() => message.remove(), 300);
            }, 5000);
        }
    });
});
