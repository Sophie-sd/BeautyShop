(function() {
    'use strict';
    
    document.addEventListener('DOMContentLoaded', function() {
        const sendTypeRadios = document.querySelectorAll('input[name="send_type"]');
        const scheduledAtField = document.querySelector('.field-scheduled_at');
        
        if (!sendTypeRadios.length || !scheduledAtField) {
            return;
        }
        
        function toggleScheduledField() {
            const selectedValue = document.querySelector('input[name="send_type"]:checked');
            if (selectedValue && selectedValue.value === 'scheduled') {
                scheduledAtField.style.display = '';
            } else {
                scheduledAtField.style.display = 'none';
                const input = scheduledAtField.querySelector('input[type="datetime-local"]');
                if (input) {
                    input.value = '';
                }
            }
        }
        
        sendTypeRadios.forEach(function(radio) {
            radio.addEventListener('change', toggleScheduledField);
        });
        
        toggleScheduledField();
    });
})();

