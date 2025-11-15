"""
Security middleware для додаткових заголовків безпеки
"""


class SecurityHeadersMiddleware:
    """
    Додає security headers до всіх відповідей
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com data:",
            "img-src 'self' data: https: http:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self' https://www.liqpay.ua",
        ]
        response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class PrivatePagesCacheMiddleware:
    """
    Забороняє кешування для приватних сторінок (профіль, замовлення, кошик)
    """
    
    PRIVATE_PATHS = [
        '/users/profile/',
        '/users/orders/',
        '/users/wishlist/',
        '/cart/',
        '/orders/',
        '/admin/',
        '/category/',
        '/products/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Перевіряємо чи це приватний маршрут
        for path in self.PRIVATE_PATHS:
            if request.path.startswith(path):
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                break
        
        return response

