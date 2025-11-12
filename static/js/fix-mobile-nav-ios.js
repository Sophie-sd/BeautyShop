/**
 * Фікс для нижнього меню на iOS Safari
 * Проблема: після входу в особистий кабінет меню відкріпляється
 */
(function() {
    'use strict';
    
    function forceFixBottomNav() {
        const bottomNav = document.querySelector('.mobile-bottom-nav');
        
        if (!bottomNav) return;
        
        // Примусово застосовуємо стилі для фіксації
        bottomNav.style.position = 'fixed';
        bottomNav.style.bottom = '0';
        bottomNav.style.left = '0';
        bottomNav.style.right = '0';
        bottomNav.style.width = '100%';
        bottomNav.style.zIndex = '9999';
        bottomNav.style.transform = 'translate3d(0, 0, 0)';
        bottomNav.style.webkitTransform = 'translate3d(0, 0, 0)';
        bottomNav.style.backfaceVisibility = 'hidden';
        bottomNav.style.webkitBackfaceVisibility = 'hidden';
    }
    
    function checkAndFix() {
        // Виправляємо при завантаженні
        forceFixBottomNav();
        
        // Виправляємо після невеликої затримки (для динамічного контенту)
        setTimeout(forceFixBottomNav, 100);
        setTimeout(forceFixBottomNav, 300);
        setTimeout(forceFixBottomNav, 500);
        
        // Виправляємо при скролі (тільки перший раз)
        let scrollFixed = false;
        const onScroll = function() {
            if (!scrollFixed) {
                forceFixBottomNav();
                scrollFixed = true;
                window.removeEventListener('scroll', onScroll);
            }
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        
        // Виправляємо при зміні орієнтації
        window.addEventListener('orientationchange', function() {
            setTimeout(forceFixBottomNav, 100);
        });
    }
    
    // Запускаємо при завантаженні DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkAndFix);
    } else {
        checkAndFix();
    }
    
    // Також запускаємо після повного завантаження
    window.addEventListener('load', checkAndFix);
    
    // Виправляємо при поверненні до сторінки (bfcache в Safari)
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            checkAndFix();
        }
    });
})();

