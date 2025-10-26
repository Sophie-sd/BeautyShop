# 🚀 Інструкція по імпорту товарів на Render

## Проблема
Товари імпортовані **локально**, а на Render інша база даних (PostgreSQL). Тому на сайті товарів немає.

## Рішення

### Варіант 1: Через Render Shell (РЕКОМЕНДОВАНИЙ)

1. **Відкрийте Dashboard Render:**
   - Перейдіть на https://dashboard.render.com
   - Виберіть ваш сервіс `beautyshop-django`

2. **Відкрийте Shell:**
   - Натисніть вкладку **"Shell"** зверху
   - Дочекайтесь підключення до сервера

3. **Запустіть імпорт:**
   ```bash
   python manage.py import_products_sitemap --workers 5
   ```

4. **Дочекайтесь завершення** (~10-15 хвилин)

5. **Перевірте результат:**
   ```bash
   python manage.py check_import_status
   ```

### Варіант 2: Через Git Push з автоматичним імпортом

Додайте команду імпорту в `build.sh`, але **УВАГА**: це збільшить час деплою на 10-15 хвилин при кожному push.

### Варіант 3: Одноразовий Job на Render

1. В Dashboard Render створіть **Background Worker**
2. Встановіть команду: `python manage.py import_products_sitemap`
3. Запустіть вручну

## Після імпорту

Товари з'являться:
- ✅ В адмінці: `https://beautyshop-django.onrender.com/admin/products/product/`
- ✅ На сайті: `https://beautyshop-django.onrender.com/products/`

## Перевірка статусу

Виконайте в Render Shell:
```bash
python manage.py check_import_status
```

Має показати:
- Всього товарів: 2500+
- Зображень: 7400+
- Категорій: 12

## Важливо

⚠️ **Імпорт потрібно запустити ОДИН РАЗ** на Render сервері
⚠️ Не додавайте імпорт в `build.sh` - це сповільнить кожен deploy
⚠️ Використовуйте `--workers 5` на Render (не 10, бо менше ресурсів)

