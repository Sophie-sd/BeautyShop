#!/usr/bin/env bash
# Скрипт для імпорту товарів на Render через Shell

echo "🚀 Імпорт товарів з Webosova на Render"
echo "========================================"
echo ""
echo "📦 Запуск імпорту (це займе ~10-15 хвилин)..."
echo ""

# Імпортуємо товари
python manage.py import_products_sitemap --workers 5

echo ""
echo "✅ Імпорт завершено!"
echo ""
echo "📊 Статистика:"
python manage.py check_import_status

