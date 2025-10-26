"""
Швидкий імпорт товарів через sitemap.xml
Використання: python manage.py import_products_sitemap
"""
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.text import slugify
from apps.products.models import Category, Product, ProductImage, ProductAttribute
from decimal import Decimal
import time
import re
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed


class Command(BaseCommand):
    help = 'Швидкий імпорт товарів через sitemap.xml'

    def __init__(self):
        super().__init__()
        self.base_url = 'https://beautyshop-ukrane.com.ua'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.stats = {
            'products': 0,
            'images': 0,
            'errors': 0,
            'skipped': 0
        }
        self.default_category = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Максимальна кількість товарів'
        )
        parser.add_argument(
            '--skip-images',
            action='store_true',
            help='Пропустити завантаження зображень'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=5,
            help='Кількість паралельних потоків (default: 5)'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        skip_images = options.get('skip_images', False)
        workers = options.get('workers', 5)
        
        self.stdout.write(self.style.SUCCESS('🚀 Імпорт товарів через Sitemap'))
        
        # Створюємо категорію за замовчуванням
        self.default_category, _ = Category.objects.get_or_create(
            slug='import-webosova',
            defaults={'name': 'Імпорт з Webosova', 'is_active': True}
        )
        
        try:
            # Отримуємо список всіх URL товарів з sitemap
            product_urls = self.get_product_urls_from_sitemap()
            
            if not product_urls:
                self.stdout.write(self.style.ERROR('❌ Не знайдено товарів у sitemap'))
                return
            
            if limit:
                product_urls = product_urls[:limit]
            
            self.stdout.write(f'📦 Знайдено товарів: {len(product_urls)}')
            self.stdout.write(f'⚙️  Потоків: {workers}\n')
            
            # Імпортуємо товари паралельно
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self.import_product, url, skip_images): url 
                    for url in product_urls
                }
                
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        result = future.result()
                        if result:
                            self.stats['products'] += 1
                            if self.stats['products'] % 50 == 0:
                                self.stdout.write(f'  ✓ Імпортовано: {self.stats["products"]}')
                    except Exception as e:
                        self.stats['errors'] += 1
                        self.stdout.write(self.style.WARNING(f'  ⚠ Помилка {url}: {str(e)[:50]}'))
            
            # Статистика
            self.stdout.write(self.style.SUCCESS(f'\n✅ Імпорт завершено!'))
            self.stdout.write(f'📊 Статистика:')
            self.stdout.write(f'  • Товарів імпортовано: {self.stats["products"]}')
            self.stdout.write(f'  • Зображень: {self.stats["images"]}')
            self.stdout.write(f'  • Пропущено (вже існують): {self.stats["skipped"]}')
            if self.stats['errors'] > 0:
                self.stdout.write(self.style.WARNING(f'  • Помилок: {self.stats["errors"]}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Критична помилка: {str(e)}'))
            raise

    def get_product_urls_from_sitemap(self):
        """Отримує всі URL товарів з sitemap.xml"""
        self.stdout.write('🗺️ Завантаження sitemap.xml...')
        
        try:
            response = self.session.get(f'{self.base_url}/sitemap.xml')
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'xml')
            urls = []
            
            # Перевіряємо чи це sitemap index
            sitemap_locs = soup.find_all('sitemap')
            if sitemap_locs:
                self.stdout.write(f'  Знайдено sitemap index з {len(sitemap_locs)} файлами')
                # Це sitemap index - завантажуємо кожен підфайл
                for sitemap in sitemap_locs:
                    loc = sitemap.find('loc')
                    if loc:
                        sitemap_url = loc.get_text()
                        self.stdout.write(f'  Завантаження {sitemap_url}...')
                        urls.extend(self.parse_single_sitemap(sitemap_url))
            else:
                # Це звичайний sitemap
                urls = self.parse_single_sitemap(f'{self.base_url}/sitemap.xml')
            
            return urls
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Помилка: {str(e)}'))
            return []
    
    def parse_single_sitemap(self, sitemap_url):
        """Парсить окремий sitemap файл"""
        try:
            response = self.session.get(sitemap_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'xml')
            
            urls = []
            for loc in soup.find_all('loc'):
                url = loc.get_text()
                # Пропускаємо російську версію сайту
                if '/ru/' in url:
                    continue
                # Товари мають формат /pXXXXXX
                if re.search(r'/p\d+', url):
                    urls.append(url)
            
            return urls
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'    Помилка: {str(e)}'))
            return []

    def import_product(self, product_url, skip_images=False):
        """Імпортує один товар"""
        try:
            response = self.session.get(product_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Парсимо дані
            data = self.parse_product_page(soup, product_url)
            
            if not data.get('name'):
                return None
            
            # Генеруємо унікальний slug
            base_slug = slugify(data['name'])
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Створюємо товар
            product = Product.objects.create(
                name=data['name'][:200],  # Обмежуємо довжину
                slug=slug,
                category=self.default_category,
                description=data.get('description', '')[:2000],
                retail_price=data['price'],
                is_active=True,
                stock=100,
            )
            
            # Завантажуємо зображення
            if not skip_images and data.get('images'):
                self.download_images(product, data['images'])
            
            # Додаємо характеристики
            if data.get('attributes'):
                self.create_attributes(product, data['attributes'])
            
            return product
            
        except Exception as e:
            raise Exception(f'Помилка імпорту: {str(e)}')

    def parse_product_page(self, soup, url):
        """Парсить дані товару"""
        data = {'images': [], 'attributes': []}
        
        # Назва
        h1 = soup.find('h1')
        if h1:
            data['name'] = h1.get_text(strip=True)
        
        # Ціна - шукаємо в id="product"
        product_block = soup.find(id='product')
        if not product_block:
            product_block = soup.find('div', class_=re.compile('product-info'))
        
        if product_block:
            price_elem = product_block.find(class_=re.compile('price'))
            if price_elem:
                price_text = price_elem.get_text()
                price_match = re.search(r'(\d+(?:\.\d+)?)\s*грн', price_text)
                if price_match:
                    data['price'] = Decimal(price_match.group(1))
        
        if 'price' not in data:
            data['price'] = Decimal('100.00')  # Дефолтна ціна
        
        # Опис
        desc_blocks = soup.find_all(['div', 'section'], class_=re.compile('description|tab-description'))
        for desc in desc_blocks:
            text = desc.get_text(strip=True)
            if len(text) > 50:
                data['description'] = text[:2000]
                break
        
        # Зображення
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src and 'catalog' in src and 'product' in src:
                if 'icon' not in src and 'logo' not in src:
                    full_url = urljoin(url, src)
                    full_url = full_url.replace('/cachewebp/', '/cache/').replace('.webp', '.jpg')
                    if full_url not in data['images']:
                        data['images'].append(full_url)
        
        return data

    def download_images(self, product, image_urls):
        """Завантажує зображення"""
        for idx, img_url in enumerate(image_urls[:3]):
            try:
                response = self.session.get(img_url, timeout=10)
                response.raise_for_status()
                
                ext = 'jpg'
                if 'content-type' in response.headers:
                    if 'png' in response.headers['content-type']:
                        ext = 'png'
                
                filename = f"{product.slug}_{idx+1}.{ext}"
                product_image = ProductImage(
                    product=product,
                    is_main=(idx == 0),
                    sort_order=idx
                )
                product_image.image.save(filename, ContentFile(response.content), save=True)
                self.stats['images'] += 1
                
            except Exception as e:
                pass

    def create_attributes(self, product, attributes):
        """Створює характеристики"""
        for idx, attr in enumerate(attributes[:20]):
            ProductAttribute.objects.create(
                product=product,
                name=attr['name'][:100],
                value=attr['value'][:200],
                sort_order=idx
            )

