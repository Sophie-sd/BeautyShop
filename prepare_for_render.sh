#!/usr/bin/env bash
# Локальний скрипт підготовки товарів для Render
# Зображення завантажуються на Cloudinary, дані експортуються в JSON

echo "🚀 Підготовка товарів для Render"
echo "=================================="
echo ""

# Перевірка Cloudinary credentials
if [ -z "$CLOUDINARY_CLOUD_NAME" ]; then
    echo "❌ CLOUDINARY_CLOUD_NAME не встановлено"
    echo "   Встановіть змінні оточення:"
    echo "   export CLOUDINARY_CLOUD_NAME=your-cloud-name"
    echo "   export CLOUDINARY_API_KEY=your-api-key"
    echo "   export CLOUDINARY_API_SECRET=your-api-secret"
    exit 1
fi

echo "✅ Cloudinary credentials знайдено"
echo "   Cloud: $CLOUDINARY_CLOUD_NAME"
echo ""

# Крок 1: Імпорт товарів з завантаженням на Cloudinary
echo "📦 Крок 1: Імпорт товарів з beautyshop-ukrane.com.ua"
echo "   Зображення завантажуються на Cloudinary..."
echo ""

read -p "Скільки товарів імпортувати? (Enter для всіх): " LIMIT

if [ -z "$LIMIT" ]; then
    python3 manage.py import_products_cloudinary --workers 3
else
    python3 manage.py import_products_cloudinary --limit $LIMIT --workers 3
fi

if [ $? -ne 0 ]; then
    echo "❌ Помилка імпорту"
    exit 1
fi

echo ""
echo "✅ Імпорт завершено!"
echo ""

# Крок 2: Розподіл по категоріях
echo "📂 Крок 2: Розподіл товарів по категоріях..."
python3 manage.py assign_categories

echo ""
echo "✅ Розподіл завершено!"
echo ""

# Крок 3: Експорт в JSON
echo "💾 Крок 3: Експорт товарів в JSON..."
python3 manage.py export_products_json --output products_data

if [ $? -ne 0 ]; then
    echo "❌ Помилка експорту"
    exit 1
fi

echo ""
echo "✅ Експорт завершено!"
echo ""

# Підсумок
echo "=================================="
echo "✅ Підготовка завершена!"
echo ""
echo "📂 JSON файли в папці: products_data/"
echo "📷 Зображення на Cloudinary: $CLOUDINARY_CLOUD_NAME"
echo ""
echo "🚀 Наступні кроки:"
echo "   1. git add products_data/"
echo "   2. git commit -m 'Додано товари для імпорту'"
echo "   3. git push"
echo "   4. На Render встановіть: AUTO_IMPORT_PRODUCTS=true"
echo "   5. Deploy запуститься автоматично"
echo ""

