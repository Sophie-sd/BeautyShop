#!/usr/bin/env bash
# Build script для Render.com

# Встановлюємо залежності
pip install -r requirements.txt

# Збираємо статичні файли
python manage.py collectstatic --no-input

# Застосовуємо міграції
python manage.py migrate --no-input

# Створюємо категорії (безпечно)
python manage.py create_categories

# Створюємо суперюзера якщо не існує
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
    print(f'✅ Superuser created: {admin_email}')
else:
    print(f'⚠️ Superuser already exists: {admin_email}')
"

# Автоматичний імпорт товарів з готових JSON (зображення вже на Cloudinary)
if [ "$AUTO_IMPORT_PRODUCTS" = "true" ]; then
    echo "🚀 Автоматичний імпорт товарів увімкнено..."
    
    # Перевіряємо чи є вже товари
    PRODUCT_COUNT=$(python manage.py shell -c "from apps.products.models import Product; print(Product.objects.count())")
    
    if [ "$PRODUCT_COUNT" -lt 100 ]; then
        echo "📦 Імпортуємо товари з JSON файлів..."
        echo "   ⚡ Швидкий імпорт без завантаження зображень"
        echo "   📷 Зображення вже на Cloudinary"
        
        # Імпортуємо готові дані (економить RAM)
        if [ -d "products_data" ]; then
            python manage.py import_from_json --input products_data
            echo "✅ Імпорт завершено!"
        else
            echo "❌ Папка products_data не знайдена"
            echo "   Запустіть локально:"
            echo "   1. python manage.py import_products_cloudinary --limit 2500"
            echo "   2. python manage.py export_products_json"
            echo "   3. git add products_data/ && git commit && git push"
        fi
    else
        echo "⚠️ Товари вже імпортовані (знайдено $PRODUCT_COUNT шт). Пропускаємо імпорт."
    fi
else
    echo "ℹ️ Автоматичний імпорт вимкнено. Встановіть AUTO_IMPORT_PRODUCTS=true для увімкнення."
fi

echo "✅ Build completed successfully!"