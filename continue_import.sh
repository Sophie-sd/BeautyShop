#!/usr/bin/env bash
# Продовження імпорту на Render (пропускає існуючі товари)

echo "🔄 Продовження імпорту товарів..."
echo "=================================="
echo ""

# Показуємо поточну статистику
echo "📊 Поточний стан:"
python manage.py check_import_status
echo ""
echo "⏳ Запуск додаткового імпорту (це займе ~10 хвилин)..."
echo "   Дублікати будуть автоматично пропущені!"
echo ""

# Запускаємо з меншою кількістю workers для стабільності
python manage.py import_products_sitemap --workers 3

echo ""
echo "✅ Імпорт завершено!"
echo ""
echo "📊 Фінальна статистика:"
python manage.py check_import_status

