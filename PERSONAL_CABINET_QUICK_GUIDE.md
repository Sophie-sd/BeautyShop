# 🚀 ШВИДКА ШПАРГАЛКА - ОСОБИСТИЙ КАБІНЕТ

## 📌 КЛЮЧОВІ МОМЕНТИ

### 1. НАЙВАЖЛИВІШЕ - ПРИХОВАТИ ОПТОВІ ЦІНИ
**ЗАРАЗ:** Оптові ціни показуються ВСІМ користувачам
**ТРЕБА:** Показувати ТІЛЬКИ авторизованим

**Змінити у всіх шаблонах:**
```django
❌ ЗАРАЗ (неправильно):
{% if product.wholesale_price %}
    <span>{{ product.wholesale_price }} ₴</span>
{% endif %}

✅ ТРЕБА (правильно):
{% if user.is_authenticated and product.wholesale_price %}
    <span>{{ product.wholesale_price }} ₴</span>
{% endif %}
```

**Файли для зміни:**
- templates/core/home.html
- templates/products/sale.html
- templates/core/search.html
- templates/blog/detail.html
- templates/wishlist/list.html

---

### 2. МОДЕЛЬ КОРИСТУВАЧА - ДОДАТИ ПОЛЯ

```python
class CustomUser(AbstractUser):
    # Існуючі поля
    phone = models.CharField(max_length=20, unique=True)  # Додати unique=True
    
    # НОВІ ПОЛЯ:
    date_of_birth = models.DateField('Дата народження', null=True, blank=True)
    email_verified = models.BooleanField('Email підтверджено', default=False)
    email_verification_token = models.CharField(max_length=100, blank=True)
```

---

### 3. ФОРМА РЕЄСТРАЦІЇ - ПОЛЯ

```python
WholesaleRegistrationForm:
✅ first_name (Ім'я)
✅ last_name (Прізвище)
✅ date_of_birth (Дата народження)
✅ phone (Телефон: +380XXXXXXXXX)
✅ email (Email)
✅ password1, password2 (Паролі)
```

**Валідація телефону:**
```python
def clean_phone(self):
    phone = self.cleaned_data.get('phone')
    # Має бути формат +380XXXXXXXXX (9 цифр після +380)
    if not re.match(r'^\+380\d{9}$', phone):
        raise ValidationError("Невірний формат. Використовуйте +380XXXXXXXXX")
    return phone
```

---

### 4. ВІДОБРАЖЕННЯ ЦІН - ЛОГІКА

**Для ВСІХ користувачів (без авторизації):**
- ✅ Роздрібна ціна (retail_price)
- ✅ Акційна ціна (sale_price)
- ✅ Ціна від 3 шт (price_3_qty)
- ✅ Ціна від 5 шт (price_5_qty)

**ТІЛЬКИ для авторизованих:**
- 🔒 Оптова ціна (wholesale_price)

**Для неавторизованих - показати заклик:**
```django
{% if not user.is_authenticated %}
<div class="register-cta">
    <a href="{% url 'users:register' %}">
        Зареєструйтесь для доступу до оптових цін
    </a>
</div>
{% endif %}
```

---

### 5. EMAIL ВЕРИФІКАЦІЯ - ПРОЦЕС

**Крок 1:** Користувач реєструється
**Крок 2:** Створюється користувач з `is_active=False`, `email_verified=False`
**Крок 3:** Генерується токен, надсилається лист
**Крок 4:** Користувач клікає на посилання в листі
**Крок 5:** Токен перевіряється, `is_active=True`, `email_verified=True`
**Крок 6:** Користувач логіниться автоматично

---

### 6. URLS СТРУКТУРА

```python
/users/register/ → реєстрація
/users/verify-email/<token>/ → підтвердження email
/users/login/ → вхід
/users/logout/ → вихід
/users/profile/ → особистий кабінет
/users/profile/edit/ → редагування
/users/orders/ → замовлення
/users/password/change/ → зміна паролю
/users/password/reset/ → відновлення паролю
```

---

### 7. НАВІГАЦІЯ - ЩО ДОДАТИ

**Header (десктоп):**
```
Неавторизований: [Вхід] [Реєстрація ОПТ]
Авторизований: [👤 Іван ▾] → Особистий кабінет, Замовлення, Вихід
```

**Mobile menu:**
```
Неавторизований: Вхід, Реєстрація
Авторизований: Іван, Особистий кабінет, Замовлення, Вихід
```

---

### 8. CSS ФАЙЛИ - СТВОРИТИ

```
static/css/user-auth.css - форми входу/реєстрації
static/css/user-profile.css - особистий кабінет
```

**Важливо:**
- ❌ БЕЗ !important
- ✅ Mobile-first підхід
- ✅ iOS Safari фікси (font-size >= 16px для input)

---

### 9. БЕЗПЕКА - ЧЕКЛІСТ

- ✅ CSRF токени в усіх формах
- ✅ Валідація на серверній стороні
- ✅ Унікальність email та phone
- ✅ Rate limiting (5 спроб входу / 15 хвилин)
- ✅ Токени з обмеженим терміном (24 години)
- ✅ Хешування паролів (Django auto)

---

### 10. ADMIN ПАНЕЛЬ

```python
CustomUserAdmin:
list_display = ['username', 'email', 'phone', 'is_wholesale', 'email_verified']
list_filter = ['is_wholesale', 'email_verified', 'is_active']
search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']
```

**Адмін може:**
- Змінювати `is_wholesale` вручну
- Підтверджувати email вручну
- Переглядати історію замовлень

---

### 11. ТЕСТУВАННЯ - МІНІМУМ

**Функціонал:**
- [ ] Реєстрація працює
- [ ] Email верифікація працює
- [ ] Оптові ціни приховані для неавторизованих
- [ ] Оптові ціни видимі для авторизованих
- [ ] Валідація телефону +380
- [ ] Унікальність email та phone

**Пристрої:**
- [ ] Desktop (Chrome, Firefox, Safari)
- [ ] iPhone (Safari)
- [ ] iPad
- [ ] Android

---

### 12. МІГРАЦІЇ - ПОСЛІДОВНІСТЬ

```bash
# 1. Змінити моделі
# 2. Створити міграції
python3 manage.py makemigrations users

# 3. Переглянути SQL (опціонально)
python3 manage.py sqlmigrate users 0003

# 4. Застосувати міграції
python3 manage.py migrate

# 5. Перевірити
python3 manage.py showmigrations users
```

---

### 13. EMAIL ШАБЛОНИ

**Лист верифікації:**
```
Тема: Підтвердіть ваш email - BeautyShop
Текст: Вітаємо! Для завершення реєстрації перейдіть за посиланням...
```

**Лист відновлення паролю:**
```
Тема: Відновлення паролю - BeautyShop
Текст: Для зміни паролю перейдіть за посиланням...
```

---

### 14. СТАТУС is_wholesale

**За замовчуванням:** `False`
**Як змінити:** Тільки через admin панель (вручну адміністратором)
**Альтернатива:** Автоматично при обороті 5000+ грн/місяць (вже реалізовано)

---

### 15. ПОМИЛКИ - ПОВІДОМЛЕННЯ

```python
"Цей номер телефону вже зареєстрований"
"Ця email адреса вже зареєстрована"
"Невірний формат телефону. Використовуйте формат +380XXXXXXXXX"
"Невірний email або пароль"
"Будь ласка, підтвердіть ваш email для входу"
```

---

## 🎯 З ЧОГО ПОЧАТИ?

### КРОК 1: Backend
1. Оновити `apps/users/models.py` (додати поля)
2. Створити міграції
3. Оновити `apps/users/forms.py` (валідація)
4. Оновити `apps/users/views.py` (email верифікація)

### КРОК 2: Приховати оптові ціни
1. Змінити всі шаблони товарів
2. Додати перевірку `{% if user.is_authenticated %}`

### КРОК 3: Frontend
1. Створити шаблони (register, login, profile)
2. Оновити навігацію (header, mobile menu)
3. Створити CSS файли

### КРОК 4: Тестування
1. Перевірити реєстрацію
2. Перевірити відображення цін
3. Перевірити на мобільних

---

## ⚠️ КРИТИЧНІ ПОМИЛКИ (НЕ РОБИТИ!)

❌ Показувати оптові ціни без перевірки авторизації
❌ Не валідувати дані на серверній стороні
❌ Використовувати !important в CSS
❌ Зберігати паролі в plain text
❌ Робити токени верифікації без терміну дії
❌ Не тестувати на iOS Safari

---

## 📞 ФОРМАТ ТЕЛЕФОНУ

**Правильно:** +380991234567 (обов'язково 9 цифр після +380)
**Неправильно:** 
- 0991234567
- +38099123456 (8 цифр)
- +3809912345678 (10 цифр)

**Regex:** `^\+380\d{9}$`

---

## 🔗 КОРИСНІ ПОСИЛАННЯ

- Django Authentication: https://docs.djangoproject.com/en/4.2/topics/auth/
- Email Verification: https://docs.djangoproject.com/en/4.2/topics/email/
- Password Reset: https://docs.djangoproject.com/en/4.2/topics/auth/default/#django.contrib.auth.views.PasswordResetView

---

**Останнє оновлення:** 2025-10-08
**Статус:** Готово до реалізації ✅

