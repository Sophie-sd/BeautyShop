from django.core.management.base import BaseCommand
from apps.orders.models import EmailSubscriber, Order, Newsletter
from django.contrib.auth import get_user_model


User = get_user_model()


class Command(BaseCommand):
    help = 'Синхронізація існуючих email адрес в систему розсилки'
    
    def handle(self, *args, **options):
        self.stdout.write('Початок синхронізації email адрес...\n')
        
        synced_count = 0
        
        self.stdout.write('1. Синхронізація зареєстрованих користувачів (тільки верифікованих оптових)...')
        for user in User.objects.filter(
            email__isnull=False, 
            is_staff=False, 
            is_superuser=False,
            is_wholesale=True,
            email_verified=True
        ).exclude(email=''):
            EmailSubscriber.add_subscriber(
                email=user.email,
                source='registered',
                name=f"{user.first_name} {user.last_name}" if user.first_name else user.username,
                is_wholesale=True
            )
            synced_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Синхронізовано {synced_count} оптових користувачів'))
        
        self.stdout.write('\n2. Синхронізація замовлень без реєстрації...')
        order_emails = Order.objects.filter(
            user__isnull=True,
            email__isnull=False
        ).exclude(email='').values_list('email', 'first_name', 'last_name').distinct()
        
        order_count = 0
        for email, first_name, last_name in order_emails:
            name = f"{first_name} {last_name}".strip()
            EmailSubscriber.add_subscriber(
                email=email,
                source='order',
                name=name,
                is_wholesale=False
            )
            order_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Синхронізовано {order_count} клієнтів з замовлень'))
        
        self.stdout.write('\n3. Синхронізація підписників розсилки...')
        newsletter_count = 0
        for newsletter in Newsletter.objects.filter(is_active=True):
            EmailSubscriber.add_subscriber(
                email=newsletter.email,
                source='newsletter',
                is_wholesale=False
            )
            newsletter_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'  ✓ Синхронізовано {newsletter_count} підписників'))
        
        total_subscribers = EmailSubscriber.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Синхронізацію завершено! Всього email адрес в системі: {total_subscribers}'
            )
        )

