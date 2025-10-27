"""
Імпорт товарів з JSON на Render (зображення вже на Cloudinary)
Швидкий імпорт без завантаження зображень - економить пам'ять
"""
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from apps.products.models import Product, ProductImage, ProductAttribute, Category
from decimal import Decimal
import json
import os
import glob


class Command(BaseCommand):
    help = 'Імпортує товари з JSON (зображення вже на Cloudinary)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=str,
            default='products_data',
            help='Папка з JSON файлами'
        )

    def handle(self, *args, **options):
        input_dir = options['input']
        
        if not os.path.exists(input_dir):
            self.stdout.write(self.style.ERROR(f'❌ Папка {input_dir} не знайдена'))
            return
        
        self.stdout.write('📦 Імпорт товарів з JSON...')
        
        # Кешуємо категорії
        categories_cache = {cat.slug: cat for cat in Category.objects.all()}
        
        # Знаходимо всі JSON файли
        json_files = sorted(glob.glob(f'{input_dir}/products_*.json'))
        
        if not json_files:
            self.stdout.write(self.style.ERROR(f'❌ JSON файли не знайдені в {input_dir}'))
            return
        
        total_imported = 0
        total_skipped = 0
        
        for json_file in json_files:
            self.stdout.write(f'\n📄 Обробка {os.path.basename(json_file)}...')
            
            with open(json_file, 'r', encoding='utf-8') as f:
                products_data = json.load(f)
            
            for product_data in products_data:
                try:
                    # Перевіряємо чи товар вже існує
                    if Product.objects.filter(slug=product_data['slug']).exists():
                        total_skipped += 1
                        continue
                    
                    # Отримуємо категорію
                    category = categories_cache.get(product_data['category_slug'])
                    if not category:
                        continue
                    
                    # Створюємо товар
                    product = Product.objects.create(
                        name=product_data['name'],
                        slug=product_data['slug'],
                        category=category,
                        description=product_data.get('description', ''),
                        retail_price=Decimal(product_data['retail_price']),
                        wholesale_price=Decimal(product_data['wholesale_price']) if product_data.get('wholesale_price') else None,
                        sale_price=Decimal(product_data['sale_price']) if product_data.get('sale_price') else None,
                        price_3_qty=Decimal(product_data['price_3_qty']) if product_data.get('price_3_qty') else None,
                        price_5_qty=Decimal(product_data['price_5_qty']) if product_data.get('price_5_qty') else None,
                        is_sale=product_data.get('is_sale', False),
                        is_top=product_data.get('is_top', False),
                        is_new=product_data.get('is_new', False),
                        is_featured=product_data.get('is_featured', False),
                        stock=product_data.get('stock', 100),
                        is_active=product_data.get('is_active', True),
                        sku=product_data.get('sku', '')
                    )
                    
                    # Додаємо зображення (вже на Cloudinary, просто посилання)
                    for img_data in product_data.get('images', []):
                        # Створюємо ProductImage та зберігаємо path з Cloudinary
                        path = img_data.get('path', '')
                        if path:
                            img = ProductImage(
                                product=product,
                                is_main=img_data.get('is_main', False),
                                sort_order=img_data.get('sort_order', 0),
                                alt_text=img_data.get('alt_text', '')
                            )
                            # Зберігаємо path - Cloudinary storage автоматично згенерує URL
                            img.image = path
                            img.save()
                    
                    # Додаємо характеристики
                    for attr_data in product_data.get('attributes', []):
                        ProductAttribute.objects.create(
                            product=product,
                            name=attr_data['name'],
                            value=attr_data['value'],
                            sort_order=attr_data.get('sort_order', 0)
                        )
                    
                    total_imported += 1
                    
                    if total_imported % 100 == 0:
                        self.stdout.write(f'  ✓ {total_imported} товарів імпортовано')
                
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Помилка: {str(e)}'))
                    continue
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Імпорт завершено!'))
        self.stdout.write(f'  • Імпортовано: {total_imported} товарів')
        self.stdout.write(f'  • Пропущено: {total_skipped} (дублікати)')

