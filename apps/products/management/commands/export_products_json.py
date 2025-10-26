"""
Експорт товарів в JSON після локального імпорту з Cloudinary
Використовується для швидкого імпорту на Render без завантаження зображень
"""
from django.core.management.base import BaseCommand
from apps.products.models import Product, ProductImage, ProductAttribute, Category
import json
import os


class Command(BaseCommand):
    help = 'Експортує товари в JSON (зображення вже на Cloudinary)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='products_data',
            help='Назва папки для експорту'
        )

    def handle(self, *args, **options):
        output_dir = options['output']
        
        # Створюємо папку якщо не існує
        os.makedirs(output_dir, exist_ok=True)
        
        self.stdout.write('📦 Експорт товарів...')
        
        # Експортуємо товари
        products_data = []
        for product in Product.objects.select_related('category').prefetch_related('images', 'attributes'):
            product_dict = {
                'name': product.name,
                'slug': product.slug,
                'category_slug': product.category.slug,
                'description': product.description,
                'retail_price': str(product.retail_price),
                'wholesale_price': str(product.wholesale_price) if product.wholesale_price else None,
                'sale_price': str(product.sale_price) if product.sale_price else None,
                'price_3_qty': str(product.price_3_qty) if product.price_3_qty else None,
                'price_5_qty': str(product.price_5_qty) if product.price_5_qty else None,
                'is_sale': product.is_sale,
                'is_top': product.is_top,
                'is_new': product.is_new,
                'is_featured': product.is_featured,
                'stock': product.stock,
                'is_active': product.is_active,
                'sku': product.sku,
                'images': [
                    {
                        'path': img.image.name,  # Шлях в storage (Cloudinary)
                        'url': img.image.url,  # Повний URL
                        'is_main': img.is_main,
                        'sort_order': img.sort_order,
                        'alt_text': img.alt_text
                    }
                    for img in product.images.all()
                ],
                'attributes': [
                    {
                        'name': attr.name,
                        'value': attr.value,
                        'sort_order': attr.sort_order
                    }
                    for attr in product.attributes.all()
                ]
            }
            products_data.append(product_dict)
        
        # Зберігаємо в JSON файли по 500 товарів
        batch_size = 500
        for i in range(0, len(products_data), batch_size):
            batch = products_data[i:i+batch_size]
            filename = f'{output_dir}/products_{i//batch_size + 1}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(batch, f, ensure_ascii=False, indent=2)
            self.stdout.write(f'  ✓ {filename} ({len(batch)} товарів)')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Експортовано {len(products_data)} товарів'))
        self.stdout.write(f'📂 Файли в папці: {output_dir}/')

