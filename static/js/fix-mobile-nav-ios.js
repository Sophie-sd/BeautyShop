(function() {
    'use strict';
    
    const bottomNav = document.querySelector('.mobile-bottom-nav');
    if (!bottomNav) return;
    
    function fix() {
        bottomNav.style.cssText = 'position:fixed;bottom:0;left:0;right:0;width:100%;z-index:1000';
        document.documentElement.style.transform = 'none';
        document.body.style.transform = 'none';
    }
    
    fix();
    setTimeout(fix, 50);
    setTimeout(fix, 200);
    
    window.addEventListener('load', fix);
    window.addEventListener('pageshow', fix);
    window.addEventListener('resize', fix, { passive: true });
    
    let scrolled = false;
    window.addEventListener('scroll', function() {
        if (!scrolled) {
            fix();
            scrolled = true;
        }
    }, { passive: true, once: true });
})();

