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
    }

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

