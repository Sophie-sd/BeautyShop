#!/usr/bin/env bash
# Тест імпорту локально (10 товарів)

echo "🧪 Тестовий імпорт 10 товарів"
echo ""

# Перевірка Django
python3 manage.py check

# Імпорт 10 товарів для тесту
python3 manage.py import_products_cloudinary --limit 10 --workers 2

echo ""
echo "✅ Перевірте зображення на Cloudinary"
echo "   Якщо все ок - запускайте prepare_for_render.sh для повного імпорту"

