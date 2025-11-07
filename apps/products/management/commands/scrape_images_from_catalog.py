"""
Команда для завантаження зображень товарів зі старого сайту через скрапінг каталогу
"""
import requests
import time
import cloudinary
import cloudinary.uploader
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.products.models import Product, ProductImage, Category
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import re


class Command(BaseCommand):
    help = 'Завантажує зображення товарів зі старого сайту через скрапінг каталогу'
    
    def __init__(self):
        super().__init__()
        self.old_site_url = 'https://beautyshop-ukrane.com.ua'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Мапа категорій Django -> старий сайт
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
        
        # Ініціалізуємо Cloudinary
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_STORAGE.get('CLOUD_NAME'),
            api_key=settings.CLOUDINARY_STORAGE.get('API_KEY'),
            api_secret=settings.CLOUDINARY_STORAGE.get('API_SECRET'),
            secure=True
        )
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Кількість товарів для обробки (default: 100)'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Обробити тільки конкретну категорію (slug)'
        )
    
    def normalize_name(self, name):
        """Нормалізує назву товару для порівняння"""
        # Видаляємо всі не-алфавітні символи і приводимо до нижнього регістру
        normalized = re.sub(r'[^a-zа-яіїє0-9]', '', name.lower())
        return normalized
    
    def scrape_category_page(self, category_url, page=1):
        """Скрапить сторінку каталогу і повертає товари"""
        try:
            url = f"{category_url}?page={page}" if page > 1 else category_url
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            
            # Шукаємо товари на сторінці (різні варіанти селекторів)
            product_blocks = soup.find_all('div', class_='product-thumb')
            if not product_blocks:
                product_blocks = soup.find_all('div', class_='product-layout')
            if not product_blocks:
                product_blocks = soup.find_all('div', {'class': lambda x: x and 'product' in x})
            
            self.stdout.write(f'    Debug: знайдено {len(product_blocks)} блоків товарів')
            
            for idx, block in enumerate(product_blocks):
                try:
                    # Знаходимо посилання на товар (зазвичай друге посилання містить назву)
                    links = block.find_all('a', href=True)
                    product_link = None
                    product_name = None
                    
                    if idx == 0:  # Debug для першого блоку
                        self.stdout.write(f'      Debug блок #{idx}: знайдено {len(links)} посилань')
                    
                    for link in links:
                        text = link.get_text(strip=True)
                        href = link['href']
                        if idx == 0:
                            self.stdout.write(f'        Link: "{text[:30]}" -> {href[:50]}')
                        # Перевіряємо що це посилання на товар (не просто категорія)
                        if text and '/' in href and len(href.split('/')) > 4:
                            product_link = link
                            product_name = text
                            break
                    
                    if not product_name or not product_link:
                        if idx == 0:
                            self.stdout.write(f'      Debug: пропускаємо - немає назви або посилання')
                        continue
                    
                    # Посилання на товар
                    product_url = product_link['href']
                    if not product_url.startswith('http'):
                        product_url = urljoin(self.old_site_url, product_url)
                    
                    # Зображення товару
                    img = block.find('img')
                    if not img:
                        if idx == 0:
                            self.stdout.write(f'      Debug: немає img тегу')
                        continue
                    
                    img_url = img.get('src') or img.get('data-src')
                    if not img_url:
                        if idx == 0:
                            self.stdout.write(f'      Debug: немає src в img')
                        continue
                    
                    if not img_url.startswith('http'):
                        img_url = urljoin(self.old_site_url, img_url)
                    
                    products.append({
                        'name': product_name,
                        'url': product_url,
                        'image': img_url,
                        'normalized_name': self.normalize_name(product_name)
                    })
                    
                    if idx == 0:
                        self.stdout.write(f'      Debug: товар додано успішно: {product_name[:50]}')
                    
                except Exception as e:
                    self.stdout.write(f'    Debug: помилка обробки блоку: {e}')
                    continue
            
            return products
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Помилка скрапінгу: {e}'))
            return []
    
    def get_product_images_from_page(self, product_url):
        """Отримує всі зображення зі сторінки товару"""
        try:
            response = self.session.get(product_url, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            images = []
            
            # Головне зображення
            main_img = soup.find('a', class_='thumbnail') or soup.find('img', class_='img-responsive')
            if main_img:
                img_url = main_img.get('href') or main_img.get('src')
                if img_url and not img_url.startswith('http'):
                    img_url = urljoin(self.old_site_url, img_url)
                if img_url:
                    images.append(img_url)
            
            # Додаткові зображення
            thumbnails = soup.find_all('a', class_='thumbnail')
            for thumb in thumbnails[1:]:  # Пропускаємо перше (головне)
                img_url = thumb.get('href')
                if img_url and not img_url.startswith('http'):
                    img_url = urljoin(self.old_site_url, img_url)
                if img_url and img_url not in images:
                    images.append(img_url)
            
            return images
            
        except Exception as e:
            return []
    
    def upload_image_to_cloudinary(self, image_url, product):
        """Завантажує зображення в Cloudinary"""
        try:
            result = cloudinary.uploader.upload(
                image_url,
                folder=f"products/{product.category.slug}",
                public_id=f"{product.sku}_{int(time.time())}",
                overwrite=False,
                resource_type="image"
            )
            return result['secure_url']
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Помилка Cloudinary: {e}'))
            return None
    
    def handle(self, *args, **options):
        limit = options['limit']
        category_filter = options.get('category')
        
        # Отримуємо категорії для обробки
        if category_filter:
            categories = Category.objects.filter(slug=category_filter, is_active=True, parent__isnull=True)
        else:
            categories = Category.objects.filter(is_active=True, parent__isnull=True)
        
        total_processed = 0
        total_success = 0
        
        for category in categories:
            old_site_category = self.category_map.get(category.slug)
            if not old_site_category:
                self.stdout.write(self.style.WARNING(f'⚠ Немає мапи для категорії: {category.slug}'))
                continue
            
            self.stdout.write(self.style.SUCCESS(f'\n\n=== КАТЕГОРІЯ: {category.name} ==='))
            
            # Отримуємо товари без фото з цієї категорії
            subcategories = category.children.filter(is_active=True)
            category_ids = [category.id] + list(subcategories.values_list('id', flat=True))
            
            products_without_images = Product.objects.filter(
                category_id__in=category_ids,
                is_active=True,
                images__isnull=True
            ).distinct()[:limit]
            
            if not products_without_images:
                self.stdout.write('  ✓ Всі товари мають зображення')
                continue
            
            self.stdout.write(f'  Товарів без фото: {products_without_images.count()}')
            
            # Скрапимо каталог старого сайту
            catalog_url = f"{self.old_site_url}/{old_site_category}"
            old_site_products = []
            
            # Скрапимо перші 5 сторінок
            for page in range(1, 6):
                page_products = self.scrape_category_page(catalog_url, page)
                if not page_products:
                    break
                old_site_products.extend(page_products)
                self.stdout.write(f'  Скраплено сторінка {page}: {len(page_products)} товарів')
                time.sleep(1)
            
            self.stdout.write(f'  Всього на старому сайті: {len(old_site_products)} товарів')
            
            # Порівнюємо і завантажуємо
            for product in products_without_images:
                if total_processed >= limit:
                    break
                
                total_processed += 1
                normalized_name = self.normalize_name(product.name)
                
                # Шукаємо співпадіння
                found = None
                for old_product in old_site_products:
                    if normalized_name in old_product['normalized_name'] or old_product['normalized_name'] in normalized_name:
                        found = old_product
                        break
                
                if not found:
                    self.stdout.write(f'  ⚠ Не знайдено: {product.name[:50]}...')
                    continue
                
                self.stdout.write(f'  ✓ Знайдено: {product.name[:50]}...')
                
                # Завантажуємо зображення
                images_to_upload = [found['image']]
                
                # Спробуємо отримати додаткові зображення зі сторінки товару
                additional_images = self.get_product_images_from_page(found['url'])
                if additional_images:
                    images_to_upload = additional_images
                
                uploaded_count = 0
                for idx, img_url in enumerate(images_to_upload):
                    cloudinary_url = self.upload_image_to_cloudinary(img_url, product)
                    if cloudinary_url:
                        ProductImage.objects.create(
                            product=product,
                            image=cloudinary_url,
                            alt_text=product.name,
                            is_main=(idx == 0),
                            sort_order=idx
                        )
                        uploaded_count += 1
                
                if uploaded_count > 0:
                    total_success += 1
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Завантажено {uploaded_count} зображень'))
                
                time.sleep(1)
        
        self.stdout.write(self.style.SUCCESS(f'\n\n=== ПІДСУМОК ==='))
        self.stdout.write(f'Оброблено: {total_processed}')
        self.stdout.write(f'Успішно: {total_success}')

