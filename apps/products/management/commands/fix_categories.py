from django.core.management.base import BaseCommand
from apps.products.models import Product, Category

class Command(BaseCommand):
    help = 'Видаляє категорію import-webosova та всі товари в ній'

    def handle(self, *args, **options):
        import_category = Category.objects.filter(slug='import-webosova').first()
        
        if not import_category:
            self.stdout.write('Категорія import-webosova не знайдена')
            return
        
        products_count = Product.objects.filter(category=import_category).count()
        
        self.stdout.write(f'Видалення {products_count} товарів з категорії import-webosova')
        
        Product.objects.filter(category=import_category).delete()
        import_category.delete()
        
        self.stdout.write(self.style.SUCCESS('✅ Категорію та товари видалено'))

