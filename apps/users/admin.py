"""
Адміністративна панель для користувачів
"""
from django.contrib import admin
from django.contrib.auth.models import Group

# Приховуємо "Групи" з адміністративної панелі (не використовуються в проекті)
admin.site.unregister(Group)
