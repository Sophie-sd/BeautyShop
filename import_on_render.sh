#!/usr/bin/env bash
# Скрипт для імпорту товарів на Render через Shell

echo "🚀 Імпорт товарів з Webosova на Render"
echo "========================================"
echo "⚙️  Режим: оптимізовано для обмеженої пам'яті (512MB)"
echo ""
echo "📦 Запуск імпорту (це займе ~15-20 хвилин)..."
echo ""

# Імпортуємо товари (обмежено 2 workers для економії пам'яті)
python manage.py import_products_sitemap --workers 2

echo ""
echo "✅ Імпорт завершено!"
echo ""
echo "📊 Статистика:"
python manage.py check_import_status

