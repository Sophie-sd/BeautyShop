"""
Middleware для перевірки валідності користувача в сесії.
"""
from django.contrib.auth import logout
from django.contrib.auth.models import AnonymousUser
from apps.users.models import CustomUser
import logging

logger = logging.getLogger(__name__)


class ValidateUserMiddleware:
    """
    Middleware для перевірки, чи існує користувач в базі даних.
    Якщо користувач видалений, але сесія все ще активна - виконується logout.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Перевіряємо, чи користувач залогінений
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Перевіряємо, чи користувач існує в БД
                if request.user.pk:
                    user = CustomUser.objects.get(pk=request.user.pk)
                    # Перевіряємо чи активний
                    if not user.is_active:
                        logger.warning(f"User {user.email} is inactive, logging out")
                        logout(request)
                        request.user = AnonymousUser()
            except CustomUser.DoesNotExist:
                # Користувача не існує в БД - виходимо з системи
                logger.warning(f"User with pk={request.user.pk} does not exist, logging out")
                logout(request)
                request.user = AnonymousUser()
            except Exception as e:
                # Інші помилки НЕ призводять до logout
                logger.error(f"Error in ValidateUserMiddleware: {e}")
        
        response = self.get_response(request)
        return response

