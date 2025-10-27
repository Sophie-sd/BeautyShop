# 🚀 Швидкий старт: Імпорт товарів

## Для локальної розробки

```bash
# 1. Імпорт товарів з webosova (зображення на Cloudinary)
python manage.py import_products_cloudinary --limit 2500

# 2. Експорт у JSON для Render
python manage.py export_products_json

# 3. Перевірка
python manage.py check_import_status
```

## Для деплою на Render

```bash
# 1. Додайте JSON файли в git
git add products_data/
git commit -m "Add products for auto-import"
git push origin main

# 2. Встановіть на Render: AUTO_IMPORT_PRODUCTS=true
# 3. Деплой відбудеться автоматично
```

## Структура категорій

- `nigti` - Нігті (гель-лаки, бази, топи)
- `volossia` - Волосся (шампуні, маски)
- `brovy-ta-vii` - Брови та вії
- `depilyatsiya` - Депіляція (шугарінг, віск, паста)
- `kosmetyka` - Косметика (креми, сироватки)
- `makiyazh` - Макіяж (помада, туш)
- `odnorazova-produktsia` - Одноразова продукція
- `dezinfektsiya-ta-sterylizatsiya` - Дезінфекція
- `mebli-dlya-saloniv` - Меблі
- `sale` - Акційні товари

## Команди

```bash
# Створити категорії
python manage.py create_categories

# Імпорт з вебсайту
python manage.py import_products_cloudinary --limit 2500 --workers 2

# Експорт у JSON
python manage.py export_products_json --output products_data

# Реімпорт з JSON
python manage.py reimport_products --input products_data

# Статус імпорту
python manage.py check_import_status
```

## Детальна інструкція

Дивіться файл [DEPLOY_INSTRUCTIONS.md](DEPLOY_INSTRUCTIONS.md)

