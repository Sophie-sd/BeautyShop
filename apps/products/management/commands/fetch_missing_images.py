"""
Команда для завантаження відсутніх зображень товарів зі старого сайту
"""
import requests
import time
import cloudinary
import cloudinary.uploader
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.products.models import Product, ProductImage
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class Command(BaseCommand):
    help = 'Завантажує відсутні зображення товарів зі старого сайту beautyshop-ukrane.com.ua'
    
    def __init__(self):
        super().__init__()
        self.old_site_url = 'https://beautyshop-ukrane.com.ua'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
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
            default=50,
            help='Кількість товарів для обробки за один запуск (default: 50)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Затримка між запитами в секундах (default: 1.0)'
        )
    
    def search_product_on_old_site(self, product):
        """Шукає товар на старому сайті за назвою"""
        try:
            # Беремо перші 50 символів назви для пошуку
            search_query = product.name[:50].strip()
            search_url = f"{self.old_site_url}/index.php?route=product/search&search={search_query}"
            
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Шукаємо посилання на товар в результатах пошуку
            # Шукаємо в блоках product-thumb або product-layout
            product_blocks = soup.find_all(['div'], class_=['product-thumb', 'product-layout'])
            
            for block in product_blocks:
                link = block.find('a', href=True)
                if link and 'product/product' in link['href'] and 'product_id=' in link['href']:
                    product_url = link['href']
                    if not product_url.startswith('http'):
                        product_url = urljoin(self.old_site_url, product_url)
                    return product_url
            
            # Якщо не знайшли в блоках, шукаємо просто посилання
            product_links = soup.find_all('a', href=True)
            for link in product_links:
                if 'product/product' in link['href'] and 'product_id=' in link['href']:
                    product_url = link['href']
                    if not product_url.startswith('http'):
                        product_url = urljoin(self.old_site_url, product_url)
                    return product_url
            
            return None
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Помилка пошуку товару: {e}'))
            return None
    
    def get_product_images(self, product_url):
        """Отримує всі зображення товару зі сторінки"""
        try:
            response = self.session.get(product_url, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            image_urls = []
            
            # Шукаємо головне зображення
            main_image = soup.find('img', class_='img-responsive')
            if main_image and main_image.get('src'):
                img_url = main_image['src']
                if not img_url.startswith('http'):
                    img_url = urljoin(self.old_site_url, img_url)
                image_urls.append(img_url)
            
            # Шукаємо додаткові зображення (thumbnails)
            thumbnails = soup.find_all('a', class_='thumbnail')
            for thumb in thumbnails:
                if thumb.get('href'):
                    img_url = thumb['href']
                    if not img_url.startswith('http'):
                        img_url = urljoin(self.old_site_url, img_url)
                    if img_url not in image_urls:
                        image_urls.append(img_url)
            
            # Також шукаємо в галереї
            gallery_images = soup.find_all('img', class_='img-thumbnail')
            for img in gallery_images:
                if img.get('src'):
                    img_url = img['src']
                    # Спробуємо отримати повнорозмірне зображення
                    if img_url.endswith('-thumb'):
                        img_url = img_url.replace('-thumb', '')
                    if not img_url.startswith('http'):
                        img_url = urljoin(self.old_site_url, img_url)
                    if img_url not in image_urls:
                        image_urls.append(img_url)
            
            return image_urls
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Помилка отримання зображень: {e}'))
            return []
    
    def upload_image_to_cloudinary(self, image_url, product):
        """Завантажує зображення в Cloudinary"""
        try:
            # Завантажуємо зображення
            result = cloudinary.uploader.upload(
                image_url,
                folder=f"products/{product.category.slug}",
                public_id=f"{product.sku}_{int(time.time())}",
                overwrite=False,
                resource_type="image",
                transformation=[
                    {'quality': 'auto:good'},
                    {'fetch_format': 'auto'}
                ]
            )
            
            return result['secure_url']
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Помилка завантаження в Cloudinary: {e}'))
            return None
    
    def handle(self, *args, **options):
        limit = options['limit']
        delay = options['delay']
        
        # Отримуємо товари без зображень
        products_without_images = Product.objects.filter(
            is_active=True,
            images__isnull=True
        ).distinct()[:limit]
        
        total = products_without_images.count()
        self.stdout.write(self.style.SUCCESS(f'Знайдено {total} товарів без зображень'))
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Всі товари вже мають зображення!'))
            return
        
        processed = 0
        success = 0
        failed = 0
        
        for product in products_without_images:
            processed += 1
            self.stdout.write(f'\n[{processed}/{total}] Обробка: {product.sku} - {product.name}')
            
            # Шукаємо товар на старому сайті
            product_url = self.search_product_on_old_site(product)
            
            if not product_url:
                self.stdout.write(self.style.WARNING(f'  ⚠ Товар не знайдено на старому сайті'))
                failed += 1
                time.sleep(delay)
                continue
            
            self.stdout.write(f'  ✓ Знайдено: {product_url}')
            
            # Отримуємо зображення
            image_urls = self.get_product_images(product_url)
            
            if not image_urls:
                self.stdout.write(self.style.WARNING(f'  ⚠ Зображення не знайдено'))
                failed += 1
                time.sleep(delay)
                continue
            
            self.stdout.write(f'  ✓ Знайдено {len(image_urls)} зображень')
            
            # Завантажуємо зображення
            images_uploaded = 0
            for idx, img_url in enumerate(image_urls):
                cloudinary_url = self.upload_image_to_cloudinary(img_url, product)
                
                if cloudinary_url:
                    # Створюємо ProductImage
                    ProductImage.objects.create(
                        product=product,
                        image=cloudinary_url,
                        alt_text=product.name,
                        is_main=(idx == 0),
                        sort_order=idx
                    )
                    images_uploaded += 1
                    self.stdout.write(f'  ✓ Завантажено зображення {idx + 1}/{len(image_urls)}')
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Не вдалось завантажити зображення {idx + 1}'))
            
            if images_uploaded > 0:
                success += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Успішно завантажено {images_uploaded} зображень'))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(f'  ✗ Не вдалось завантажити жодного зображення'))
            
            time.sleep(delay)
        
        # Підсумок
        self.stdout.write(self.style.SUCCESS(f'\n\n=== ПІДСУМОК ==='))
        self.stdout.write(self.style.SUCCESS(f'Оброблено: {processed}'))
        self.stdout.write(self.style.SUCCESS(f'Успішно: {success}'))
        self.stdout.write(self.style.ERROR(f'Помилок: {failed}'))

