# 📦 Інструкція з деплою товарів на Render

## 🎯 Огляд процесу

Система автоматично імпортує товари на Render з готових JSON файлів. Зображення зберігаються на Cloudinary.

---

## 🚀 Процес деплою

### 1️⃣ **Локальна підготовка (виконується один раз)**

```bash
# 1. Імпорт товарів з webosova на Cloudinary
python manage.py import_products_cloudinary --limit 2500

# 2. Експорт товарів у JSON файли
python manage.py export_products_json

# 3. Перевірте що створилися файли
ls -la products_data/
# Має бути: products_1.json, products_2.json, ... products_6.json

# 4. Додайте файли в git
git add products_data/
git commit -m "Add products data for Render import"
git push origin main
```

### 2️⃣ **Налаштування на Render.com**

1. Відкрийте Dashboard → Your Service → Environment
2. Додайте змінні оточення:

```
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
AUTO_IMPORT_PRODUCTS=true
```

3. Збережіть зміни

### 3️⃣ **Деплой**

Просто зробіть push в git - Render автоматично:
- Встановить залежності
- Створить категорії
- Імпортує всі товари з JSON
- Розкладе їх по категоріям
- Підключить зображення з Cloudinary

```bash
git push origin main
```

---

## 📂 Структура файлів

```
products_data/
├── products_1.json  # 500 товарів
├── products_2.json  # 500 товарів
├── products_3.json  # 500 товарів
├── products_4.json  # 500 товарів
├── products_5.json  # 500 товарів
└── products_6.json  # решта товарів
```

### Формат JSON

```json
[
  {
    "name": "Назва товару",
    "slug": "nazva-tovaru",
    "category_slug": "nigti",
    "description": "Опис...",
    "retail_price": "100.00",
    "wholesale_price": "80.00",
    "sale_price": null,
    "price_3_qty": "95.00",
    "price_5_qty": "90.00",
    "is_sale": false,
    "is_top": false,
    "is_new": false,
    "is_featured": false,
    "stock": 100,
    "is_active": true,
    "sku": "BS00123",
    "images": [
      {
        "path": "products/product_1.jpg",
        "is_main": true,
        "sort_order": 0,
        "alt_text": "Альтернативний текст"
      }
    ],
    "attributes": [
      {
        "name": "Об'єм",
        "value": "100 мл",
        "sort_order": 0
      }
    ]
  }
]
```

---

## 📊 Категорії товарів

Товари автоматично розподіляються за категоріями:

1. **Акційні товари** (`sale`)
2. **Нігті** (`nigti`)
3. **Волосся** (`volossia`)
4. **Брови та вії** (`brovy-ta-vii`)
5. **Депіляція** (`depilyatsiya`)
6. **Косметика** (`kosmetyka`)
7. **Макіяж** (`makiyazh`)
8. **Одноразова продукція** (`odnorazova-produktsia`)
9. **Дезінфекція та стерилізація** (`dezinfektsiya-ta-sterylizatsiya`)
10. **Меблі для салонів** (`mebli-dlya-saloniv`)
11. **Імпорт з Webosova** (`import-webosova`) - тимчасова для нерозпізнаних

---

## 🛠️ Management команди

### Імпорт товарів з вебсайту (локально)
```bash
# Імпорт з автоматичним завантаженням на Cloudinary
python manage.py import_products_cloudinary --limit 2500

# З налаштуваннями
python manage.py import_products_cloudinary --batch-size 200 --workers 2
```

### Експорт у JSON
```bash
# Експорт всіх товарів
python manage.py export_products_json

# В іншу папку
python manage.py export_products_json --output my_data
```

### Реімпорт на Render (автоматично)
```bash
# Виконується автоматично при build, але можна запустити вручну:
python manage.py reimport_products --input products_data
```

### Створення категорій
```bash
python manage.py create_categories
```

### Перевірка статусу
```bash
python manage.py check_import_status
```

---

## ⚙️ Як працює система

### Build процес (build.sh)

1. **Встановлення залежностей**
   ```bash
   pip install -r requirements.txt
   ```

2. **Збирання статики**
   ```bash
   python manage.py collectstatic --no-input
   ```

3. **Міграції БД**
   ```bash
   python manage.py migrate --no-input
   ```

4. **Створення категорій**
   ```bash
   python manage.py create_categories
   ```

5. **Створення адміна**
   - Автоматично створюється якщо не існує

6. **Імпорт товарів** (якщо `AUTO_IMPORT_PRODUCTS=true`)
   ```bash
   python manage.py reimport_products --input products_data
   ```

---

## 🔄 Оновлення товарів

### Повний реімпорт

```bash
# Локально: оновити дані
python manage.py import_products_cloudinary --limit 2500
python manage.py export_products_json

# Git push
git add products_data/
git commit -m "Update products data"
git push origin main

# На Render автоматично відбудеться реімпорт
```

### Часткове оновлення

Для часткового оновлення краще використовувати Django Admin панель.

---

## ⚠️ Важливі примітки

### Зображення
- Всі зображення зберігаються на **Cloudinary**
- В JSON зберігається тільки `path` (не повний URL)
- Cloudinary автоматично генерує URL при запиті
- Формат: `products/product-name_1.jpg`

### Продуктивність
- Процес імпорту займає 5-15 хвилин
- Обробляється ~2500 товарів
- Використовується батчинг по 500 товарів

### Лімити Render (Free Plan)
- 512 MB RAM
- Build timeout: 15 хвилин
- Може потребувати повторного деплою якщо timeout

---

## 🐛 Troubleshooting

### Проблема: Товари не імпортуються

**Рішення:**
1. Перевірте що `AUTO_IMPORT_PRODUCTS=true` в Environment Variables
2. Перевірте наявність `products_data/` в репозиторії
3. Перегляньте логи build процесу на Render

### Проблема: Зображення не відображаються

**Рішення:**
1. Перевірте Cloudinary credentials
2. Перевірте що path в JSON відповідає структурі на Cloudinary
3. Перевірте налаштування CORS на Cloudinary

### Проблема: Timeout під час build

**Рішення:**
1. Зменшіть кількість товарів або розділіть на частини
2. Запустіть імпорт вручну через Render Shell після деплою
3. Встановіть `AUTO_IMPORT_PRODUCTS=false` і імпортуйте через Shell

### Імпорт через Render Shell (якщо timeout)

```bash
# В Render Dashboard → Shell
python manage.py reimport_products --input products_data
```

---

## 📈 Статистика після імпорту

Build скрипт автоматично виведе статистику:
```
📊 Фінальна статистика:
  • Всього товарів: 2456
  • Активних категорій: 11
  • Нігті: 856 товарів
  • Волосся: 324 товарів
  • Брови та вії: 198 товарів
  • Депіляція: 445 товарів
  ...
```

---

## 🎉 Готово!

Після успішного деплою всі товари будуть доступні на сайті з:
- Правильними категоріями
- Зображеннями з Cloudinary
- Всіма атрибутами та характеристиками
- Правильними цінами (роздріб, опт, градація)

---

## 📞 Підтримка

При виникненні питань або проблем:
1. Перевірте логи на Render Dashboard
2. Запустіть `python manage.py check_import_status` для діагностики
3. Перегляньте цей документ повторно

**Успішного деплою! 🚀**

