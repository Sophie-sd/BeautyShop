# Посібник активації користувачів

## Проблема: "Користувач не може відновити пароль"

Якщо користувач бачить повідомлення що лист надіслано, але не отримує його - **перевірте чи активовано акаунт**.

### Причина

При реєстрації користувач створюється з `is_active=False` і чекає підтвердження email. Django **не відправляє** листи для відновлення паролю неактивним користувачам (це стандартна безпекова функція).

### Рішення 1: Активація через Django Admin (рекомендовано)

1. Перейдіть до Django Admin:
   ```
   https://beautyshop-django.onrender.com/admin/
   ```

2. Увійдіть як адміністратор (використайте дані з `ADMIN_EMAIL` та `ADMIN_PASSWORD`)

3. Перейдіть до розділу **"Користувачі"** (Users)

4. Знайдіть користувача за email: `prometeylabs@gmail.com`

5. **Варіант А: Швидка активація через Actions**
   - Виберіть користувача (поставте галочку)
   - У випадаючому меню "Action" виберіть:
     - **"Активувати користувачів"** - просто активує
     - або **"Підтвердити email"** - активує + підтверджує email
   - Натисніть "Go"

6. **Варіант Б: Ручна активація**
   - Клікніть на ім'я користувача
   - Знайдіть поле **"Active"** (Активний) 
   - Поставте галочку ✓
   - Натисніть "Save"

### Рішення 2: Через Django Shell (для розробників)

```bash
# Локально
python manage.py shell

# На Render
render shell -s beautyshop-django
```

```python
from apps.users.models import CustomUser

# Знайти користувача
user = CustomUser.objects.get(email='prometeylabs@gmail.com')

# Активувати
user.is_active = True
user.email_verified = True
user.save()

print(f"✅ Користувач {user.email} активовано!")
```

### Рішення 3: Відправити лист верифікації повторно

Якщо потрібно щоб користувач сам підтвердив email:

```python
from apps.users.models import CustomUser
from apps.users.utils import send_verification_email
from django.test import RequestFactory

user = CustomUser.objects.get(email='prometeylabs@gmail.com')

# Створюємо mock request
factory = RequestFactory()
request = factory.get('/')
request.META['HTTP_HOST'] = 'beautyshop-django.onrender.com'
request.META['wsgi.url_scheme'] = 'https'

# Відправляємо лист
if send_verification_email(user, request):
    print("✅ Лист відправлено!")
else:
    print("❌ Помилка відправки")
```

## Перевірка статусу користувача

### В Django Admin
Список користувачів показує колонки:
- **email_verified** - чи підтверджено email
- **is_active** - чи активовано акаунт

### В Shell
```python
from apps.users.models import CustomUser

user = CustomUser.objects.get(email='prometeylabs@gmail.com')
print(f"Email: {user.email}")
print(f"Is Active: {user.is_active}")
print(f"Email Verified: {user.email_verified}")
print(f"Username: {user.username}")
```

## Типові проблеми

### 1. Користувач не отримав лист при реєстрації
**Причини:**
- Email потрапив у спам
- Проблема з Gmail App Password
- Помилка в налаштуваннях SMTP

**Рішення:** Активуйте вручну через Admin

### 2. Користувач намагається відновити пароль але лист не приходить
**Причина:** `is_active=False`

**Рішення:** Активуйте через Admin, потім користувач зможе відновити пароль

### 3. Як дізнатися чи працює email?
Перевірте логи Render:
```bash
render logs -s beautyshop-django --tail
```

Шукайте:
- `✅ Verification email sent successfully`
- `❌ Failed to send verification email`
- `📧 Password reset email should be sent`

## Автоматизація активації (опційно)

Якщо хочете **автоматично активувати** користувачів без підтвердження email (не рекомендовано для продакшну), змініть в `apps/users/forms.py`:

```python
def save(self, commit=True):
    user = super().save(commit=False)
    # ... інший код ...
    
    # ЗМІНИТИ ЦЕ:
    user.is_active = False  # На це:
    user.is_active = True   # Автоматична активація
    
    if commit:
        user.save()
    return user
```

**Увага:** Це знижує безпеку - будь-хто зможе зареєструватися з чужим email!

