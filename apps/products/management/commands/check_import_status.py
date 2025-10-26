"""
Перевірка статусу імпорту товарів
"""
from django.core.management.base import BaseCommand
from apps.products.models import Product, ProductImage, Category


class Command(BaseCommand):
    help = 'Перевірка статусу імпорту'

    def handle(self, *args, **options):
        total_products = Product.objects.count()
        with_images = Product.objects.filter(images__isnull=False).distinct().count()
        categories = Category.objects.count()
        total_images = ProductImage.objects.count()
        
        import_category = Category.objects.filter(slug='import-webosova').first()
        if import_category:
            imported = Product.objects.filter(category=import_category).count()
        else:
            imported = 0
        
        self.stdout.write(self.style.SUCCESS('\n📊 Статус імпорту:\n'))
        self.stdout.write(f'  • Всього товарів: {total_products}')
        self.stdout.write(f'  • Імпортовано з Webosova: {imported}')
        self.stdout.write(f'  • Товарів з зображеннями: {with_images}')
        self.stdout.write(f'  • Всього зображень: {total_images}')
        self.stdout.write(f'  • Категорій: {categories}\n')
        
        if imported > 0:
            progress = (imported / 2267) * 100
            self.stdout.write(f'  📈 Прогрес: {progress:.1f}% (з 2267 товарів)\n')
        
        # Останні імпортовані товари
        recent = Product.objects.order_by('-created_at')[:5]
        if recent:
            self.stdout.write('  🆕 Останні товари:')
            for p in recent:
                img_count = p.images.count()
                self.stdout.write(f'     • {p.name[:60]} (зобр: {img_count})')

