document.addEventListener('DOMContentLoaded', function() {
    const liqpayForm = document.getElementById('liqpay-form');
    const submitBtn = document.getElementById('liqpay-submit-btn');
    
    if (!liqpayForm || !submitBtn) {
        return;
    }
    
    liqpayForm.addEventListener('submit', function(e) {
        if (submitBtn.disabled) {
            e.preventDefault();
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.classList.add('loading');
        
        const btnText = submitBtn.querySelector('.btn-text');
        if (!btnText) {
            const text = submitBtn.textContent;
            submitBtn.innerHTML = `<span class="spinner"></span><span class="btn-text">${text}</span>`;
        }
        
        setTimeout(function() {
            if (submitBtn.disabled) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('loading');
            }
        }, 30000);
    });
    
    window.addEventListener('pageshow', function(event) {
        if (event.persisted || (window.performance && window.performance.navigation.type === 2)) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('loading');
        }
    });
});

