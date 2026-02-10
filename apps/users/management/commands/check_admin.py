"""
Django management command для перевірки стану адміністратора
Використання: python manage.py check_admin
"""
from django.core.management.base import BaseCommand
from apps.users.models import CustomUser
import json
import time


class Command(BaseCommand):
    help = 'Перевіряє стан адміністратора в базі даних'

    def handle(self, *args, **options):
        # #region agent log
        with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({
                'location': 'check_admin.py:18',
                'message': 'check_admin command started',
                'data': {},
                'timestamp': int(time.time() * 1000),
                'hypothesisId': 'D,E'
            }) + '\n')
        # #endregion
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.WARNING('🔍 ПЕРЕВІРКА АДМІНІСТРАТОРА'))
        self.stdout.write('='*70 + '\n')
        
        # Шукаємо всіх суперюзерів
        superusers = CustomUser.objects.filter(is_superuser=True)
        
        if not superusers.exists():
            self.stdout.write(self.style.ERROR('❌ СУПЕРЮЗЕРИ НЕ ЗНАЙДЕНІ!'))
            # #region agent log
            with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'check_admin.py:38',
                    'message': 'No superusers found',
                    'data': {},
                    'timestamp': int(time.time() * 1000),
                    'hypothesisId': 'D,E'
                }) + '\n')
            # #endregion
            return
        
        for user in superusers:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Суперюзер знайдений:'))
            self.stdout.write(f'   ID: {user.id}')
            self.stdout.write(f'   Username: {user.username}')
            self.stdout.write(f'   Email: {user.email}')
            self.stdout.write(f'   Phone: {user.phone or "не встановлено"}')
            self.stdout.write(f'   First name: {user.first_name}')
            self.stdout.write(f'   Last name: {user.last_name}')
            self.stdout.write(f'   is_active: {user.is_active}')
            self.stdout.write(f'   is_staff: {user.is_staff}')
            self.stdout.write(f'   is_superuser: {user.is_superuser}')
            self.stdout.write(f'   has_usable_password: {user.has_usable_password()}')
            self.stdout.write(f'   password (перші 30 символів): {user.password[:30]}')
            self.stdout.write(f'   date_joined: {user.date_joined}')
            self.stdout.write(f'   last_login: {user.last_login or "ніколи"}')
            
            # #region agent log
            with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'check_admin.py:68',
                    'message': 'Superuser details',
                    'data': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'phone': user.phone,
                        'is_active': user.is_active,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                        'has_usable_password': user.has_usable_password(),
                        'password_prefix': user.password[:30],
                        'password_algorithm': user.password.split('$')[0] if '$' in user.password else 'unknown',
                    },
                    'timestamp': int(time.time() * 1000),
                    'hypothesisId': 'A,C,D'
                }) + '\n')
            # #endregion
            
            # Тест паролю з ENV
            import os
            test_password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'BeautyShop2024!')
            password_check = user.check_password(test_password)
            
            self.stdout.write(f'\n   🔐 Тест паролю з ENV:')
            self.stdout.write(f'   Пароль: {test_password}')
            self.stdout.write(f'   Результат: {"✅ ВАЛІДНИЙ" if password_check else "❌ НЕВАЛІДНИЙ"}')
            
            # #region agent log
            with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'check_admin.py:100',
                    'message': 'Password test result',
                    'data': {
                        'username': user.username,
                        'test_password_length': len(test_password),
                        'password_check': password_check,
                    },
                    'timestamp': int(time.time() * 1000),
                    'hypothesisId': 'A,B'
                }) + '\n')
            # #endregion
            
            self.stdout.write('-' * 70)
        
        # Шукаємо користувача "beautyshop_admin" окремо
        try:
            specific_user = CustomUser.objects.get(username='beautyshop_admin')
            self.stdout.write(self.style.SUCCESS(f'\n✅ Користувач "beautyshop_admin" знайдений'))
            # #region agent log
            with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'check_admin.py:123',
                    'message': 'beautyshop_admin found',
                    'data': {
                        'exists': True,
                        'is_superuser': specific_user.is_superuser,
                    },
                    'timestamp': int(time.time() * 1000),
                    'hypothesisId': 'E'
                }) + '\n')
            # #endregion
        except CustomUser.DoesNotExist:
            self.stdout.write(self.style.ERROR('\n❌ Користувач "beautyshop_admin" НЕ знайдений'))
            # #region agent log
            with open('/Users/sofiadmitrenko/Sites/beautyshop/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    'location': 'check_admin.py:137',
                    'message': 'beautyshop_admin not found',
                    'data': {'exists': False},
                    'timestamp': int(time.time() * 1000),
                    'hypothesisId': 'E'
                }) + '\n')
            # #endregion
        
        self.stdout.write('\n' + '='*70)
