/**
 * Обробка форми підписки на розсилку (десктоп і мобільна версії)
 */

document.addEventListener('DOMContentLoaded', function() {
    // Десктопна форма
    const desktopForm = document.getElementById('desktopSubscribeForm');
    if (desktopForm) {
        desktopForm.addEventListener('submit', handleSubscribe);
    }
    
    // Мобільна форма
    const mobileForm = document.getElementById('mobileSubscribeForm');
    if (mobileForm) {
        mobileForm.addEventListener('submit', handleSubscribe);
    }
});

function handleSubscribe(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('.btn-subscribe');
    const originalText = submitBtn.textContent;
    
    // Отримуємо дані форми
    const formData = new FormData(form);
    const name = formData.get('name');
    const email = formData.get('email');
    const privacy = form.querySelector('input[name="privacy"]');
    
    // Валідація
    if (!name || !email) {
        showMessage(form, 'Будь ласка, заповніть всі поля', 'error');
        return;
    }
    
    if (privacy && !privacy.checked) {
        showMessage(form, 'Необхідно дати згоду на обробку персональних даних', 'error');
        return;
    }
    
    // Валідація email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMessage(form, 'Введіть коректну email адресу', 'error');
        return;
    }
    
    // Відображення процесу відправки
    submitBtn.textContent = 'Відправка...';
    submitBtn.disabled = true;
    
    // Відправка на сервер
    fetch(form.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken')
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage(form, data.message || 'Дякуємо за підписку!', 'success');
            form.reset();
        } else {
            showMessage(form, data.message || 'Виникла помилка', 'error');
        }
    })
    .catch(error => {
        showMessage(form, 'Помилка з\'єднання з сервером', 'error');
    })
    .finally(() => {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    });
}

function showMessage(form, message, type) {
    // Видаляємо попереднє повідомлення
    const existingMessage = form.querySelector('.subscribe-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Створюємо нове повідомлення
    const messageDiv = document.createElement('div');
    messageDiv.className = `subscribe-message subscribe-message-${type}`;
    messageDiv.textContent = message;
    
    // Вставляємо перед кнопкою
    const submitBtn = form.querySelector('.btn-subscribe');
    form.insertBefore(messageDiv, submitBtn);
    
    // Стилі для повідомлення
    messageDiv.style.padding = '10px 15px';
    messageDiv.style.marginBottom = '15px';
    messageDiv.style.borderRadius = '6px';
    messageDiv.style.fontSize = '0.9rem';
    messageDiv.style.textAlign = 'center';
    messageDiv.style.animation = 'fadeIn 0.3s ease';
    
    if (type === 'success') {
        messageDiv.style.background = 'rgba(76, 175, 80, 0.1)';
        messageDiv.style.color = '#4CAF50';
        messageDiv.style.border = '1px solid rgba(76, 175, 80, 0.3)';
    } else {
        messageDiv.style.background = 'rgba(244, 67, 54, 0.1)';
        messageDiv.style.color = '#F44336';
        messageDiv.style.border = '1px solid rgba(244, 67, 54, 0.3)';
    }
    
    // Автоматично видаляємо через 5 секунд
    setTimeout(() => {
        messageDiv.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            messageDiv.remove();
        }, 300);
    }, 5000);
}

// Додаємо анімації
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeOut {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-10px);
        }
    }
`;
document.head.appendChild(style);

