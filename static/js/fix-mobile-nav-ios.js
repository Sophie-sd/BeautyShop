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
        
        bottomNav.style.position = 'fixed';
        bottomNav.style.bottom = '0';
        bottomNav.style.left = '0';
        bottomNav.style.right = '0';
        bottomNav.style.width = '100%';
        bottomNav.style.zIndex = '1000';
        
        document.documentElement.style.transform = 'none';
        document.documentElement.style.perspective = 'none';
        document.body.style.transform = 'none';
        document.body.style.perspective = 'none';
        
        bottomNav.style.transform = 'translateZ(0)';
        requestAnimationFrame(function() {
            bottomNav.style.transform = 'none';
        });
    }
    
    function checkAndFix() {
        forceFixBottomNav();
        setTimeout(forceFixBottomNav, 100);
        setTimeout(forceFixBottomNav, 300);
        
        let scrollFixed = false;
        const onScroll = function() {
            if (!scrollFixed) {
                forceFixBottomNav();
                scrollFixed = true;
                window.removeEventListener('scroll', onScroll);
            }
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        
        window.addEventListener('orientationchange', function() {
            setTimeout(forceFixBottomNav, 100);
            setTimeout(forceFixBottomNav, 300);
        });
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkAndFix);
    } else {
        checkAndFix();
    }
    
    window.addEventListener('load', checkAndFix);
    
    window.addEventListener('pageshow', function(event) {
        if (event.persisted) {
            forceFixBottomNav();
            setTimeout(forceFixBottomNav, 100);
        }
        forceFixBottomNav();
    });
    
    window.addEventListener('pagehide', function() {
        const bottomNav = document.querySelector('.mobile-bottom-nav');
        if (bottomNav) {
            bottomNav.style.transform = 'none';
        }
    });
    
    const observer = new MutationObserver(forceFixBottomNav);
    observer.observe(document.body, { 
        attributes: true, 
        attributeFilter: ['class'] 
    });
})();

