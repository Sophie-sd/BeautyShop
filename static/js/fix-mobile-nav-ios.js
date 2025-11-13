(function() {
    'use strict';
    
    if(!/iPad|iPhone|iPod/.test(navigator.userAgent)) return;
    
    function fix() {
        document.documentElement.style.transform = 'none';
        document.body.style.transform = 'none';
    }
    
    fix();
    window.addEventListener('pageshow', fix);
})();

