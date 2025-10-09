# 🔒 База даних та безпека особистого кабінету

## 📊 СТРУКТУРА БАЗИ ДАНИХ

### 1. Таблиця користувачів (`users_customuser`)

**Поля:**
- `id` - унікальний ідентифікатор
- `username` - ім'я користувача (унікальне, генерується з email)
- `email` - email адреса (унікальна, обов'язкове поле)
- `phone` - телефон у форматі +380XXXXXXXXX (унікальне, обов'язкове поле)
- `password` - хешований пароль (використовується PBKDF2 алгоритм)
- `first_name` - ім'я користувача
- `last_name` - прізвище користувача
- `date_of_birth` - дата народження
- `is_active` - статус активності (False до підтвердження email)
- `email_verified` - статус підтвердження email
- `email_verification_token` - токен для підтвердження email
- `is_wholesale` - статус оптового клієнта
- `monthly_turnover` - місячний оборот
- `last_turnover_update` - дата останнього оновлення обороту
- `created_at` - дата реєстрації
- `date_joined` - дата приєднання
- `last_login` - дата останнього входу

**Індекси:**
- PRIMARY KEY (`id`)
- UNIQUE INDEX (`username`)
- UNIQUE INDEX (`email`)
- UNIQUE INDEX (`phone`)
- INDEX (`is_wholesale`)
- INDEX (`email_verified`)

### 2. Таблиця профілів (`users_userprofile`)

**Поля:**
- `id` - унікальний ідентифікатор
- `user_id` - зовнішній ключ до CustomUser (ONE-TO-ONE)
- `company_name` - назва компанії (опціонально)
- `tax_number` - податковий номер (опціонально)
- `address` - адреса (опціонально)
- `notes` - примітки (опціонально)

**Зв'язки:**
- ONE-TO-ONE з `users_customuser` через `user_id`

---

## 🔐 БЕЗПЕКА

### 1. Хешування паролів

**Django використовує PBKDF2 алгоритм:**
- PBKDF2-SHA256 з 600,000 ітераціями
- Солтінг (випадкова сіль для кожного паролю)
- Пароль НІКОЛИ не зберігається у відкритому вигляді

**Приклад хешу:**
```
pbkdf2_sha256$600000$random_salt$hash_value
```

### 2. Захист від SQL-ін'єкцій

**Django ORM автоматично екранує запити:**
- Використовуються параметризовані запити
- Всі дані проходять через ORM валідацію
- Прямі SQL запити екрануються через `cursor.execute()`

### 3. Захист від CSRF атак

**CSRF токени:**
- Кожна форма містить CSRF токен
- Токени перевіряються на сервері
- Конфігурація: `CSRF_COOKIE_SECURE`, `CSRF_COOKIE_HTTPONLY`

### 4. Email верифікація

**Двоетапна верифікація:**
1. Користувач реєструється → `is_active=False`
2. Надсилається email з токеном верифікації
3. Користувач переходить за посиланням → `is_active=True`, `email_verified=True`
4. Токен видаляється після використання

**Токени:**
- Генеруються через `secrets.token_urlsafe(32)` (256 біт ентропії)
- Зберігаються в базі даних
- Одноразові (видаляються після використання)

### 5. Автентифікація

**Custom Authentication Backend:**
- Вхід через email АБО username
- Перевірка паролю через `user.check_password()`
- Автоматична перевірка `is_active` статусу
- Захист від brute-force через rate limiting (можна додати)

**Конфігурація:**
```python
AUTHENTICATION_BACKENDS = [
    'apps.users.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

### 6. Відновлення паролю

**Django's PasswordResetView:**
- Генерація токена через `default_token_generator`
- Токени мають обмежений час життя (24 години)
- UID користувача кодується в base64
- Email надсилається через безпечний SMTP (TLS)

**Формат посилання:**
```
/users/password/reset/<uidb64>/<token>/
```

### 7. Session Management

**Django Sessions:**
- Сесії зберігаються в базі даних
- Session ID передається через cookies
- Cookies помічені як `HttpOnly` та `Secure` (в production)
- Автоматичне видалення старих сесій

**Конфігурація:**
```python
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 днів
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True  # Тільки для HTTPS
```

---

## 💾 РЕЗЕРВНЕ КОПІЮВАННЯ

### 1. Development (SQLite)

**Автоматичне збереження:**
- База даних зберігається в файлі `db.sqlite3`
- Файл не комітиться в Git (захищений .gitignore)
- Рекомендується робити бекапи вручну

**Команди для бекапу:**
```bash
# Створення бекапу
cp db.sqlite3 backups/db_$(date +%Y%m%d_%H%M%S).sqlite3

# Відновлення з бекапу
cp backups/db_20241009_120000.sqlite3 db.sqlite3
```

### 2. Production (PostgreSQL на Render.com)

**Автоматичні бекапи Render:**
- Щоденні автоматичні бекапи
- Зберігаються протягом 7 днів (безкоштовний план)
- Можна відновити через панель Render

**Ручні бекапи:**
```bash
# Експорт бази даних
pg_dump -h hostname -U username -d dbname > backup.sql

# Імпорт бази даних
psql -h hostname -U username -d dbname < backup.sql
```

---

## 🛡️ ДОДАТКОВІ МІРИ БЕЗПЕКИ

### 1. Валідація даних

**Server-side валідація:**
- Email формат: `EmailField`
- Телефон формат: `RegexValidator(r'^\+380\d{9}$')`
- Пароль складність: Django's `PasswordValidator`
- Унікальність: перевірка в `clean_email()` та `clean_phone()`

**Client-side валідація:**
- HTML5 pattern атрибути
- JavaScript валідація (додаткова)
- Не замінює server-side валідацію!

### 2. Захист особистих даних

**GDPR відповідність:**
- Користувачі можуть видалити свій акаунт
- Всі персональні дані видаляються з БД
- Паролі ніколи не зберігаються у відкритому вигляді
- Email використовується тільки для автентифікації

**Доступ до даних:**
- Адміністратор бачить всі дані через Django Admin
- Користувачі бачать тільки свої дані
- Оптові ціни показуються тільки після автентифікації

### 3. Логування

**Django Logging:**
```python
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/security.log',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
        },
    },
}
```

**Що логується:**
- Невдалі спроби входу
- Зміни паролів
- Реєстрації нових користувачів
- Помилки відправки email

---

## 📈 МОНІТОРИНГ ТА ОПТИМІЗАЦІЯ

### 1. Індекси БД

**Рекомендовані індекси:**
- `email` - для швидкого пошуку при вході
- `phone` - для перевірки унікальності
- `is_wholesale` - для фільтрації оптових клієнтів
- `created_at` - для сортування по даті реєстрації

### 2. Оптимізація запитів

**select_related() та prefetch_related():**
```python
# Замість:
user = CustomUser.objects.get(email=email)
profile = user.profile  # Додатковий запит

# Краще:
user = CustomUser.objects.select_related('profile').get(email=email)
```

### 3. Кешування

**Django Cache Framework:**
```python
from django.core.cache import cache

# Кешування даних користувача
user_data = cache.get(f'user_{user_id}')
if not user_data:
    user_data = get_user_data(user_id)
    cache.set(f'user_{user_id}', user_data, 3600)  # 1 година
```

---

## ✅ ЧЕКЛИСТ БЕЗПЕКИ

- [x] Паролі хешуються (PBKDF2-SHA256)
- [x] CSRF захист увімкнено
- [x] SQL-ін'єкції неможливі (Django ORM)
- [x] Email верифікація обов'язкова
- [x] Токени генеруються безпечно
- [x] Session cookies захищені
- [x] Валідація на сервері та клієнті
- [x] Унікальність email та phone
- [x] Автоматичні бекапи (production)
- [x] Логування безпеки
- [ ] Rate limiting (рекомендується додати)
- [ ] Two-Factor Authentication (опціонально)
- [ ] IP whitelist для адмін-панелі (опціонально)

---

## 🚨 У РАЗІ КОМПРОМЕТАЦІЇ

### Якщо підозра на витік даних:

1. **Негайно змініть SECRET_KEY** в налаштуваннях
2. **Змусьте всіх користувачів змінити паролі**
3. **Перевірте логи на підозрілу активність**
4. **Зробіть бекап поточної БД**
5. **Оновіть всі залежності** (`pip install -U`)
6. **Перевірте код на вразливості** (Django security checklist)

### Контакти підтримки:

- Email: beautyshop.supp@gmail.com
- Phone: +38 (068) 175-26-54

---

**Останнє оновлення:** Жовтень 2025
**Версія Django:** 4.2.x
**База даних:** SQLite (dev) / PostgreSQL (production)

