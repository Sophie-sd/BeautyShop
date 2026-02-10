"""
Middleware для діагностики проблем з входом в Django Admin
"""
import logging

logger = logging.getLogger('apps.users')


class AdminLoginDebugMiddleware:
    """
    Middleware для логування спроб входу в адмінку (без чутливих даних).
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Логуємо POST запити до /admin/login/ (мінімально)
        if request.path == '/admin/login/' and request.method == 'POST':
            logger.info(f"Спроба входу в адмінку з IP: {self.get_client_ip(request)}")
        
        response = self.get_response(request)
        
        # Логуємо результат спроби входу
        if request.path == '/admin/login/' and request.method == 'POST':
            if hasattr(request, 'user') and request.user.is_authenticated:
                logger.info(f"Успішний вхід адміністратора")
            else:
                logger.warning(f"Невдала спроба входу в адмінку")
        
        return response
    
    def get_client_ip(self, request):
        """Отримує IP адресу клієнта (враховуючи проксі Render)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

