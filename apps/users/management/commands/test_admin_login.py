"""
Django management command для тестування входу адміністратора
Використання: python manage.py test_admin_login
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from apps.users.models import CustomUser
from django.test import RequestFactory


class Command(BaseCommand):
    help = 'Тестує вхід адміністратора через authentication backends'

    def handle(self, *args, **options):
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.WARNING('🧪 ТЕСТУВАННЯ ВХОДУ АДМІНІСТРАТОРА'))
        self.stdout.write('='*70 + '\n')
        
        # Створюємо фейковий request object
        factory = RequestFactory()
        request = factory.post('/admin/login/')
        
        # Тестові дані
        test_credentials = [
            ('beautyshop_admin', 'BeautyShop2024!'),
            ('admin', 'BeautyShop2024!'),
            ('beautyshop@gmail.com', 'BeautyShop2024!'),
        ]
        
        for username, password in test_credentials:
            self.stdout.write(f'\n🔐 Тестування входу для: {username}')
            self.stdout.write('-' * 70)
            
            # Спочатку перевіряємо чи існує користувач
            user_exists = False
            try:
                # Шукаємо за username
                user = CustomUser.objects.filter(username=username).first()
                if not user:
                    # Шукаємо за email
                    user = CustomUser.objects.filter(email=username).first()
                
                if user:
                    user_exists = True
                    self.stdout.write(self.style.SUCCESS(f'✅ Користувач знайдений:'))
                    self.stdout.write(f'   Username: {user.username}')
                    self.stdout.write(f'   Email: {user.email}')
                    self.stdout.write(f'   is_staff: {user.is_staff}')
                    self.stdout.write(f'   is_superuser: {user.is_superuser}')
                    self.stdout.write(f'   is_active: {user.is_active}')
                    
                    # Перевіряємо пароль
                    password_valid = user.check_password(password)
                    if password_valid:
                        self.stdout.write(self.style.SUCCESS(f'✅ Пароль валідний'))
                    else:
                        self.stdout.write(self.style.ERROR(f'❌ Пароль НЕ валідний'))
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Користувач НЕ знайдений'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Помилка пошуку користувача: {e}'))
            
            # Тепер пробуємо authenticate через Django backends
            if user_exists:
                self.stdout.write(f'\n🔐 Тестування через Django authenticate():')
                try:
                    authenticated_user = authenticate(
                        request=request,
                        username=username,
                        password=password
                    )
                    
                    if authenticated_user:
                        self.stdout.write(self.style.SUCCESS(f'✅ Аутентифікація УСПІШНА'))
                        self.stdout.write(f'   User: {authenticated_user.username}')
                        self.stdout.write(f'   Backend: {authenticated_user.backend if hasattr(authenticated_user, "backend") else "Unknown"}')
                    else:
                        self.stdout.write(self.style.ERROR(f'❌ Аутентифікація НЕВДАЛА'))
                        self.stdout.write(f'   Можливі причини:')
                        self.stdout.write(f'   - Невірний пароль')
                        self.stdout.write(f'   - Користувач не активний (is_active=False)')
                        self.stdout.write(f'   - Backend відхилив користувача')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Помилка аутентифікації: {e}'))
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ ТЕСТУВАННЯ ЗАВЕРШЕНО'))
        self.stdout.write('='*70 + '\n')

