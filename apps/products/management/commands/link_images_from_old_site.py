"""
Команда для прив'язки зображень товарів безпосередньо з URL старого сайту
(без завантаження в Cloudinary - для швидкого тестування)
"""
import requests
import time
from django.core.management.base import BaseCommand
from apps.products.models import Product, ProductImage, Category
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re


class Command(BaseCommand):
    help = 'Прив\'язує зображення товарів через URL зі старого сайту'
    
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
    
    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)
        parser.add_argument('--category', type=str)
    
    def normalize_name(self, name):
        return re.sub(r'[^a-zа-яіїє0-9]', '', name.lower())
    
    def scrape_category_page(self, category_url, page=1):
        try:
            url = f"{category_url}?page={page}" if page > 1 else category_url
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = []
            product_blocks = soup.find_all('div', class_='product-thumb')
            
            for block in product_blocks:
                try:
                    links = block.find_all('a', href=True)
                    product_link = None
                    product_name = None
                    
                    for link in links:
                        text = link.get_text(strip=True)
                        href = link['href']
                        if text and '/' in href and len(href.split('/')) > 4:
                            product_link = link
                            product_name = text
                            break
                    
                    if not product_name or not product_link:
                        continue
                    
                    product_url = product_link['href']
                    if not product_url.startswith('http'):
                        product_url = urljoin(self.old_site_url, product_url)
                    
                    img = block.find('img')
                    if not img:
                        continue
                    
                    img_url = img.get('src') or img.get('data-src')
                    if not img_url:
                        continue
                    
                    if not img_url.startswith('http'):
                        img_url = urljoin(self.old_site_url, img_url)
                    
                    products.append({
                        'name': product_name,
                        'url': product_url,
                        'image': img_url,
                        'normalized_name': self.normalize_name(product_name)
                    })
                    
                except Exception:
                    continue
            
            return products
        except Exception:
            return []
    
    def handle(self, *args, **options):
        limit = options['limit']
        category_filter = options.get('category')
        
        if category_filter:
            categories = Category.objects.filter(slug=category_filter, is_active=True, parent__isnull=True)
        else:
            categories = Category.objects.filter(is_active=True, parent__isnull=True)
        
        total_processed = 0
        total_success = 0
        
        for category in categories:
            if total_processed >= limit:
                break
                
            old_site_category = self.category_map.get(category.slug)
            if not old_site_category:
                continue
            
            self.stdout.write(self.style.SUCCESS(f'\n=== {category.name} ==='))
            
            subcategories = category.children.filter(is_active=True)
            category_ids = [category.id] + list(subcategories.values_list('id', flat=True))
            
            products_without_images = Product.objects.filter(
                category_id__in=category_ids,
                is_active=True,
                images__isnull=True
            ).distinct()[:limit - total_processed]
            
            if not products_without_images:
                continue
            
            catalog_url = f"{self.old_site_url}/{old_site_category}"
            old_site_products = []
            
            for page in range(1, 6):
                page_products = self.scrape_category_page(catalog_url, page)
                if not page_products:
                    break
                old_site_products.extend(page_products)
                time.sleep(0.5)
            
            for product in products_without_images:
                if total_processed >= limit:
                    break
                
                total_processed += 1
                normalized_name = self.normalize_name(product.name)
                
                found = None
                for old_product in old_site_products:
                    if normalized_name in old_product['normalized_name'] or old_product['normalized_name'] in normalized_name:
                        found = old_product
                        break
                
                if not found:
                    continue
                
                # Створюємо ProductImage з URL старого сайту
                img_obj = ProductImage(
                    product=product,
                    image=found['image'],
                    alt_text=product.name,
                    is_main=True,
                    sort_order=0
                )
                img_obj.save(skip_optimization=True)
                total_success += 1
                self.stdout.write(f'  ✓ {product.name[:60]}...')
                
                time.sleep(0.3)
        
        self.stdout.write(self.style.SUCCESS(f'\n\nОброблено: {total_processed} | Успішно: {total_success}'))

