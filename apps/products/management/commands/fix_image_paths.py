from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Виправляє шляхи зображень (видаляє зайвий media/ префікс)'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM products_productimage WHERE image LIKE 'media/%'")
            total = cursor.fetchone()[0]
            
            self.stdout.write(f'Знайдено {total} зображень з media/ префіксом')
            
            cursor.execute("UPDATE products_productimage SET image = REPLACE(image, 'media/', '') WHERE image LIKE 'media/%'")
            updated = cursor.rowcount
        
        self.stdout.write(self.style.SUCCESS(f'✅ Оновлено {updated} зображень'))

