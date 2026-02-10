"""
Custom authentication backends для входу
"""
from django.contrib.auth.backends import ModelBackend
from .models import CustomUser
import logging

logger = logging.getLogger('apps.users')


class WholesaleClientBackend(ModelBackend):
    """
    Backend для ОСОБИСТОГО КАБІНЕТУ оптових клієнтів
    - Дозволяє вхід ТІЛЬКИ через email (НЕ username, НЕ телефон)
    - ЗАБОРОНЯЄ вхід адміністраторам (is_staff=True або is_superuser=True)
    - Призначений виключно для звичайних оптових клієнтів
    - НЕ обробляє запити від Django Admin (пропускає для AdminOnlyBackend)
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        # Пропускаємо запити від Django Admin - дозволяємо AdminOnlyBackend обробити їх
        if request and request.path.startswith('/admin/'):
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
                # Логуємо тільки невдалі спроби входу (для безпеки)
                logger.warning(f"Невдала спроба входу в адмінку з невідомим обліковим записом")
                return None
        
        # ВАЖЛИВО: Перевіряємо що це адміністратор
        if not (user.is_staff or user.is_superuser):
            logger.warning(f"Спроба входу в адмінку неадміністраторським обліковим записом")
            return None
        
        # Перевіряємо пароль
        if user.check_password(password) and self.user_can_authenticate(user):
            logger.info(f"Успішний вхід адміністратора в систему")
            return user
        else:
            logger.warning(f"Невдала спроба входу адміністратора (невірний пароль)")
        
        return None

