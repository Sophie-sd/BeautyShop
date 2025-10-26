#!/usr/bin/env bash
# Скрипт для першого запуску на Render: імпорт + розподіл по категоріях

echo "🚀 Налаштування товарів на Render"
echo "=================================="
echo ""

echo "📊 1. Поточний стан:"
python manage.py check_import_status
echo ""

echo "📦 2. Імпорт товарів (займе ~15-20 хвилин, оптимізовано для 512MB)..."
python manage.py import_products_sitemap --workers 2
echo ""

echo "🔄 3. Розподіл товарів по категоріях..."
python manage.py assign_categories
echo ""

echo "✅ Налаштування завершено!"
echo ""
echo "📊 Фінальна статистика:"
python manage.py check_import_status

