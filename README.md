# 💄 Beauty Shop - Інтернет-магазин професійної косметики

Повнофункціональний інтернет-магазин професійної косметики та обладнання для салонів краси, розроблений на Django.

## ✨ Особливості

### 🛒 E-commerce функціонал
- **Каталог товарів** з категоріями та фільтрами
- **Кошик без реєстрації** - сесійний кошик
- **Система замовлень** з різними статусами
- **Роздрібні та оптові ціни** (опт від 5000₴/місяць)
- **Кількісні знижки** для всіх користувачів
- **Акційні товари** з відсотком знижки

### 🎨 Дизайн та UX
- **Адаптивний дизайн** для всіх пристроїв
- **Mobile-first підхід** з особливою увагою до iOS Safari
- **Горизонтальні слайдери** для категорій та товарів
- **Touch-friendly інтерфейс** з swipe жестами
- **Колірна схема**: Яскравий рожевий, золотий, темно-сірий
- **Чистий CSS** без `!important` та конфліктів

### 📱 Мобільна оптимізація
- **iOS Safari сумісність** з safe areas
- **Viewport height фікси** для iPhone
- **Hardware acceleration** для smooth анімацій
- **Touch callout контроль** для кращого UX
- **Zoom prevention** на input focus

### 🔧 Технічні особливості
- **Django 4.2+** з модульною архітектурою apps
- **Українська локалізація** повністю
- **SEO готовність** з мета тегами та структурованими даними
- **Готовність до деплою** на Render
- **Адмін панель** для управління контентом

## 🚀 Швидкий старт

### Встановлення

1. **Клонуйте репозиторій:**
```bash
git clone https://github.com/Sophie-sd/BeautyShop.git
cd BeautyShop
```

2. **Створіть віртуальне середовище:**
```bash
python -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate
```

3. **Встановіть залежності:**
```bash
pip install -r requirements.txt
```

4. **Виконайте міграції:**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Створіть суперкористувача:**
```bash
python manage.py createsuperuser
```

6. **Запустіть сервер:**
```bash
python manage.py runserver
```

Сайт буде доступний за адресою: http://127.0.0.1:8000/

## 📁 Структура проекту

```
beautyshop/
├── apps/                    # Django додатки
│   ├── core/               # Основний функціонал
│   ├── products/           # Товари та категорії
│   ├── cart/               # Кошик покупок
│   ├── orders/             # Замовлення
│   ├── users/              # Користувачі
│   └── blog/               # Блог та статті
├── static/                 # Статичні файли
│   ├── css/               # Стилі
│   ├── js/                # JavaScript
│   └── images/            # Зображення
├── templates/             # HTML шаблони
└── beautyshop/           # Налаштування Django
```

## 🎯 Основні сторінки

- **Головна** (`/`) - Hero секція, категорії, рекомендовані товари
- **Каталог** (`/catalog/`) - Всі категорії товарів
- **Кошик** (`/cart/`) - Перегляд та редагування кошика
- **Доставка та оплата** (`/delivery/`) - Інформація про доставку
- **Повернення та обмін** (`/returns/`) - Умови повернення
- **Про нас** (`/about/`) - Інформація про компанію
- **Контакти** (`/contacts/`) - Контактна інформація
- **Адмін панель** (`/admin/`) - Управління контентом

## 🛠 Налаштування для продакшену

### Render деплой

1. **Створіть сервіс на Render**
2. **Підключіть GitHub репозиторій**
3. **Налаштуйте змінні середовища:**
   - `DJANGO_SETTINGS_MODULE=beautyshop.settings.production`
   - `SECRET_KEY=your-secret-key`
   - `DATABASE_URL=your-database-url`

### Змінні середовища

Створіть файл `.env` з наступними змінними:

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=your-database-url
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

## 🎨 Кастомізація

### Кольори
Основні кольори визначені в `static/css/base.css`:
```css
:root {
  --primary-pink: #FF1493;      /* Яскравий рожевий */
  --accent-gold: #FFD700;       /* Золотий */
  --neutral-dark: #2C3E50;      /* Темно-сірий */
}
```

### Слайдери
Горизонтальні слайдери налаштовуються в `static/js/sliders.js` та `static/css/sliders.css`.

## 📱 Мобільна підтримка

### iOS Safari
- Safe area підтримка для iPhone X+
- Viewport height фікси
- Touch оптимізації
- Hardware acceleration

### Android Chrome
- Touch action оптимізація
- Overscroll behavior контроль
- High-DPI підтримка

## 🤝 Внесок у розробку

1. Fork репозиторій
2. Створіть feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit зміни (`git commit -m 'Add some AmazingFeature'`)
4. Push до branch (`git push origin feature/AmazingFeature`)
5. Відкрийте Pull Request

## 📄 Ліцензія

Цей проект розроблений для Beauty Shop Ukraine.

## 👨‍💻 Розробка

Розроблено командою **PrometeyLabs**

---

**Beauty Shop** - професійна косметика для салонів краси 💄✨
