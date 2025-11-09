"""
Management команда для автоматичного оновлення статусу акцій
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.promotions.models import Promotion
from apps.products.models import Product


class Command(BaseCommand):
    help = 'Оновлює статус акцій: знімає закінчені, активує нові'
    
    def handle(self, *args, **options):
        now = timezone.now()
        
        removed_count = 0
        activated_count = 0
        
        # Знаходимо всі товари з закінченими акціями
        expired_products = Product.objects.filter(
            is_sale=True,
            sale_end_date__lt=now
        )
        
        for product in expired_products:
            product.is_sale = False
            product.sale_price = None
            product.sale_start_date = None
            product.sale_end_date = None
            product.active_promotion_name = ''
            product.save()
            removed_count += 1
        
        # Знаходимо активні акції які ще не застосовані
        active_promotions = Promotion.objects.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        
        for promotion in active_promotions:
            count = promotion.apply_to_products()
            activated_count += count
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Оновлено: знято {removed_count} закінчених акцій, '
                f'застосовано {activated_count} активних акцій'
            )
        )

