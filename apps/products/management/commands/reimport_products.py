"""
Повний реімпорт товарів з очищенням і правильним збереженням Cloudinary URLs
"""
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from apps.products.models import Product, ProductImage, ProductAttribute, Category
from decimal import Decimal
import json
import os
import glob


class Command(BaseCommand):
    help = 'Повний реімпорт товарів з Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=str,
            default='products_data',
            help='Папка з JSON файлами'
        )

    def handle(self, *args, **options):
        input_dir = options['input']
        
        self.stdout.write('🔄 ПОВНИЙ РЕІМПОРТ ТОВАРІВ')
        self.stdout.write('=' * 50)
        
        # Крок 1: Видаляємо всі старі товари
        old_count = Product.objects.count()
        self.stdout.write(f'\n🗑️  Видалення {old_count} старих товарів...')
        Product.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('✅ Товари видалено'))
        
        # Крок 2: Перевіряємо наявність JSON файлів
        if not os.path.exists(input_dir):
            self.stdout.write(self.style.ERROR(f'❌ Папка {input_dir} не знайдена'))
            return
        
        json_files = sorted(glob.glob(f'{input_dir}/products_*.json'))
        if not json_files:
            self.stdout.write(self.style.ERROR(f'❌ JSON файли не знайдені'))
            return
        
        self.stdout.write(f'\n📦 Знайдено {len(json_files)} JSON файлів')
        
        # Крок 3: Кешуємо категорії
        categories_cache = {cat.slug: cat for cat in Category.objects.all()}
        self.stdout.write(f'📂 Завантажено {len(categories_cache)} категорій')
        
        # Крок 4: Імпортуємо товари
        total_imported = 0
        total_images = 0
        
        for json_file in json_files:
            filename = os.path.basename(json_file)
            self.stdout.write(f'\n📄 Обробка {filename}...')
            
            with open(json_file, 'r', encoding='utf-8') as f:
                products_data = json.load(f)
            
            for product_data in products_data:
                try:
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
                    
                    # Додаємо зображення через bulk_create щоб обійти save() з оптимізацією
                    images_to_create = []
                    for img_data in product_data.get('images', []):
                        path = img_data.get('path', '')
                        if path:
                            img = ProductImage(
                                product=product,
                                is_main=img_data.get('is_main', False),
                                sort_order=img_data.get('sort_order', 0),
                                alt_text=img_data.get('alt_text', '') or product.name
                            )
                            # Встановлюємо path напряму - bulk_create НЕ викликає save()
                            img.image.name = path
                            images_to_create.append(img)
                    
                    # Зберігаємо всі зображення одним запитом БЕЗ виклику save()
                    if images_to_create:
                        ProductImage.objects.bulk_create(images_to_create)
                        total_images += len(images_to_create)
                    
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
        
        # Фінальна статистика
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('✅ РЕІМПОРТ ЗАВЕРШЕНО!'))
        self.stdout.write(f'\n📊 Статистика:')
        self.stdout.write(f'  • Імпортовано товарів: {total_imported}')
        self.stdout.write(f'  • Додано зображень: {total_images}')
        self.stdout.write(f'  • Середньо зображень на товар: {total_images/total_imported if total_imported > 0 else 0:.1f}')
        
        # Перевірка першого товару
        first_product = Product.objects.first()
        if first_product and first_product.images.exists():
            first_img = first_product.images.first()
            self.stdout.write(f'\n🔍 Перевірка:')
            self.stdout.write(f'  Товар: {first_product.name}')
            self.stdout.write(f'  Зображень: {first_product.images.count()}')
            self.stdout.write(f'  URL: {first_img.image.url}')

