"""
Django management command для перевірки стану адміністратора
Використання: python manage.py check_admin
"""
from django.core.management.base import BaseCommand
from apps.users.models import CustomUser
import os


class Command(BaseCommand):
    help = 'Перевіряє стан адміністратора в базі даних'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.WARNING('🔍 ПЕРЕВІРКА АДМІНІСТРАТОРА'))
        self.stdout.write('='*70 + '\n')
        
        # Шукаємо всіх суперюзерів
        superusers = CustomUser.objects.filter(is_superuser=True)
        
        if not superusers.exists():
            self.stdout.write(self.style.ERROR('❌ СУПЕРЮЗЕРИ НЕ ЗНАЙДЕНІ!'))
            
            # Також перевіримо чи є користувачі взагалі
            total_users = CustomUser.objects.count()
            self.stdout.write(f'\n   Всього користувачів в БД: {total_users}')
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ Знайдено {superusers.count()} суперюзер(ів)\n'))
        
        for user in superusers:
            self.stdout.write(self.style.SUCCESS(f'✅ Суперюзер #{user.id}:'))
            self.stdout.write(f'   Username: {user.username}')
            self.stdout.write(f'   Email: {user.email}')
            self.stdout.write(f'   Phone: {user.phone or "не встановлено"}')
            self.stdout.write(f'   First name: {user.first_name}')
            self.stdout.write(f'   Last name: {user.last_name}')
            self.stdout.write(f'   is_active: {user.is_active}')
            self.stdout.write(f'   is_staff: {user.is_staff}')
            self.stdout.write(f'   is_superuser: {user.is_superuser}')
            self.stdout.write(f'   has_usable_password: {user.has_usable_password()}')
            self.stdout.write(f'   password (algorithm): {user.password.split("$")[0] if "$" in user.password else "unknown"}')
            self.stdout.write(f'   password (перші 30 символів): {user.password[:30]}')
            self.stdout.write(f'   date_joined: {user.date_joined}')
            self.stdout.write(f'   last_login: {user.last_login or "ніколи"}')
            
            # Тест паролю з ENV
            test_password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'BeautyShop2024!')
            password_check = user.check_password(test_password)
            
            self.stdout.write(f'\n   🔐 Тест паролю з ENV:')
            self.stdout.write(f'   Пароль для тесту: {test_password}')
            self.stdout.write(f'   Результат check_password(): {"✅ ВАЛІДНИЙ" if password_check else "❌ НЕВАЛІДНИЙ"}')
            
            self.stdout.write('-' * 70)
        
        # Шукаємо користувача "beautyshop_admin" окремо
        self.stdout.write('\n' + self.style.WARNING('🔍 Пошук конкретного користувача "beautyshop_admin":'))
        try:
            specific_user = CustomUser.objects.get(username='beautyshop_admin')
            self.stdout.write(self.style.SUCCESS('   ✅ Знайдений'))
            if not specific_user.is_superuser:
                self.stdout.write(self.style.ERROR('   ⚠️  НЕ є суперюзером!'))
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('   ❌ НЕ знайдений'))
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write('💡 Підказка: Якщо пароль невалідний, запустіть: python manage.py reset_admin')
        self.stdout.write('='*70 + '\n')

