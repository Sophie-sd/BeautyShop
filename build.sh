#!/usr/bin/env bash
set -o errexit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

echo "📊 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "👤 Resetting admin credentials..."
python manage.py reset_admin

echo "✅ Build completed successfully!"
