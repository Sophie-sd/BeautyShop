#!/usr/bin/env bash
# УЛЬТРА-БЕЗПЕЧНИЙ імпорт для Render
# Імпортує дуже повільно, але стабільно

echo "🐌 УЛЬТРА-БЕЗПЕЧНИЙ ІМПОРТ (дуже повільно, але стабільно)"
echo "=========================================================="
echo ""

# Вимикаємо всі фонові процеси
pkill -f "manage.py" 2>/dev/null

echo "📊 Поточний стан:"
python manage.py check_import_status
echo ""

echo "⚙️ Режим:"
echo "  • 1 worker"
echo "  • По 50 товарів за раз"
echo "  • З паузами між батчами"
echo "  • Без зображень"
echo "  • З retry на помилки"
echo ""

# Імпортуємо по 50 товарів 10 разів
for i in {1..10}; do
    echo "🔄 Ітерація $i/10..."
    python manage.py import_products_sitemap --workers 1 --skip-images --limit 50
    echo "  Пауза 5 секунд..."
    sleep 5
    
    # Розподіл кожні 3 ітерації
    if [ $((i % 3)) -eq 0 ]; then
        echo "  📂 Розподіл по категоріях..."
        python manage.py assign_categories
    fi
    
    gc.collect 2>/dev/null || true
done

echo ""
echo "✅ Імпорт завершено!"
echo ""
python manage.py check_import_status

