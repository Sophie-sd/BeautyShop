"""
Django команда для встановлення градації цін та оптових цін
Використання: python manage.py set_prices [--all]
"""
from django.core.management.base import BaseCommand
from apps.products.models import Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Встановлює градацію цін та оптові ціни для товарів'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Встановити ціни для ВСІХ товарів (за замовчуванням - перші 100)',
        )

    def handle(self, *args, **options):
        self.stdout.write('Встановлення градації цін...\n')
        
        products = Product.objects.filter(is_active=True)
        
        if not options['all']:
            products = products[:100]
            self.stdout.write(f'Режим: перші 100 товарів (використайте --all для всіх)\n')
        else:
            self.stdout.write(f'Режим: ВСІ товари ({products.count()} шт)\n')
        
        updated_count = 0
        
        for product in products:
            retail = product.retail_price
            
            # Градація: -5% від 3шт, -10% від 5шт
            product.price_3_qty = retail * Decimal('0.95')
            product.price_5_qty = retail * Decimal('0.90')
            
            # Оптова ціна: -15%
            product.wholesale_price = retail * Decimal('0.85')
            
            product.save(update_fields=['price_3_qty', 'price_5_qty', 'wholesale_price'])
            updated_count += 1
            
            if updated_count % 50 == 0:
                self.stdout.write(f'  Оброблено {updated_count} товарів...')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Готово! Встановлено ціни для {updated_count} товарів')
        )
        self.stdout.write('\nТепер на сайті відображаються:')
        self.stdout.write('  • Градація цін (від 3шт -5%, від 5шт -10%)')
        self.stdout.write('  • Оптові ціни для залогінених (-15%)')

