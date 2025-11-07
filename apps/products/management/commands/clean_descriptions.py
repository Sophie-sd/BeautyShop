"""
Management команда для очищення описів товарів від слова "Опис" на початку
"""
from django.core.management.base import BaseCommand
from apps.products.models import Product


class Command(BaseCommand):
    help = 'Видаляє слово "Опис" з початку описів товарів'
    
    def handle(self, *args, **options):
        products = Product.objects.exclude(description='')
        updated_count = 0
        
        for product in products:
            original_description = product.description
            
            # Видаляємо "Опис" з початку (різні варіанти)
            cleaned_description = original_description
            
            # Варіанти які треба видалити
            prefixes_to_remove = [
                'Опис',
                'опис',
                'ОПИС',
                'Опис:',
                'опис:',
                'ОПИС:',
            ]
            
            for prefix in prefixes_to_remove:
                if cleaned_description.startswith(prefix):
                    cleaned_description = cleaned_description[len(prefix):].strip()
                    break
            
            # Якщо щось змінилося - зберігаємо
            if cleaned_description != original_description:
                product.description = cleaned_description
                product.save(update_fields=['description'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Очищено опис для товару: {product.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nОновлено {updated_count} товарів')
        )

