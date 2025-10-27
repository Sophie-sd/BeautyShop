"""
Імпорт товарів з JSON та завантаження локальних зображень на Cloudinary
"""
import json
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files import File
from apps.products.models import Product, ProductImage, Category
from decimal import Decimal


class Command(BaseCommand):
    help = 'Імпортує товари з JSON та завантажує зображення на Cloudinary'
    
    def __init__(self):
        super().__init__()
        self.stats = {
            'products': 0,
            'images': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=str,
            default='products_data',
            help='Папка з JSON файлами'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Видалити всі товари перед імпортом'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Максимальна кількість товарів'
        )
    
    def handle(self, *args, **options):
        input_dir = options['input']
        clear = options['clear']
        limit = options.get('limit')
        
        self.stdout.write(self.style.SUCCESS('🚀 Імпорт товарів з JSON на Cloudinary'))
        
        # Перевірка Cloudinary
        if 'cloudinary' not in str(settings.DEFAULT_FILE_STORAGE).lower():
            self.stdout.write(self.style.ERROR('❌ Cloudinary не налаштований!'))
            self.stdout.write(f'DEFAULT_FILE_STORAGE: {settings.DEFAULT_FILE_STORAGE}')
            return
        
        self.stdout.write(self.style.SUCCESS('✅ Cloudinary налаштований'))
        
        # Очищення бази
        if clear:
            self.stdout.write('🗑️  Видалення існуючих товарів...')
            Product.objects.all().delete()
            self.stdout.write('✅ База очищена')
        
        # Пошук JSON файлів
        json_files = sorted(Path(input_dir).glob('*.json'))
        
        if not json_files:
            self.stdout.write(self.style.ERROR(f'❌ Не знайдено JSON файлів в {input_dir}'))
            return
        
        self.stdout.write(f'📂 Знайдено {len(json_files)} JSON файлів\n')
        
        total_products = 0
        
        # Обробка кожного JSON файлу
        for json_file in json_files:
            self.stdout.write(f'📦 Обробка {json_file.name}...')
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    products_data = json.load(f)
                
                for product_data in products_data:
                    if limit and total_products >= limit:
                        break
                    
                    self.import_product(product_data)
                    total_products += 1
                    
                    if total_products % 100 == 0:
                        self.stdout.write(
                            f'  ✓ {total_products} товарів, '
                            f'{self.stats["images"]} зображень на Cloudinary'
                        )
                
                if limit and total_products >= limit:
                    break
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Помилка файлу {json_file.name}: {e}'))
                continue
        
        # Фінальна статистика
        self.stdout.write(self.style.SUCCESS(f'\n✅ Імпорт завершено!'))
        self.stdout.write(f'📊 Статистика:')
        self.stdout.write(f'  • Товарів імпортовано: {self.stats["products"]}')
        self.stdout.write(f'  • Зображень на Cloudinary: {self.stats["images"]}')
        self.stdout.write(f'  • Пропущено: {self.stats["skipped"]}')
        if self.stats['errors'] > 0:
            self.stdout.write(self.style.WARNING(f'  • Помилок: {self.stats["errors"]}'))
    
    def import_product(self, product_data):
        """Імпортує один товар з завантаженням зображень на Cloudinary"""
        try:
            # Перевірка дубліката
            if Product.objects.filter(slug=product_data['slug']).exists():
                self.stats['skipped'] += 1
                return
            
            # Категорія
            category_slug = product_data.get('category_slug', 'import-webosova')
            category = Category.objects.filter(slug=category_slug).first()
            
            if not category:
                category = Category.objects.filter(slug='import-webosova').first()
            
            if not category:
                category = Category.objects.create(
                    name='Імпорт',
                    slug='import-webosova',
                    is_active=True
                )
            
            # Створення товару
            product = Product.objects.create(
                name=product_data['name'][:200],
                slug=product_data['slug'],
                category=category,
                description=product_data.get('description', '')[:2000],
                retail_price=Decimal(product_data['retail_price']) if product_data['retail_price'] else Decimal('0'),
                is_active=product_data.get('is_active', True),
                stock=product_data.get('stock', 100),
                is_new=product_data.get('is_new', False),
                is_top=product_data.get('is_top', False),
                is_sale=product_data.get('is_sale', False),
                is_featured=product_data.get('is_featured', False),
            )
            
            # Завантаження зображень на Cloudinary
            for img_data in product_data.get('images', []):
                if self.upload_image_to_cloudinary(product, img_data):
                    self.stats['images'] += 1
            
            self.stats['products'] += 1
            
        except Exception as e:
            self.stats['errors'] += 1
            self.stdout.write(self.style.WARNING(f'⚠️  Помилка товару {product_data.get("name", "")[:50]}: {e}'))
    
    def upload_image_to_cloudinary(self, product, img_data):
        """Завантажує локальне зображення на Cloudinary"""
        try:
            path = img_data.get('path', '')
            if not path:
                self.stdout.write(f'    ⚠️  Немає path для зображення')
                return False
            
            # Повний шлях до локального файлу
            local_path = os.path.join(settings.MEDIA_ROOT, path)
            
            if not os.path.exists(local_path):
                self.stdout.write(f'    ⚠️  Файл не знайдено: {local_path}')
                return False
            
            # Створюємо ProductImage і зберігаємо на Cloudinary
            product_image = ProductImage(
                product=product,
                is_main=img_data.get('is_main', False),
                sort_order=img_data.get('sort_order', 0),
                alt_text=img_data.get('alt_text', '') or product.name
            )
            
            # Відкриваємо локальний файл і зберігаємо на Cloudinary БЕЗ оптимізації
            with open(local_path, 'rb') as f:
                # skip_optimization=True щоб не запускати PIL оптимізацію
                product_image.image.save(
                    os.path.basename(path),
                    File(f),
                    save=False
                )
                product_image.save(skip_optimization=True)
            
            self.stdout.write(f'    ✓ Завантажено: {os.path.basename(path)}')
            return True
            
        except Exception as e:
            self.stdout.write(f'    ❌ Помилка завантаження: {e}')
            import traceback
            traceback.print_exc()
            return False

