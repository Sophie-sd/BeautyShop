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
        # #region agent log
        import json; import time
        with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f: f.write(json.dumps({'location':'backends.py:56','message':'AdminOnlyBackend authenticate called','data':{'username':username,'password_length':len(password) if password else 0,'has_request':request is not None},'timestamp':int(time.time()*1000),'hypothesisId':'A,B,C,D,E'})+'\n')
        # #endregion
        
        if username is None or password is None:
            logger.debug(f"AdminOnlyBackend: username або password відсутні")
            return None
        
        logger.info(f"🔐 AdminOnlyBackend: Спроба входу для '{username}'")
        
        user = None
        
        # Спробуємо знайти користувача за username (для адмінів)
        try:
            user = CustomUser.objects.get(username=username)
            logger.info(f"✅ Користувач знайдений за username: {user.username}")
            # #region agent log
            import json; import time
            with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f: f.write(json.dumps({'location':'backends.py:67','message':'User found by username','data':{'username':user.username,'is_staff':user.is_staff,'is_superuser':user.is_superuser,'is_active':user.is_active,'email':user.email,'has_usable_password':user.has_usable_password()},'timestamp':int(time.time()*1000),'hypothesisId':'C,D'})+'\n')
            # #endregion
        except CustomUser.DoesNotExist:
            logger.debug(f"Користувач НЕ знайдений за username: {username}")
            pass
        
        # Якщо не username, спробуємо email
        if not user:
            try:
                user = CustomUser.objects.get(email=username)
                logger.info(f"✅ Користувач знайдений за email: {user.email}")
                # #region agent log
                import json; import time
                with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f: f.write(json.dumps({'location':'backends.py:80','message':'User found by email','data':{'username':user.username,'is_staff':user.is_staff,'is_superuser':user.is_superuser,'is_active':user.is_active,'has_usable_password':user.has_usable_password()},'timestamp':int(time.time()*1000),'hypothesisId':'C,D'})+'\n')
                # #endregion
            except CustomUser.DoesNotExist:
                logger.debug(f"Користувач НЕ знайдений за email: {username}")
                pass
        
        # Якщо не email, спробуємо телефон
        if not user:
            try:
                user = CustomUser.objects.get(phone=username)
                logger.info(f"✅ Користувач знайдений за phone: {user.phone}")
                # #region agent log
                import json; import time
                with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f: f.write(json.dumps({'location':'backends.py:93','message':'User found by phone','data':{'username':user.username,'is_staff':user.is_staff,'is_superuser':user.is_superuser,'is_active':user.is_active,'has_usable_password':user.has_usable_password()},'timestamp':int(time.time()*1000),'hypothesisId':'C,D'})+'\n')
                # #endregion
            except CustomUser.DoesNotExist:
                logger.warning(f"❌ Користувач НЕ знайдений за username/email/phone: {username}")
                # #region agent log
                import json; import time
                with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f: f.write(json.dumps({'location':'backends.py:99','message':'User not found at all','data':{'search_term':username},'timestamp':int(time.time()*1000),'hypothesisId':'E'})+'\n')
                # #endregion
                return None
        
        # ВАЖЛИВО: Перевіряємо що це адміністратор
        if not (user.is_staff or user.is_superuser):
            logger.warning(f"❌ Користувач {user.username} НЕ є адміністратором (is_staff={user.is_staff}, is_superuser={user.is_superuser})")
            # #region agent log
            import json; import time
            with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f: f.write(json.dumps({'location':'backends.py:107','message':'User is not admin','data':{'username':user.username,'is_staff':user.is_staff,'is_superuser':user.is_superuser},'timestamp':int(time.time()*1000),'hypothesisId':'D'})+'\n')
            # #endregion
            # Звичайні користувачі НЕ можуть заходити через адмінку
            return None
        
        logger.info(f"✅ Користувач {user.username} є адміністратором")
        
        # Перевіряємо пароль
        password_valid = user.check_password(password)
        can_authenticate = self.user_can_authenticate(user)
        # #region agent log
        import json; import time
        with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f: f.write(json.dumps({'location':'backends.py:119','message':'Password check result','data':{'username':user.username,'password_valid':password_valid,'can_authenticate':can_authenticate,'is_active':user.is_active,'password_hash_prefix':user.password[:20]},'timestamp':int(time.time()*1000),'hypothesisId':'A,B,C'})+'\n')
        # #endregion
        
        if password_valid and can_authenticate:
            logger.info(f"✅ Пароль валідний для {user.username}")
            return user
        else:
            logger.warning(f"❌ Пароль НЕ валідний для {user.username}")
            # #region agent log
            import json; import time
            with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f: f.write(json.dumps({'location':'backends.py:129','message':'Authentication failed','data':{'username':user.username,'password_valid':password_valid,'can_authenticate':can_authenticate},'timestamp':int(time.time()*1000),'hypothesisId':'A,B,C'})+'\n')
            # #endregion
        
        return None

