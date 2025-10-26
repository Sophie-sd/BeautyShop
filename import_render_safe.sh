#!/usr/bin/env bash
# БЕЗПЕЧНИЙ імпорт для Render (512MB RAM)
# Імпортує частинами, щоб не перевантажити пам'ять

echo "🚀 БЕЗПЕЧНИЙ ІМПОРТ для Render (обмежена пам'ять)"
echo "=================================================="
echo ""

echo "📊 Поточний стан:"
python manage.py check_import_status
echo ""

echo "⚙️ Налаштування:"
echo "  • Workers: 1 (для мінімального використання пам'яті)"
echo "  • Батчі: по 50 товарів"
echo "  • Без зображень (швидше + менше пам'яті)"
echo ""

echo "📦 КРОК 1/3: Імпорт без зображень (~5 хвилин)..."
python manage.py import_products_sitemap --workers 1 --skip-images --limit 500
echo ""

echo "🔄 Розподіл по категоріях..."
python manage.py assign_categories
echo ""

echo "📦 КРОК 2/3: Продовження імпорту..."
python manage.py import_products_sitemap --workers 1 --skip-images --limit 1000
python manage.py assign_categories
echo ""

echo "📦 КРОК 3/3: Фінальний імпорт..."
python manage.py import_products_sitemap --workers 1 --skip-images
python manage.py assign_categories
echo ""

echo "✅ Імпорт завершено!"
echo ""
echo "📊 Фінальна статистика:"
python manage.py check_import_status
echo ""
echo "💡 Зображення можна завантажити окремо пізніше якщо потрібно"

