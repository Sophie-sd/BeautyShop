# 📦 Гайд по імпорту товарів з Webosova

## Виконано імпорт

✅ **2500 товарів** імпортовано з https://beautyshop-ukrane.com.ua/
✅ **7420 зображень** завантажено та оптимізовано
✅ Всі товари доступні в адмінці для редагування

## Команди для роботи

### Перевірка статусу
```bash
python manage.py check_import_status
```

### Повторний імпорт (якщо потрібно)
```bash
python manage.py import_products_sitemap --workers 10
```

### Імпорт з обмеженням (для тестування)
```bash
python manage.py import_products_sitemap --limit 10 --skip-images
```

## Робота з товарами в адмінці

### 📂 Категорії
Всі імпортовані товари зараз в категорії **"Імпорт з Webosova"** (`/admin/products/category/`)

Рекомендується:
1. Створити правильні категорії (Нігті, Волосся, і т.д.)
2. Масово перенести товари через адмінку

### 💰 Ціни
Кожен товар має:
- **retail_price** - імпортована ціна
- **wholesale_price** - можна встановити оптову
- **sale_price** - для акцій
- **price_3_qty** / **price_5_qty** - градації цін

### 🏷️ Стікери та мітки
Доступно:
- `is_top` - Хіт продажів
- `is_new` - Новинка
- `is_sale` - Акційний товар
- `is_featured` - Рекомендований

### 📷 Зображення
Зображення автоматично:
- Оптимізовані до 800x800px
- Конвертовані в JPEG
- Перше зображення встановлено як головне

## Масові операції

### Приклад: встановити акцію на категорію
```python
from apps.products.models import Product, Category

category = Category.objects.get(slug='nigti')
products = Product.objects.filter(category=category)

for product in products:
    product.sale_price = product.retail_price * 0.9  # 10% знижка
    product.is_sale = True
    product.save()
```

### Приклад: перенести товари в нову категорію
```python
from apps.products.models import Product, Category

old_cat = Category.objects.get(slug='import-webosova')
new_cat = Category.objects.get(slug='nigti')

Product.objects.filter(
    category=old_cat,
    name__icontains='гель-лак'
).update(category=new_cat)
```

## Структура даних

Кожен товар містить:
- Назва (`name`)
- Slug (автогенерований)
- SKU (автогенерований: BS00001, BS00002...)
- Опис (`description`)
- Ціна (`retail_price`)
- Зображення (через `ProductImage`)
- Характеристики (через `ProductAttribute`)
- Кількість на складі (`stock` = 100 за замовчуванням)

## Технічна інформація

### Файли команд
- `apps/products/management/commands/import_products_sitemap.py` - основний парсер
- `apps/products/management/commands/check_import_status.py` - перевірка статусу

### Встановлені залежності
- `beautifulsoup4==4.12.3` - парсинг HTML
- `requests==2.32.5` - HTTP запити
- `Pillow==11.3.0` - обробка зображень

### Продуктивність
- ~4 товари/секунду
- Паралельна обробка (10 потоків)
- Автоматична оптимізація зображень

