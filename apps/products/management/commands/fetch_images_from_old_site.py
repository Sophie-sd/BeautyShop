"""
Завантаження зображень товарів зі старого сайту beautyshop-ukrane.com.ua на Cloudinary
Для товарів що вже імпортовані але не мають зображень
"""
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from apps.products.models import Product, ProductImage
import time
from urllib.parse import urljoin, quote
import re


class Command(BaseCommand):
    help = 'Завантажує зображення товарів зі старого сайту на Cloudinary'

    def __init__(self):
        super().__init__()
        self.old_site_url = 'https://beautyshop-ukrane.com.ua'
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.stats = {
            'processed': 0,
            'images_added': 0,
            'not_found': 0,
            'errors': 0
        }

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Максимальна кількість товарів для обробки'
        )
        parser.add_argument(
            '--sku',
            type=str,
            default=None,
            help='Конкретний SKU товару для обробки'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Завантажити зображення навіть якщо вони вже є'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        sku = options.get('sku')
        force = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS('🖼️  Завантаження зображень зі старого сайту'))
        self.stdout.write(f'📡 Сайт: {self.old_site_url}\n')
        
        # Вибираємо товари без зображень або конкретний товар
        if sku:
            products = Product.objects.filter(sku=sku)
            if not products.exists():
                self.stdout.write(self.style.ERROR(f'❌ Товар з SKU {sku} не знайдено'))
                return
        elif force:
            products = Product.objects.filter(is_active=True)
        else:
            products = Product.objects.filter(images__isnull=True, is_active=True).distinct()
        
        if limit:
            products = products[:limit]
        
        total = products.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Всі товари мають зображення!'))
            return
        
        self.stdout.write(f'📦 Знайдено товарів для обробки: {total}\n')
        
        for idx, product in enumerate(products, 1):
            try:
                self.stdout.write(f'\n[{idx}/{total}] {product.name[:60]}...')
                self.stdout.write(f'  SKU: {product.sku}')
                
                # Шукаємо товар на старому сайті за SKU або назвою
                product_url = self.find_product_on_old_site(product)
                
                if not product_url:
                    self.stdout.write(self.style.WARNING('  ⚠️  Не знайдено на старому сайті'))
                    self.stats['not_found'] += 1
                    continue
                
                self.stdout.write(f'  ✓ Знайдено: {product_url}')
                
                # Завантажуємо зображення
                images_added = self.download_images_for_product(product, product_url, force)
                
                if images_added > 0:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Завантажено {images_added} зображень'))
                    self.stats['images_added'] += images_added
                else:
                    self.stdout.write(self.style.WARNING('  ⚠️  Зображення не знайдено'))
                
                self.stats['processed'] += 1
                
                # Пауза між запитами
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Помилка: {str(e)}'))
                self.stats['errors'] += 1
                continue
        
        # Фінальна статистика
        self.stdout.write(self.style.SUCCESS(f'\n\n✅ Завершено!'))
        self.stdout.write(f'📊 Статистика:')
        self.stdout.write(f'  • Товарів оброблено: {self.stats["processed"]}')
        self.stdout.write(f'  • Зображень завантажено: {self.stats["images_added"]}')
        self.stdout.write(f'  • Не знайдено на сайті: {self.stats["not_found"]}')
        if self.stats['errors'] > 0:
            self.stdout.write(self.style.WARNING(f'  • Помилок: {self.stats["errors"]}'))

    def find_product_on_old_site(self, product):
        """Шукає товар на старому сайті"""
        
        # Спроба 1: Пошук за SKU через пошукову систему
        search_terms = [
            product.sku,
            product.name[:100],
        ]
        
        for term in search_terms:
            try:
                # Пошук через сайт
                search_url = f'{self.old_site_url}/index.php?route=product/search&search={quote(term)}'
                response = self.session.get(search_url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Шукаємо посилання на товар
                    product_links = soup.find_all('a', href=re.compile(r'product_id=\d+'))
                    
                    if product_links:
                        # Беремо перший результат
                        return urljoin(self.old_site_url, product_links[0]['href'])
                
                time.sleep(0.5)
                
            except Exception:
                continue
        
        return None

    def download_images_for_product(self, product, product_url, force=False):
        """Завантажує зображення товару"""
        try:
            response = self.session.get(product_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Видаляємо старі зображення якщо force=True
            if force:
                product.images.all().delete()
            
            # Знаходимо всі зображення товару
            image_urls = []
            
            # Шукаємо зображення в галереї
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    # Фільтруємо тільки зображення товарів
                    if 'catalog' in src or 'products' in src or 'cache' in src:
                        if 'logo' not in src.lower() and 'banner' not in src.lower():
                            full_url = urljoin(product_url, src)
                            # Використовуємо оригінальне зображення замість кешованого
                            full_url = re.sub(r'/cache/[^/]+/', '/cache/', full_url)
                            if full_url not in image_urls:
                                image_urls.append(full_url)
            
            if not image_urls:
                return 0
            
            # Завантажуємо перші 5 зображень
            images_added = 0
            for idx, img_url in enumerate(image_urls[:5]):
                try:
                    img_response = self.session.get(img_url, timeout=15)
                    img_response.raise_for_status()
                    
                    # Перевіряємо розмір
                    if len(img_response.content) > 10 * 1024 * 1024:  # Більше 10MB
                        continue
                    
                    # Визначаємо розширення
                    ext = 'jpg'
                    content_type = img_response.headers.get('content-type', '')
                    if 'png' in content_type:
                        ext = 'png'
                    elif 'webp' in content_type:
                        ext = 'webp'
                    
                    filename = f"{product.slug}_{idx+1}.{ext}"
                    
                    # Створюємо ProductImage і зберігаємо на Cloudinary
                    product_image = ProductImage(
                        product=product,
                        is_main=(idx == 0),
                        sort_order=idx,
                        alt_text=product.name
                    )
                    
                    product_image.image.save(filename, ContentFile(img_response.content), save=False)
                    product_image.save(skip_optimization=True)
                    
                    images_added += 1
                    
                    time.sleep(0.3)
                    
                except Exception:
                    continue
            
            return images_added
            
        except Exception as e:
            raise Exception(f'Помилка завантаження зображень: {str(e)}')

