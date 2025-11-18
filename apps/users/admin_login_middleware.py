"""
Middleware для діагностики проблем з входом в Django Admin
"""
import logging

logger = logging.getLogger('apps.users')


class AdminLoginDebugMiddleware:
    """
    Middleware для діагностики проблем з входом в адмінку.
    Логує всі спроби входу та відповідні помилки.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Логуємо всі POST запити до /admin/login/
        if request.path == '/admin/login/' and request.method == 'POST':
            logger.info("="*70)
            logger.info("🔐 СПРОБА ВХОДУ В АДМІНКУ")
            logger.info("="*70)
            logger.info(f"📍 IP Address: {self.get_client_ip(request)}")
            logger.info(f"🌐 User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
            logger.info(f"🍪 Session Key: {request.session.session_key if hasattr(request, 'session') else 'NO SESSION'}")
            logger.info(f"🔑 CSRF Cookie: {'Present' if request.COOKIES.get('beautyshop_csrftoken') else 'MISSING'}")
            logger.info(f"📝 Username field: {request.POST.get('username', 'NOT PROVIDED')}")
            logger.info(f"🔒 Password provided: {'YES' if request.POST.get('password') else 'NO'}")
            logger.info(f"🎯 Referrer: {request.META.get('HTTP_REFERER', 'None')}")
            logger.info(f"🌍 Origin: {request.META.get('HTTP_ORIGIN', 'None')}")
            logger.info(f"🔐 Secure: {request.is_secure()}")
            logger.info("="*70)
        
        response = self.get_response(request)
        
        # Логуємо результат спроби входу
        if request.path == '/admin/login/' and request.method == 'POST':
            logger.info("="*70)
            logger.info("📤 РЕЗУЛЬТАТ СПРОБИ ВХОДУ")
            logger.info("="*70)
            logger.info(f"📊 Status Code: {response.status_code}")
            logger.info(f"📍 Redirect Location: {response.get('Location', 'None')}")
            logger.info(f"👤 User authenticated: {request.user.is_authenticated if hasattr(request, 'user') else 'Unknown'}")
            if hasattr(request, 'user') and request.user.is_authenticated:
                logger.info(f"✅ Logged in as: {request.user.username} (is_staff={request.user.is_staff})")
            else:
                logger.warning(f"❌ Вхід НЕ ВДАВСЯ")
            logger.info("="*70 + "\n")
        
        return response
    
    def get_client_ip(self, request):
        """Отримує IP адресу клієнта (враховуючи проксі Render)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

