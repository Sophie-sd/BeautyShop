#!/usr/bin/env bash
# Build script для Render.com
set -e  # Зупинити при помилках

echo "🔨 BUILD PROCESS STARTED"
echo "========================"
echo ""

# Встановлюємо залежності
echo "📦 Встановлення залежностей..."
pip install -r requirements.txt
echo "✅ Залежності встановлено"
echo ""

# Створюємо папку для медіа (якщо потрібно)
mkdir -p media
chmod 755 media

# Збираємо статичні файли
echo "📁 Збирання статичних файлів..."
python manage.py collectstatic --no-input
echo "✅ Статичні файли зібрано"
echo ""

# Застосовуємо міграції
echo "🗄️  Застосування міграцій бази даних..."
python manage.py migrate --no-input
echo "✅ Міграції застосовано"
echo ""

# Створюємо категорії (безпечно)
echo "📂 Створення категорій товарів..."
python manage.py create_categories
echo "✅ Категорії створено"
echo ""

# Створюємо суперюзера якщо не існує
echo "👤 Створення суперюзера..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
import os
User = get_user_model()
admin_email = os.getenv('ADMIN_EMAIL', 'beautyshop.supp@gmail.com')
admin_password = os.getenv('ADMIN_PASSWORD', 'ChangeMe123!')
if not User.objects.filter(email=admin_email).exists():
    user = User.objects.create_superuser(
        username='admin',
        email=admin_email,
        password=admin_password,
        phone='+380681752654',
        first_name='Admin',
        last_name='BeautyShop'
    )
    print('✅ Superuser створено: ' + admin_email)
else:
    print('⚠️ Superuser вже існує: ' + admin_email)
"
echo ""

# Автоматичний імпорт товарів з готових JSON (зображення вже на Cloudinary)
if [ "$AUTO_IMPORT_PRODUCTS" = "true" ]; then
    echo "========================"
    echo "🚀 АВТОМАТИЧНИЙ ІМПОРТ ТОВАРІВ"
    echo "========================"
    echo ""
    
    if [ -d "products_data" ]; then
        # Перевіряємо чи є JSON файли
        json_count=$(ls -1 products_data/*.json 2>/dev/null | wc -l)
        
        if [ "$json_count" -gt 0 ]; then
            echo "📦 Знайдено JSON файлів: $json_count"
            echo "🔄 Запуск повного реімпорту товарів..."
            echo ""
            
            # Запускаємо повний реімпорт (очищення + імпорт в одній команді)
            python manage.py reimport_products --input products_data
            
            echo ""
            echo "✅ Реімпорт товарів завершено успішно!"
            
            # Виводимо статистику
            echo ""
            echo "📊 Фінальна статистика:"
            python manage.py shell -c "
from apps.products.models import Product, Category
total_products = Product.objects.count()
total_categories = Category.objects.filter(is_active=True).count()
print(f'  • Всього товарів: {total_products}')
print(f'  • Активних категорій: {total_categories}')
for cat in Category.objects.filter(is_active=True).order_by('sort_order'):
    count = Product.objects.filter(category=cat).count()
    if count > 0:
        print(f'  • {cat.name}: {count} товарів')
"
        else
            echo "⚠️ JSON файли не знайдені в папці products_data/"
            echo "   Імпорт пропущено"
        fi
    else
        echo "❌ Папка products_data не знайдена"
        echo ""
        echo "📝 Для додавання товарів виконайте локально:"
        echo "   1. python manage.py import_products_cloudinary --limit 2500"
        echo "   2. python manage.py export_products_json"
        echo "   3. git add products_data/ && git commit -m 'Add products data' && git push"
        echo ""
        echo "   Після цього товари автоматично імпортуються при наступному деплої"
    fi
else
    echo "========================"
    echo "ℹ️  ІМПОРТ ТОВАРІВ ВИМКНЕНО"
    echo "========================"
    echo ""
    echo "Для увімкнення автоматичного імпорту встановіть:"
    echo "AUTO_IMPORT_PRODUCTS=true в Environment Variables на Render"
fi

echo ""
echo "========================"
echo "✅ BUILD COMPLETED SUCCESSFULLY!"
echo "========================"