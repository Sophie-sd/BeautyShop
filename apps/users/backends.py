"""
Custom authentication backends для входу
"""
from django.contrib.auth.backends import ModelBackend
from .models import CustomUser


class WholesaleClientBackend(ModelBackend):
    """
    Backend для ОСОБИСТОГО КАБІНЕТУ оптових клієнтів
    - Дозволяє вхід ТІЛЬКИ через email (НЕ username, НЕ телефон)
    - ЗАБОРОНЯЄ вхід адміністраторам (is_staff=True або is_superuser=True)
    - Призначений виключно для звичайних оптових клієнтів
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        user = None
        
        # Шукаємо користувача ТІЛЬКИ за email
        try:
            user = CustomUser.objects.get(email=username)
        except CustomUser.DoesNotExist:
            return None
        
        # ВАЖЛИВО: Перевіряємо що це НЕ адміністратор
        if user and (user.is_staff or user.is_superuser):
            # Адміністратори НЕ можуть заходити в особистий кабінет
            return None
        
        # Перевіряємо пароль
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None


class AdminOnlyBackend(ModelBackend):
    """
    Backend для АДМІНКИ
    - Дозволяє вхід через username, email або телефон
    - Працює ТІЛЬКИ для адміністраторів (is_staff=True)
    - Використовується лише для /admin/
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        user = None
        
        # Спробуємо знайти користувача за username (для адмінів)
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            pass
        
        # Якщо не username, спробуємо email
        if not user:
            try:
                user = CustomUser.objects.get(email=username)
            except CustomUser.DoesNotExist:
                pass
        
        # Якщо не email, спробуємо телефон
        if not user:
            try:
                user = CustomUser.objects.get(phone=username)
            except CustomUser.DoesNotExist:
                return None
        
        # ВАЖЛИВО: Перевіряємо що це адміністратор
        if not (user.is_staff or user.is_superuser):
            # Звичайні користувачі НЕ можуть заходити через адмінку
            return None
        
        # Перевіряємо пароль
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None

