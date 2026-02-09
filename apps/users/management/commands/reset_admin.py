"""
Django management command для скидання паролю адміністратора
Використання: python manage.py reset_admin
"""
from django.core.management.base import BaseCommand
from apps.users.models import CustomUser
import os


class Command(BaseCommand):
    help = 'Скидає пароль адміністратора або створює нового'

    def handle(self, *args, **options):
        # Новий пароль
        new_password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'BeautyShop2024!')
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.WARNING('🔄 СКИДАННЯ ПАРОЛЮ АДМІНІСТРАТОРА'))
        self.stdout.write('='*70 + '\n')
        
        # Шукаємо суперюзерів
        superusers = CustomUser.objects.filter(is_superuser=True, is_staff=True)
        
        if superusers.exists():
            for user in superusers:
                user.set_password(new_password)
                user.is_active = True
                user.save()
                
                self.stdout.write(self.style.SUCCESS(f'✅ Пароль оновлено:'))
                self.stdout.write(f'   👤 Username: {user.username}')
                self.stdout.write(f'   📧 Email: {user.email}')
                self.stdout.write(f'   🔑 Password: {new_password}')
                self.stdout.write('-' * 70)
        else:
            # Створюємо нового
            self.stdout.write(self.style.WARNING('⚠️  Суперюзери не знайдені. Створюю нового...\n'))
            
            username = os.getenv('ADMIN_USERNAME', 'admin')
            email = os.getenv('ADMIN_EMAIL', 'beautyshop.supp@gmail.com')
            phone = os.getenv('ADMIN_PHONE', '+380681752654')
            
            try:
                user = CustomUser.objects.create_superuser(
                    username=username,
                    email=email,
                    password=new_password,
                    phone=phone,
                    first_name='Admin',
                    last_name='BeautyShop'
                )
                user.is_active = True
                user.email_verified = True
                user.save()
                
                self.stdout.write(self.style.SUCCESS('✅ Новий суперюзер створено:'))
                self.stdout.write(f'   👤 Username: {user.username}')
                self.stdout.write(f'   📧 Email: {user.email}')
                self.stdout.write(f'   🔑 Password: {new_password}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Помилка: {e}'))
                return
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write('🌐 Django Admin URL:')
        self.stdout.write('   https://beautyshop-django.onrender.com/admin/')
        self.stdout.write('='*70)
        self.stdout.write(self.style.SUCCESS('⚠️  ВИКОРИСТАЙТЕ ЦІ ДАНІ ДЛЯ ВХОДУ!'))
        self.stdout.write('='*70 + '\n')

