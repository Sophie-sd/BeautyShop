/**
 * Фікс для нижнього меню на iOS Safari
 * Проблема: після навігації меню може відкріплятися від низу екрану
 * Рішення: видалення всіх transform на батьківських елементах та легкий repaint
 */
(function() {
    'use strict';
    
    function forceFixBottomNav() {
        const bottomNav = document.querySelector('.mobile-bottom-nav');
        
        if (!bottomNav) return;
        
        // Примусово застосовуємо стилі для фіксації без transform
        bottomNav.style.position = 'fixed';
        bottomNav.style.bottom = '0';
        bottomNav.style.left = '0';
        bottomNav.style.right = '0';
        bottomNav.style.width = '100%';
        bottomNav.style.zIndex = '1000';
        
        // Переконуємось, що на body та html немає transform
        document.documentElement.style.transform = 'none';
        document.documentElement.style.perspective = 'none';
        document.body.style.transform = 'none';
        document.body.style.perspective = 'none';
        
        // Легкий repaint для iOS Safari (тимчасовий translateZ)
        bottomNav.style.transform = 'translateZ(0)';
        requestAnimationFrame(function() {
            bottomNav.style.transform = 'none';
        });
    }
    
    function checkAndFix() {
        // Виправляємо при завантаженні
        forceFixBottomNav();
        
        // Виправляємо після невеликої затримки (для динамічного контенту)
        setTimeout(forceFixBottomNav, 100);
        setTimeout(forceFixBottomNav, 300);
        
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
            setTimeout(forceFixBottomNav, 300);
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
    
    // КРИТИЧНО: Виправляємо при поверненні до сторінки (bfcache в Safari)
    // Це вирішує проблему відкріплення меню при навігації вперед/назад
    window.addEventListener('pageshow', function(event) {
        // event.persisted === true означає, що сторінка завантажена з кешу
        if (event.persisted) {
            forceFixBottomNav();
            setTimeout(forceFixBottomNav, 100);
        }
        // Запускаємо також при звичайному показі сторінки
        forceFixBottomNav();
    });
    
    // Додатковий обробник для pagehide (перед виходом зі сторінки)
    window.addEventListener('pagehide', function() {
        // Видаляємо тимчасові transform, щоб при поверненні не було проблем
        const bottomNav = document.querySelector('.mobile-bottom-nav');
        if (bottomNav) {
            bottomNav.style.transform = 'none';
        }
    });
})();

