document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const submitButton = document.querySelector('.user-action-btn-save');
    const formFields = form.querySelectorAll('input[type="text"], input[type="email"], input[type="tel"]');
    
    const originalValues = {};
    formFields.forEach(field => {
        originalValues[field.name] = field.value;
    });
    
    function checkForChanges() {
        let hasChanges = false;
        
        formFields.forEach(field => {
            if (field.value !== originalValues[field.name]) {
                hasChanges = true;
            }
        });
        
        if (hasChanges) {
            submitButton.disabled = false;
            submitButton.classList.remove('user-action-btn-disabled');
        } else {
            submitButton.disabled = true;
            submitButton.classList.add('user-action-btn-disabled');
        }
    }
    
    formFields.forEach(field => {
        field.addEventListener('input', checkForChanges);
        field.addEventListener('change', checkForChanges);
    });
    
    checkForChanges();
}); 