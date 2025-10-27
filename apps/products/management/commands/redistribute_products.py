from django.core.management.base import BaseCommand
from apps.products.models import Product, Category

class Command(BaseCommand):
    help = 'Розподіляє товари з Імпорт категорії по правильним категоріям'

    def handle(self, *args, **options):
        import_cat = Category.objects.filter(slug='import-webosova').first()
        if not import_cat:
            self.stdout.write('Категорія import-webosova не знайдена')
            return

        products = Product.objects.filter(category=import_cat)
        total = products.count()
        
        self.stdout.write(f'Знайдено {total} товарів в категорії Імпорт')
        
        category_map = self._get_category_map()
        updated = 0
        
        for product in products:
            new_cat = self._detect_category(product, category_map)
            if new_cat and new_cat != import_cat:
                product.category = new_cat
                product.save(update_fields=['category'])
                updated += 1
                
                if updated % 100 == 0:
                    self.stdout.write(f'Оновлено {updated}/{total}')
        
        self.stdout.write(self.style.SUCCESS(f'✅ Розподілено {updated} товарів'))
        
        if products.count() == 0:
            import_cat.delete()
            self.stdout.write(self.style.SUCCESS('✅ Категорію Імпорт видалено'))
    
    def _get_category_map(self):
        return {
            'nigti': ['nigti', 'nogti', 'nails', 'gel-lak', 'baza', 'top'],
            'volossia': ['volosya', 'volossya', 'hair', 'shampun', 'maska'],
            'brovy-ta-vii': ['brovi', 'brows', 'vii', 'resnicy'],
            'depilyatsiya': ['depilyaciya', 'depilacia', 'shugaring', 'vosk', 'pasta'],
            'kosmetyka': ['kosmetika', 'krem', 'serum'],
            'makiyazh': ['makeup', 'pomada', 'tush'],
            'odnorazova-produktsia': ['odnorazova', 'disposable', 'rukavychky', 'masochky'],
            'dezinfektsiya-ta-sterylizatsiya': ['dezinfekciya', 'sterilizaciya', 'antiseptyk'],
            'mebli-dlya-saloniv': ['mebli', 'furniture', 'kreslo', 'kushetka'],
        }
    
    def _detect_category(self, product, category_map):
        slug_lower = product.slug.lower()
        name_lower = product.name.lower()
        
        for cat_slug, keywords in category_map.items():
            for keyword in keywords:
                if keyword in slug_lower or keyword in name_lower:
                    cat = Category.objects.filter(slug=cat_slug).first()
                    if cat:
                        return cat
        
        return None

