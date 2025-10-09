# 🚀 Інструкція по деплою на Render.com

## 📋 ПЕРЕДУМОВИ

Перед початком переконайтеся, що у вас є:
- ✅ Акаунт на [Render.com](https://render.com)
- ✅ Gmail App Password (вже створено: `ymycifcxvdrtvrvx`)
- ✅ Email: `beautyshop.supp@gmail.com`
- ✅ Проект запушено на GitHub

---

## 🔐 КРОК 1: ПІДГОТОВКА ЗМІННИХ СЕРЕДОВИЩА

### Список всіх змінних, які потрібно додати на Render:

| Змінна | Значення | Опис |
|--------|----------|------|
| `DJANGO_SETTINGS_MODULE` | `beautyshop.settings.production` | Файл налаштувань |
| `DEBUG` | `False` | Вимкнути debug режим |
| `SECRET_KEY` | (генерується автоматично) | Секретний ключ Django |
| `DATABASE_URL` | (генерується автоматично) | PostgreSQL connection string |
| `ALLOWED_HOSTS` | `beautyshop-django.onrender.com,beautyshop-django-*.onrender.com` | Дозволені хости |
| `CSRF_TRUSTED_ORIGINS` | `https://beautyshop-django.onrender.com` | CSRF захист |
| `SITE_URL` | `https://beautyshop-django.onrender.com` | URL сайту |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | Email backend |
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP сервер Gmail |
| `EMAIL_PORT` | `587` | SMTP порт |
| `EMAIL_USE_TLS` | `True` | Використовувати TLS |
| `EMAIL_USE_SSL` | `False` | Не використовувати SSL |
| `EMAIL_HOST_USER` | `beautyshop.supp@gmail.com` | Gmail адреса |
| `EMAIL_HOST_PASSWORD` | `ymycifcxvdrtvrvx` | App Password (БЕЗ пробілів!) |
| `DEFAULT_FROM_EMAIL` | `Beauty Shop <beautyshop.supp@gmail.com>` | Відправник email |
| `ADMIN_EMAIL` | `admin@beautyshop.ua` | Email адміністратора |
| `ADMIN_PASSWORD` | `ВашСильнийПароль123!` | Пароль адміністратора |

---

## 🛠️ КРОК 2: НАЛАШТУВАННЯ НА RENDER

### 2.1. Створення Web Service

1. **Зайдіть на Render Dashboard:**
   - Перейдіть на https://dashboard.render.com

2. **Створіть новий Web Service:**
   - Натисніть "New +" → "Web Service"
   - Підключіть ваш GitHub репозиторій `BeautyShop`
   - Назва: `beautyshop-django`

3. **Основні налаштування:**
   ```
   Name: beautyshop-django
   Region: Frankfurt (EU Central)
   Branch: main
   Root Directory: (залиште порожнім)
   Runtime: Python 3
   Build Command: chmod +x build.sh && ./build.sh
   Start Command: gunicorn beautyshop.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
   Plan: Free
   ```

4. **Advanced Settings → Environment Variables:**
   Додайте всі змінні з таблиці вище (натисніть "Add Environment Variable"):

### 2.2. Створення PostgreSQL Database

1. **На Render Dashboard натисніть "New +" → "PostgreSQL"**

2. **Налаштування:**
   ```
   Name: beautyshop-db
   Database: beautyshop
   User: beautyshop_user
   Region: Frankfurt (EU Central) - ВАЖЛИВО: той же регіон що і Web Service!
   Plan: Free
   ```

3. **Після створення скопіюйте "Internal Database URL"**

4. **Додайте до Web Service:**
   - Перейдіть в Web Service → Environment
   - Додайте змінну `DATABASE_URL` зі значенням "Internal Database URL"

---

## 📧 КРОК 3: ДЕТАЛЬНІ ІНСТРУКЦІЇ ПО ДОДАВАННЮ ЗМІННИХ

### Як додати змінні середовища на Render:

1. **Перейдіть в ваш Web Service**
2. **Клікніть "Environment" в лівому меню**
3. **Клікніть "Add Environment Variable"**
4. **Додайте кожну змінну окремо:**

#### Приклад 1: Email налаштування

```
Key: EMAIL_HOST_USER
Value: beautyshop.supp@gmail.com
```

```
Key: EMAIL_HOST_PASSWORD
Value: ymycifcxvdrtvrvx
```

**⚠️ ВАЖЛИВО:** Пароль вводьте БЕЗ пробілів: `ymycifcxvdrtvrvx`

#### Приклад 2: Django налаштування

```
Key: DJANGO_SETTINGS_MODULE
Value: beautyshop.settings.production
```

```
Key: DEBUG
Value: False
```

#### Приклад 3: Адмін акаунт

```
Key: ADMIN_EMAIL
Value: admin@beautyshop.ua
```

```
Key: ADMIN_PASSWORD
Value: ВашСильнийПароль123!
```

**⚠️ ЗМІНІТЬ пароль адміністратора на свій!**

---

## 🔄 КРОК 4: ДЕПЛОЙ

### 4.1. Автоматичний деплой

Render автоматично задеплоїть ваш сайт після додавання всіх змінних.

**Процес деплою:**
1. ✅ Клонування репозиторію
2. ✅ Встановлення залежностей (`pip install -r requirements.txt`)
3. ✅ Збір статичних файлів (`collectstatic`)
4. ✅ Міграції БД (`migrate`)
5. ✅ Створення категорій (`create_categories`)
6. ✅ Створення суперюзера
7. ✅ Запуск Gunicorn

### 4.2. Перевірка логів

**Під час деплою відкрийте "Logs" і перевіряйте:**

```bash
# Успішна міграція
✅ Operations to perform:
✅ Running migrations

# Створення суперюзера
✅ Superuser created: admin@beautyshop.ua

# Збір статичних файлів
✅ X static files copied

# Запуск сервера
✅ Listening at: http://0.0.0.0:XXXXX
```

### 4.3. Якщо виникли помилки

**Перевірте логи на наявність:**
- ❌ `ModuleNotFoundError` → додайте пакет в `requirements.txt`
- ❌ `ImproperlyConfigured` → перевірте змінні середовища
- ❌ `OperationalError` → перевірте DATABASE_URL
- ❌ `SMTPAuthenticationError` → перевірте EMAIL_HOST_PASSWORD

---

## ✅ КРОК 5: ПЕРЕВІРКА РОБОТИ

### 5.1. Перевірка основного функціоналу

Після успішного деплою перевірте:

1. **Головна сторінка:**
   ```
   https://beautyshop-django.onrender.com/
   ```
   ✅ Має відкритися без помилок

2. **Адмін панель:**
   ```
   https://beautyshop-django.onrender.com/admin/
   ```
   - Логін: `admin@beautyshop.ua`
   - Пароль: той що ви встановили в `ADMIN_PASSWORD`

3. **Реєстрація:**
   ```
   https://beautyshop-django.onrender.com/users/register/
   ```
   - Зареєструйте тестового користувача
   - Перевірте чи приходить email на `beautyshop.supp@gmail.com`

4. **Відновлення паролю:**
   ```
   https://beautyshop-django.onrender.com/users/password/reset/
   ```
   - Введіть email тестового користувача
   - Перевірте чи приходить email

### 5.2. Тестування email функціоналу

**Запустіть в Render Shell:**

1. **Відкрийте Shell:**
   - Web Service → Shell (вгорі справа)

2. **Тест відправки email:**
   ```python
   from django.core.mail import send_mail
   from django.conf import settings
   
   result = send_mail(
       'Тест з Render',
       'Це тестовий лист з production сервера',
       settings.DEFAULT_FROM_EMAIL,
       ['beautyshop.supp@gmail.com'],
       fail_silently=False,
   )
   print(f'Email sent: {result}')
   ```

   **Очікуваний результат:**
   ```
   Email sent: 1
   ```

3. **Перевірте пошту `beautyshop.supp@gmail.com`**

---

## 🔒 КРОК 6: БЕЗПЕКА ДАНИХ

### 6.1. Що захищено автоматично:

✅ **Паролі користувачів:**
- Хешуються PBKDF2-SHA256 (600,000 ітерацій)
- Ніколи не зберігаються у відкритому вигляді
- Неможливо розшифрувати

✅ **База даних PostgreSQL:**
- Автоматичне шифрування на рівні Render
- Щоденні бекапи (зберігаються 7 днів на Free план)
- Ізольована мережа (Internal Database URL)
- SSL з'єднання

✅ **Змінні середовища:**
- Зашифровані на Render
- Доступні тільки вам
- Не показуються в логах
- Не комітяться в Git

✅ **HTTPS:**
- Автоматичний SSL сертифікат від Render
- Примусове перенаправлення HTTP → HTTPS
- HSTS включено (31536000 секунд)

✅ **CSRF захист:**
- Токени на всіх формах
- Trusted Origins налаштовані
- Secure cookies (HttpOnly, Secure)

### 6.2. Додаткові міри безпеки:

1. **Регулярно міняйте паролі:**
   - Пароль адміністратора (через Django Admin)
   - Gmail App Password (кожні 3-6 місяців)

2. **Моніторинг логів:**
   - Перевіряйте Render Logs на підозрілу активність
   - Шукайте невдалі спроби входу

3. **Бекапи бази даних:**
   ```bash
   # На Free плані - автоматичні щоденні бекапи
   # Для ручного бекапу:
   # 1. Зайдіть в Database → Backups
   # 2. Клікніть "Create Backup"
   ```

4. **Обмеження доступу до Admin:**
   - Використовуйте сильні паролі
   - Не діліться даними доступу
   - Регулярно перевіряйте логи входу

---

## 📊 КРОК 7: МОНІТОРИНГ ТА ПІДТРИМКА

### 7.1. Render Dashboard

**Метрики які потрібно моніторити:**

1. **Web Service → Metrics:**
   - CPU Usage
   - Memory Usage
   - Response Time
   - Request Count

2. **Database → Metrics:**
   - Storage Used
   - Connection Count
   - Query Performance

### 7.2. Логування

**Типи логів на Render:**

1. **Build Logs:**
   - Встановлення залежностей
   - Міграції
   - Збір статичних файлів

2. **Deploy Logs:**
   - Запуск сервера
   - Помилки запуску

3. **Runtime Logs:**
   - Запити користувачів
   - Помилки 500
   - Email відправка

**Як переглянути логи:**
```
Web Service → Logs → Select time range
```

### 7.3. Автоматичне оновлення

**Render автоматично деплоїть при push на GitHub:**

1. Ви робите зміни локально
2. `git push origin main`
3. Render автоматично:
   - Клонує новий код
   - Запускає build.sh
   - Перезапускає сервер
   - ✅ Оновлення готове!

**Щоб вимкнути автоматичний деплой:**
```
Web Service → Settings → Auto-Deploy → OFF
```

---

## 🔧 КРОК 8: УСУНЕННЯ ПРОБЛЕМ

### Проблема 1: Email не надсилається

**Перевірте:**
1. ✅ `EMAIL_HOST_USER` = `beautyshop.supp@gmail.com`
2. ✅ `EMAIL_HOST_PASSWORD` = `ymycifcxvdrtvrvx` (БЕЗ пробілів!)
3. ✅ `EMAIL_HOST` = `smtp.gmail.com`
4. ✅ `EMAIL_PORT` = `587`
5. ✅ `EMAIL_USE_TLS` = `True`

**Тест в Shell:**
```python
from django.core.mail import send_mail
send_mail('Test', 'Test', 'beautyshop.supp@gmail.com', ['beautyshop.supp@gmail.com'])
```

### Проблема 2: 500 Error на сайті

**Перевірте логи:**
```
Web Service → Logs
```

**Типові помилки:**
- `ALLOWED_HOSTS` - додайте ваш домен
- `DATABASE_URL` - перевірте з'єднання з БД
- `SECRET_KEY` - має бути встановлено

### Проблема 3: Static files не завантажуються

**Перевірте:**
1. `collectstatic` виконалося успішно в логах
2. `whitenoise` додано в `requirements.txt`
3. Очистіть кеш браузера (Ctrl+Shift+R)

### Проблема 4: Database connection error

**Перевірте:**
1. PostgreSQL database створено
2. `DATABASE_URL` додано в Environment Variables
3. Database та Web Service в одному регіоні

---

## 📱 КРОК 9: НАЛАШТУВАННЯ CUSTOM DOMAIN (Опціонально)

### Якщо ви хочете використовувати свій домен:

1. **Придбайте домен:**
   - Наприклад: `beautyshop.com.ua`

2. **На Render:**
   ```
   Web Service → Settings → Custom Domain
   → Add Custom Domain
   → Введіть: beautyshop.com.ua
   ```

3. **У вашого реєстратора доменів:**
   ```
   Тип: CNAME
   Ім'я: @
   Значення: beautyshop-django.onrender.com
   ```

4. **Оновіть змінні середовища:**
   ```
   ALLOWED_HOSTS = beautyshop.com.ua,www.beautyshop.com.ua
   CSRF_TRUSTED_ORIGINS = https://beautyshop.com.ua,https://www.beautyshop.com.ua
   ```

5. **SSL сертифікат:**
   - Render автоматично створить Let's Encrypt сертифікат
   - Зачекайте 5-10 хвилин

---

## 📞 ПІДТРИМКА

### Контакти:

**Email техпідтримки:**
- `beautyshop.supp@gmail.com`

**Render Support:**
- https://render.com/docs
- https://community.render.com

**Django Documentation:**
- https://docs.djangoproject.com

---

## ✅ ЧЕКЛИСТ ПЕРЕД ЗАПУСКОМ

Переконайтеся що все зроблено:

- [ ] PostgreSQL database створено
- [ ] Web Service створено
- [ ] Всі змінні середовища додані (16 змінних)
- [ ] EMAIL_HOST_PASSWORD без пробілів
- [ ] ADMIN_PASSWORD змінено на сильний
- [ ] Деплой завершився успішно
- [ ] Головна сторінка відкривається
- [ ] Адмін панель працює
- [ ] Реєстрація працює
- [ ] Email надсилається
- [ ] Відновлення паролю працює
- [ ] Оптові ціни показуються тільки авторизованим
- [ ] Static files завантажуються
- [ ] HTTPS працює

---

## 🎉 ВСЕ ГОТОВО!

Після виконання всіх кроків ваш сайт буде повністю функціональним на production!

**URL вашого сайту:**
```
https://beautyshop-django.onrender.com
```

**Адмін панель:**
```
https://beautyshop-django.onrender.com/admin/
```

**Безпека:**
- ✅ Всі дані зашифровані
- ✅ Паролі хешовані
- ✅ HTTPS обов'язковий
- ✅ Автоматичні бекапи
- ✅ Secure cookies
- ✅ CSRF захист

---

**Останнє оновлення:** Жовтень 2025
**Версія:** Production Ready 1.0
**Статус:** ✅ Готово до деплою

