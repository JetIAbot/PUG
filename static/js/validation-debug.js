// Script de validación simplificado - DESHABILITADO PARA DEPURACIÓN
console.log('Validation script loaded - VALIDATION DISABLED');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    const form = document.getElementById('studentForm');
    console.log('Form found:', form);
    
    if (form) {
        form.addEventListener('submit', function(e) {
            console.log('Form submission detected - ALLOWING ALL SUBMISSIONS');
            
            const matricola = document.getElementById('matricola').value.trim();
            const password = document.getElementById('password').value.trim();
            
            console.log('Matricola:', matricola);
            console.log('Password length:', password.length);
            console.log('Form validation BYPASSED - allowing submission');
            
            // NO VALIDATION - PERMITIR SIEMPRE EL ENVÍO
            return true;
        });
    }
});
