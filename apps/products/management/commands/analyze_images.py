"""
Команда для аналізу статистики зображень товарів
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from apps.products.models import Product, ProductImage, Category


class Command(BaseCommand):
    help = 'Показує статистику зображень товарів'
    
    def handle(self, *args, **options):
        # Загальна статистика
        total_products = Product.objects.filter(is_active=True).count()
        products_with_images = Product.objects.filter(is_active=True, images__isnull=False).distinct().count()
        products_without_images = Product.objects.filter(is_active=True, images__isnull=True).distinct().count()
        
        self.stdout.write(self.style.SUCCESS('\n=== ЗАГАЛЬНА СТАТИСТИКА ==='))
        self.stdout.write(f'Всього активних товарів: {total_products}')
        self.stdout.write(self.style.SUCCESS(f'Товарів з фото: {products_with_images} ({products_with_images/total_products*100:.1f}%)'))
        self.stdout.write(self.style.ERROR(f'Товарів без фото: {products_without_images} ({products_without_images/total_products*100:.1f}%)'))
        
        # Статистика по категоріях
        self.stdout.write(self.style.SUCCESS('\n=== СТАТИСТИКА ПО КАТЕГОРІЯХ ==='))
        categories = Category.objects.filter(is_active=True, parent__isnull=True)
        
        for category in categories:
            # Отримуємо всі підкатегорії
            subcategories = category.children.filter(is_active=True)
            category_ids = [category.id] + list(subcategories.values_list('id', flat=True))
            
            total_in_cat = Product.objects.filter(category_id__in=category_ids, is_active=True).count()
            with_images = Product.objects.filter(
                category_id__in=category_ids, 
                is_active=True, 
                images__isnull=False
            ).distinct().count()
            without_images = Product.objects.filter(
                category_id__in=category_ids,
                is_active=True,
                images__isnull=True
            ).distinct().count()
            
            if total_in_cat > 0:
                percentage = (without_images / total_in_cat) * 100
                status = '✓' if without_images == 0 else '⚠' if percentage < 20 else '✗'
                
                self.stdout.write(f'\n{status} {category.name}')
                self.stdout.write(f'  Всього: {total_in_cat} | З фото: {with_images} | Без фото: {without_images} ({percentage:.1f}%)')
        
        # Топ товарів без фото (перші 10)
        self.stdout.write(self.style.SUCCESS('\n=== ТОП ТОВАРІВ БЕЗ ФОТО ==='))
        products_no_images = Product.objects.filter(
            is_active=True,
            images__isnull=True
        ).select_related('category')[:10]
        
        for idx, product in enumerate(products_no_images, 1):
            self.stdout.write(f'{idx}. [{product.sku}] {product.name} ({product.category.name})')
        
        # Статистика по кількості зображень
        self.stdout.write(self.style.SUCCESS('\n=== КІЛЬКІСТЬ ЗОБРАЖЕНЬ НА ТОВАР ==='))
        
        products_with_stats = Product.objects.filter(is_active=True).annotate(
            images_count=Count('images')
        ).values('images_count').annotate(count=Count('id')).order_by('images_count')
        
        for stat in products_with_stats:
            images_count = stat['images_count']
            products_count = stat['count']
            label = 'без фото' if images_count == 0 else f'{images_count} фото'
            self.stdout.write(f'{label}: {products_count} товарів')
        
        self.stdout.write('\n')

