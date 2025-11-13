document.addEventListener('DOMContentLoaded', function() {
    const liqpayForm = document.getElementById('liqpay-form');
    const submitBtn = document.getElementById('liqpay-submit-btn');
    
    if (!liqpayForm || !submitBtn) {
        return;
    }
    
    liqpayForm.addEventListener('submit', function() {
        if (!submitBtn.disabled) {
            submitBtn.disabled = true;
            submitBtn.classList.add('loading');
            
            setTimeout(function() {
                submitBtn.disabled = false;
                submitBtn.classList.remove('loading');
            }, 30000);
        }
    });
    
    window.addEventListener('pageshow', function(event) {
        if (event.persisted || (window.performance && window.performance.navigation.type === 2)) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('loading');
        }
    });
});

