# 🔒 Керівництво з безпеки Beauty Shop

## 📋 Зміст

1. [Система аутентифікації](#система-аутентифікації)
2. [Розділення доступів](#розділення-доступів)
3. [Налаштування сесій](#налаштування-сесій)
4. [CSRF та XSS захист](#csrf-та-xss-захист)
5. [Безпечні практики](#безпечні-практики)
6. [FAQ з безпеки](#faq-з-безпеки)

---

## 🔐 Система аутентифікації

### Два окремих backend для аутентифікації:

#### 1. `WholesaleClientBackend` — Для оптових клієнтів
**Файл:** `apps/users/backends.py`

**Призначення:**
- Використовується для входу в **особистий кабінет** (`/users/login/`)
- Доступний ТІЛЬКИ для звичайних оптових клієнтів

**Правила входу:**
- ✅ Дозволяє вхід через **email** або **телефон**
- ❌ **НЕ дозволяє** вхід через username
- ❌ **ЗАБОРОНЯЄ** вхід адміністраторам (`is_staff=True` або `is_superuser=True`)

**Приклад використання:**
```python
# Користувач може ввійти через:
# - Email: client@example.com
# - Телефон: +380991234567
# Але НЕ через username!
```

---

#### 2. `AdminOnlyBackend` — Для адміністраторів
**Файл:** `apps/users/backends.py`

**Призначення:**
- Використовується для входу в **адмін-панель** (`/admin/`)
- Доступний ТІЛЬКИ для адміністраторів

**Правила входу:**
- ✅ Дозволяє вхід через **username**, **email** або **телефон**
- ✅ **ТІЛЬКИ** для користувачів з `is_staff=True` або `is_superuser=True`
- ❌ **ЗАБОРОНЯЄ** вхід звичайним клієнтам

**Приклад використання:**
```python
# Адміністратор може ввійти через:
# - Username: admin
# - Email: admin@beautyshop.ua
# - Телефон: +380123456789
```

---

### Порядок backends у налаштуваннях:

**Файл:** `beautyshop/settings/base.py`

```python
AUTHENTICATION_BACKENDS = [
    'apps.users.backends.WholesaleClientBackend',  # Перший — для клієнтів
    'apps.users.backends.AdminOnlyBackend',        # Другий — для адмінів
    'django.contrib.auth.backends.ModelBackend',   # Fallback
]
```

**Важливо:** Порядок має значення! Django перевіряє backends по черзі.

---

## 🚧 Розділення доступів

### Хто куди може заходити:

| Тип користувача | Особистий кабінет (`/users/`) | Адмін-панель (`/admin/`) |
|----------------|------------------------------|--------------------------|
| **Оптовий клієнт** (звичайний користувач) | ✅ Так | ❌ Ні |
| **Адміністратор** (`is_staff=True`) | ❌ Ні | ✅ Так |
| **Суперадміністратор** (`is_superuser=True`) | ❌ Ні | ✅ Так |
| **Неавторизований** | ❌ Ні (редірект на login) | ❌ Ні (редірект на admin/login) |

---

### Захист особистого кабінету від адміністраторів:

**Файл:** `apps/users/views.py`

Всі views особистого кабінету мають перевірку в методі `dispatch()`:

```python
def dispatch(self, request, *args, **kwargs):
    # БЕЗПЕКА: Адміністратори НЕ можуть заходити в особистий кабінет
    if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
        messages.error(
            request,
            '🔒 Доступ заборонено. Адміністратори не мають доступу до особистого кабінету оптових клієнтів.'
        )
        return redirect('/admin/')
    return super().dispatch(request, *args, **kwargs)
```

**Захищені views:**
- ✅ `ProfileView` — особистий кабінет
- ✅ `UserOrdersView` — замовлення користувача
- ✅ `ProfileEditView` — редагування профілю

---

### Чому це важливо?

1. **Запобігання конфліктам:**
   - Адміністратори не бачать оптові ціни
   - Не створюється плутанина з замовленнями
   
2. **Безпека даних:**
   - Адміністратори працюють тільки через адмінку
   - Немає змішування прав доступу
   
3. **Чіткість ролей:**
   - Адмін = управління сайтом
   - Клієнт = покупки з оптовими цінами

---

## ⏰ Налаштування сесій

### Налаштування сесій користувачів:

**Файл:** `beautyshop/settings/base.py`

```python
# Налаштування сесій для ОПТОВИХ КЛІЄНТІВ
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 днів
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only в production
SESSION_COOKIE_HTTPONLY = True  # Захист від XSS атак
SESSION_COOKIE_SAMESITE = 'Lax'  # Захист від CSRF атак
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
```

### Налаштування сесій адміністраторів:

```python
# Окремі налаштування для АДМІНКИ (коротша сесія для безпеки)
ADMIN_SESSION_COOKIE_AGE = 60 * 60 * 8  # 8 годин
```

---

### Чому різні терміни сесій?

| Параметр | Оптові клієнти | Адміністратори | Пояснення |
|----------|---------------|----------------|-----------|
| **Термін дії** | 7 днів | 8 годин | Клієнти входять рідше, адміни — регулярно |
| **Безпека** | Середня | Висока | Адмінка — критичний доступ |
| **Зручність** | Висока | Середня | Клієнти не хочуть часто вводити пароль |

---

### Коли запитується пароль:

✅ **Запитується пароль при:**
- Першому вході на сайт
- Після очищення cookies/cache
- Після виходу з акаунту (logout)
- Після закінчення терміну сесії (7 днів для клієнтів, 8 годин для адмінів)

❌ **НЕ запитується пароль:**
- Під час активної сесії
- При переході між сторінками сайту
- При закритті/відкритті браузера (якщо сесія активна)

---

## 🛡️ CSRF та XSS захист

### CSRF (Cross-Site Request Forgery) захист:

**Файл:** `beautyshop/settings/base.py`

```python
# CSRF settings
CSRF_COOKIE_HTTPONLY = False  # Дозволяє JavaScript читати CSRF токен
CSRF_USE_SESSIONS = False     # Зберігає CSRF токен у cookies
CSRF_COOKIE_SAMESITE = 'Lax'  # Захист від CSRF атак
```

**В development.py:**
```python
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.onrender.com',
    'https://beautyshop-django.onrender.com',
]
```

---

### XSS (Cross-Site Scripting) захист:

```python
# Security settings
SECURE_BROWSER_XSS_FILTER = True       # Вбудований XSS фільтр браузера
SECURE_CONTENT_TYPE_NOSNIFF = True     # Запобігає MIME-type sniffing
X_FRAME_OPTIONS = 'DENY'               # Запобігає clickjacking
SESSION_COOKIE_HTTPONLY = True         # JavaScript не може читати session cookie
```

---

### HTTPS налаштування (Production):

```python
SECURE_HSTS_SECONDS = 31536000         # 1 рік
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True           # Cookies тільки через HTTPS
```

---

## 🔑 Безпечні практики

### 1. Паролі

**Вимоги до паролів:**
- ✅ Мінімум 8 символів
- ✅ Мінімум 1 велика літера
- ✅ Мінімум 1 цифра
- ✅ Хешування через Django `PBKDF2PasswordHasher`

**Налаштування Django:**
```python
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
]
```

---

### 2. Email верифікація

**Всі нові користувачі ОБОВ'ЯЗКОВО проходять верифікацію email:**

1. Реєстрація → користувач створюється з `is_active=False`
2. Відправляється email з унікальним токеном
3. Користувач клікає на посилання
4. Email підтверджується → `is_active=True`
5. Користувач може увійти

**Файли:**
- `apps/users/models.py` — модель з полем `email_verification_token`
- `apps/users/utils.py` — функція `send_verification_email()`
- `apps/users/views.py` — `EmailVerificationView`

---

### 3. Захист від brute-force атак

**Рекомендації:**

1. **Django Axes** (опційно, можна встановити):
   ```bash
   pip install django-axes
   ```
   - Блокує IP після N невдалих спроб входу
   - Логує підозрілу активність

2. **Rate limiting** на рівні nginx/gunicorn:
   ```nginx
   limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
   ```

3. **Captcha** для форми входу (опційно):
   - Google reCAPTCHA
   - Django Simple Captcha

---

### 4. Логування безпекових подій

**Файл:** `apps/users/views.py`

Всі важливі події логуються:

```python
import logging
logger = logging.getLogger(__name__)

# Приклади логування:
logger.info(f"📝 New user registered: {user.email}")
logger.info(f"✅ User logged in: {user.email}")
logger.warning(f"⚠️ Failed login attempt for: {username}")
logger.error(f"❌ Security violation: Admin tried to access client area")
```

**Налаштування логування:**
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
        },
    },
    'loggers': {
        'apps.users': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

---

### 5. Безпека у production

**Чеклист для production:**

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` у змінній оточення (не в коді!)
- [ ] HTTPS увімкнено (через Nginx/Cloudflare)
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] Регулярне оновлення залежностей
- [ ] Backup бази даних щодня
- [ ] Моніторинг логів

---

## ❓ FAQ з безпеки

### 1. Чому адміністратор не може ввійти в особистий кабінет?

**Відповідь:** Це захист від конфліктів та плутанини.

**Причини:**
- Адміністратори мають спеціальні права в адмінці
- Особистий кабінет показує оптові ціни
- Змішування ролей може призвести до помилок
- Адміністратори повинні працювати виключно через адмін-панель

**Рішення:** Якщо адміністратору потрібно перевірити роботу особистого кабінету:
1. Створіть окремий тестовий акаунт БЕЗ прав адміністратора
2. Зареєструйтеся як звичайний оптовий клієнт
3. Перевірте функціонал

---

### 2. Чому при вході в адмінку не завжди запитує пароль?

**Відповідь:** Це нормально! Діє сесія.

**Пояснення:**
- Сесія адміністратора зберігається **8 годин**
- Після входу не потрібно вводити пароль повторно протягом цього часу
- Це зручно для адміністраторів, які працюють весь день

**Коли запитає пароль знову:**
- Через 8 годин після входу
- Після виходу з акаунту (кнопка "Вийти")
- Після очищення cookies браузера
- З іншого пристрою/браузера

---

### 3. Як змінити термін дії сесії?

**Для клієнтів:**
```python
# beautyshop/settings/base.py
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 днів (було 7)
```

**Для адміністраторів:**
```python
# beautyshop/settings/base.py
ADMIN_SESSION_COOKIE_AGE = 60 * 60 * 4  # 4 години (було 8)
```

---

### 4. Що робити якщо підозра на злом?

**Негайні дії:**

1. **Змінити паролі:**
   ```bash
   python manage.py changepassword admin
   ```

2. **Скинути всі сесії:**
   ```bash
   python manage.py clearsessions
   ```

3. **Перевірити логи:**
   ```bash
   tail -f logs/security.log
   grep "FAILED" logs/security.log
   ```

4. **Перевірити користувачів:**
   ```bash
   python manage.py shell
   >>> from apps.users.models import CustomUser
   >>> admins = CustomUser.objects.filter(is_staff=True)
   >>> for admin in admins:
   ...     print(f"{admin.username} | {admin.email} | last_login: {admin.last_login}")
   ```

5. **Оновити SECRET_KEY:**
   - Згенерувати новий ключ
   - Оновити у змінних оточення
   - Перезапустити сервер

---

### 5. Як додати двофакторну аутентифікацію (2FA)?

**Рекомендовані пакети:**

1. **django-otp** (для адмінки):
   ```bash
   pip install django-otp
   pip install qrcode
   ```

2. **django-allauth** (для клієнтів):
   ```bash
   pip install django-allauth
   ```

**Інтеграція (приклад):**
```python
# settings.py
INSTALLED_APPS += [
    'django_otp',
    'django_otp.plugins.otp_totp',
]

MIDDLEWARE += [
    'django_otp.middleware.OTPMiddleware',
]
```

---

### 6. Як захистити від DDoS атак?

**На рівні сервера:**

1. **Nginx rate limiting:**
   ```nginx
   limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
   limit_req zone=general burst=20 nodelay;
   ```

2. **Cloudflare:**
   - Безкоштовний CDN з DDoS захистом
   - Автоматична фільтрація трафіку
   - Rate limiting на рівні DNS

3. **Fail2ban:**
   ```bash
   sudo apt install fail2ban
   # Налаштувати правила для Django
   ```

---

## 📞 Контакти з безпеки

При виявленні вразливостей:
- 📧 Email: security@beautyshop.ua
- 🔒 Використовуйте GPG для шифрування повідомлень
- ⚠️ **НЕ публікуйте** вразливості публічно до їх виправлення

---

## 📚 Додаткові ресурси

### Документація:
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

### Інструменти для аудиту:
- `python manage.py check --deploy` — перевірка безпеки Django
- `bandit` — статичний аналіз коду Python
- `safety check` — перевірка вразливостей у залежностях

---

**Документ оновлено:** Жовтень 2024  
**Версія:** 1.0  
**Автор:** Beauty Shop Development Team

