"""
Масове завантаження зображень з оптимізацією для всіх товарів
"""
import requests
import time
from django.core.management.base import BaseCommand
from apps.products.models import Product, ProductImage, Category
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from collections import defaultdict


class Command(BaseCommand):
    help = 'Масове завантаження зображень для всіх товарів без фото'
    
    def __init__(self):
        super().__init__()
        self.old_site_url = 'https://beautyshop-ukrane.com.ua'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.category_map = {
            'nigti': 'nigti',
            'volossia': 'volossia',
            'brovy-ta-vii': 'brovi-ta-viji',
            'depilacia': 'depilyaciya-shugaring',
            'kosmetyka': 'kosmetika-dlya-osobi-ta-tila',
            'makiiazh': 'makiyazh',
            'odnorazova-produkcia': 'odnorazova-produkciya',
            'dezinfekcia': 'dezinfekciya-ta-sterilizaciya',
            'mebli': 'mebli-dlya-saloniv',
        }
        
        # Кеш для скраплених товарів
        self.catalog_cache = defaultdict(list)
    
    def add_arguments(self, parser):
        parser.add_argument('--pages', type=int, default=20, help='Кількість сторінок для скрапінгу')
        parser.add_argument('--delay', type=float, default=0.3, help='Затримка між запитами')
    
    def normalize_name(self, name):
        return re.sub(r'[^a-zа-яіїє0-9]', '', name.lower())
    
    def scrape_full_catalog(self, category_url, max_pages):
        """Скрапить всі сторінки каталогу"""
        all_products = []
        
        for page in range(1, max_pages + 1):
            try:
                url = f"{category_url}?page={page}" if page > 1 else category_url
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    break
                
                soup = BeautifulSoup(response.content, 'html.parser')
                product_blocks = soup.find_all('div', class_='product-thumb')
                
                if not product_blocks:
                    break
                
                for block in product_blocks:
                    try:
                        links = block.find_all('a', href=True)
                        for link in links:
                            text = link.get_text(strip=True)
                            href = link['href']
                            if text and '/' in href and len(href.split('/')) > 4:
                                img = block.find('img')
                                if not img:
                                    continue
                                
                                img_url = img.get('src') or img.get('data-src')
                                if not img_url:
                                    continue
                                
                                if not img_url.startswith('http'):
                                    img_url = urljoin(self.old_site_url, img_url)
                                
                                all_products.append({
                                    'name': text,
                                    'image': img_url,
                                    'normalized_name': self.normalize_name(text)
                                })
                                break
                    except:
                        continue
                
                self.stdout.write(f'    Сторінка {page}: {len(product_blocks)} товарів')
                time.sleep(0.3)
                
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'    Помилка сторінки {page}: {e}'))
                break
        
        return all_products
    
    def match_product(self, product, catalog_products):
        """Шукає співпадіння товару в каталозі"""
        normalized_name = self.normalize_name(product.name)
        
        # Спочатку точне співпадіння
        for cat_prod in catalog_products:
            if normalized_name == cat_prod['normalized_name']:
                return cat_prod
        
        # Потім часткове співпадіння (довга назва містить коротку)
        for cat_prod in catalog_products:
            if len(normalized_name) > 10:  # тільки для довгих назв
                if normalized_name in cat_prod['normalized_name'] or cat_prod['normalized_name'] in normalized_name:
                    # Перевірка що не занадто різні
                    len_diff = abs(len(normalized_name) - len(cat_prod['normalized_name']))
                    if len_diff < len(normalized_name) * 0.5:  # різниця менше 50%
                        return cat_prod
        
        return None
    
    def handle(self, *args, **options):
        max_pages = options['pages']
        delay = options['delay']
        
        self.stdout.write(self.style.SUCCESS('\n=== МАСОВЕ ЗАВАНТАЖЕННЯ ЗОБРАЖЕНЬ ===\n'))
        
        total_processed = 0
        total_success = 0
        total_skipped = 0
        
        categories = Category.objects.filter(is_active=True, parent__isnull=True).order_by('name')
        
        for category in categories:
            old_site_category = self.category_map.get(category.slug)
            if not old_site_category:
                continue
            
            self.stdout.write(self.style.SUCCESS(f'\n▶ {category.name}'))
            
            # Отримуємо товари без фото з цієї категорії
            subcategories = category.children.filter(is_active=True)
            category_ids = [category.id] + list(subcategories.values_list('id', flat=True))
            
            products_without_images = Product.objects.filter(
                category_id__in=category_ids,
                is_active=True,
                images__isnull=True
            ).distinct()
            
            if not products_without_images:
                self.stdout.write('  ✓ Всі товари мають зображення')
                continue
            
            count = products_without_images.count()
            self.stdout.write(f'  Товарів без фото: {count}')
            
            # Скрапимо каталог
            catalog_url = f"{self.old_site_url}/{old_site_category}"
            self.stdout.write(f'  Скрапінг каталогу (до {max_pages} сторінок)...')
            
            catalog_products = self.scrape_full_catalog(catalog_url, max_pages)
            self.stdout.write(f'  Знайдено в каталозі: {len(catalog_products)} товарів')
            
            if not catalog_products:
                self.stdout.write(self.style.WARNING('  ⚠ Каталог порожній, пропускаємо'))
                continue
            
            # Співставляємо і завантажуємо
            category_success = 0
            for product in products_without_images:
                total_processed += 1
                
                matched = self.match_product(product, catalog_products)
                
                if not matched:
                    total_skipped += 1
                    continue
                
                try:
                    img_obj = ProductImage(
                        product=product,
                        image=matched['image'],
                        alt_text=product.name,
                        is_main=True,
                        sort_order=0
                    )
                    img_obj.save(skip_optimization=True)
                    total_success += 1
                    category_success += 1
                    
                    if category_success <= 3:  # Показуємо перші 3
                        self.stdout.write(f'  ✓ {product.name[:50]}...')
                    
                    time.sleep(delay)
                    
                except Exception as e:
                    self.stdout.write(f'  ✗ Помилка: {product.name[:40]}... - {e}')
            
            if category_success > 3:
                self.stdout.write(f'  ✓ ... і ще {category_success - 3} товарів')
            
            self.stdout.write(f'  Підсумок категорії: {category_success} успішно')
        
        # Фінальний звіт
        self.stdout.write(self.style.SUCCESS(f'\n\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('ФІНАЛЬНИЙ ЗВІТ'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}'))
        self.stdout.write(f'Оброблено: {total_processed}')
        self.stdout.write(self.style.SUCCESS(f'Успішно: {total_success}'))
        self.stdout.write(self.style.WARNING(f'Пропущено (не знайдено): {total_skipped}'))
        
        if total_processed > 0:
            success_rate = (total_success / total_processed) * 100
            self.stdout.write(f'\nУспішність: {success_rate:.1f}%')

