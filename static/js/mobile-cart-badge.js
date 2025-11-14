/**
 * Оновлення badge кошика в мобільній навігації
 * Без inline стилів, тільки через CSS класи
 */

(function() {
    'use strict';

    /**
     * Оновлення badge мобільного кошика
     */
    function updateMobileCartBadge(count) {
        const mobileCartBadge = document.getElementById('mobileCartBadge');
        
        if (!mobileCartBadge) {
            return;
        }

        if (count > 0) {
            mobileCartBadge.textContent = count;
            mobileCartBadge.classList.remove('nav-badge-hidden');
        } else {
            mobileCartBadge.textContent = '';
            mobileCartBadge.classList.add('nav-badge-hidden');
        }
        
        // iOS Safari fix: примусове оновлення DOM
        mobileCartBadge.style.display = 'none';
        mobileCartBadge.offsetHeight; // Force reflow
        mobileCartBadge.style.display = '';
        
        // Примусове перемальовування для iOS Safari
        if (isIOSSafari()) {
            requestAnimationFrame(() => {
                document.body.style.transform = 'translateZ(0)';
                setTimeout(() => {
                    document.body.style.transform = '';
                }, 0);
            });
        }
    }
    
    /**
     * Перевірка чи це iOS Safari
     */
    function isIOSSafari() {
        const ua = window.navigator.userAgent;
        const iOS = !!ua.match(/iPad/i) || !!ua.match(/iPhone/i);
        const webkit = !!ua.match(/WebKit/i);
        const iOSSafari = iOS && webkit && !ua.match(/CriOS/i);
        return iOSSafari;
    }

    /**
     * Отримання кількості товарів з кошика через AJAX
     */
    async function fetchCartCount() {
        try {
            const response = await fetch('/cart/api/count/', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            });

            if (!response.ok) {
                console.warn('Не вдалося отримати кількість товарів у кошику');
                return 0;
            }

            const data = await response.json();
            return data.count || 0;
        } catch (error) {
            console.error('Помилка при отриманні кількості товарів:', error);
            return 0;
        }
    }

    /**
     * Ініціалізація при завантаженні сторінки
     */
    function init() {
        // Оновлюємо badge при завантаженні
        fetchCartCount().then(count => {
            updateMobileCartBadge(count);
        });

        // Слухаємо події додавання/видалення товарів
        document.addEventListener('cart:updated', function(event) {
            const count = event.detail?.count || 0;
            updateMobileCartBadge(count);
        });

        // Слухаємо події з localStorage (для синхронізації між вкладками)
        window.addEventListener('storage', function(event) {
            if (event.key === 'cart_count') {
                const count = parseInt(event.newValue) || 0;
                updateMobileCartBadge(count);
            }
        });
    }

    // Запускаємо при завантаженні DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Експортуємо функцію для використання в інших скриптах
    window.updateMobileCartBadge = updateMobileCartBadge;
})();

