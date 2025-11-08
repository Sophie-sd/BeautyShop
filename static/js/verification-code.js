document.addEventListener('DOMContentLoaded', function() {
    const codeInput = document.querySelector('.code-input');
    const resendBtn = document.getElementById('resendBtn');
    const resendTimer = document.getElementById('resendTimer');
    const codeForm = document.getElementById('codeForm');
    
    let countdownTime = 60;
    let countdownInterval = null;
    
    if (codeInput) {
        codeInput.focus();
        
        codeInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length > 6) {
                value = value.substring(0, 6);
            }
            
            e.target.value = value;
            
            if (value.length === 6) {
                codeForm.querySelector('button[type="submit"]').focus();
            }
        });
        
        codeInput.addEventListener('paste', function(e) {
            e.preventDefault();
            const pastedText = (e.clipboardData || window.clipboardData).getData('text');
            const digits = pastedText.replace(/\D/g, '').substring(0, 6);
            codeInput.value = digits;
            
            if (digits.length === 6) {
                codeForm.querySelector('button[type="submit"]').focus();
            }
        });
    }
    
    function startCountdown() {
        resendBtn.disabled = true;
        resendBtn.classList.add('disabled');
        countdownTime = 60;
        
        updateCountdownDisplay();
        
        countdownInterval = setInterval(function() {
            countdownTime--;
            updateCountdownDisplay();
            
            if (countdownTime <= 0) {
                clearInterval(countdownInterval);
                resendBtn.disabled = false;
                resendBtn.classList.remove('disabled');
                resendTimer.textContent = '';
            }
        }, 1000);
    }
    
    function updateCountdownDisplay() {
        if (countdownTime > 0) {
            resendTimer.textContent = `Повторно надіслати можна через ${countdownTime} сек`;
        } else {
            resendTimer.textContent = '';
        }
    }
    
    startCountdown();
    
    if (resendBtn) {
        const scriptTag = document.querySelector('script[data-resend-url]');
        let resendUrl = scriptTag ? scriptTag.getAttribute('data-resend-url') : '';
        
        if (!resendUrl) {
            const currentPath = window.location.pathname;
            if (currentPath.includes('password')) {
                resendUrl = '/users/password/reset/resend-code/';
            } else {
                resendUrl = '/users/resend-verification-code/';
            }
        }
        
        resendBtn.addEventListener('click', function() {
            if (this.disabled) return;
            
            const originalText = this.textContent;
            this.textContent = 'Відправка...';
            this.disabled = true;
            
            fetch(resendUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage(data.message, 'success');
                    startCountdown();
                } else {
                    showMessage(data.message, 'error');
                    this.disabled = false;
                    this.textContent = originalText;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showMessage('Помилка при відправці коду. Спробуйте ще раз.', 'error');
                this.disabled = false;
                this.textContent = originalText;
            });
        });
    }
    
    function showMessage(message, type) {
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.textContent = message;
        
        const authCard = document.querySelector('.auth-card');
        const authHeader = document.querySelector('.auth-header');
        authCard.insertBefore(alertDiv, authHeader.nextSibling);
        
        setTimeout(() => {
            alertDiv.style.transition = 'opacity 0.3s';
            alertDiv.style.opacity = '0';
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    }
    
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
    
    codeForm.addEventListener('submit', function() {
        const submitBtn = this.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Перевірка...';
    });
});

