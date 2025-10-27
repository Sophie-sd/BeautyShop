"""
Автоматичний імпорт товарів для Render з Cloudinary
Оптимізовано для роботи під час build процесу
Зображення автоматично завантажуються на Cloudinary через Django STORAGES
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
import gc
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed


class Command(BaseCommand):
    help = 'Автоматичний імпорт товарів з Cloudinary для Render'

    def __init__(self):
        super().__init__()
        self.base_url = 'https://webosova.com.ua'
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
        self.category_cache = {}
        
        # Мапінг URL категорій на наші категорії
        self.URL_CATEGORY_MAP = {
            'nigti': 'nigti',
            'nogti': 'nigti',
            'nails': 'nigti',
            'gel-laki': 'nigti',
            'gel-lak': 'nigti',
            'baza': 'nigti',
            'top': 'nigti',
            'volosya': 'volossia',
            'volossya': 'volossia',
            'volossia': 'volossia',
            'hair': 'volossia',
            'shampun': 'volossia',
            'maska': 'volossia',
            'brovi': 'brovy-ta-vii',
            'brows': 'brovy-ta-vii',
            'vii': 'brovy-ta-vii',
            'resnicy': 'brovy-ta-vii',
            'depilyaciya': 'depilyatsiya',
            'depilacia': 'depilyatsiya',
            'depilyatsiya': 'depilyatsiya',
            'shugaring': 'depilyatsiya',
            'vosk': 'depilyatsiya',
            'pasta': 'depilyatsiya',
            'kosmetika': 'kosmetyka',
            'kosmetyka': 'kosmetyka',
            'krem': 'kosmetyka',
            'serum': 'kosmetyka',
            'makiyazh': 'makiyazh',
            'makeup': 'makiyazh',
            'pomada': 'makiyazh',
            'tush': 'makiyazh',
            'odnorazova': 'odnorazova-produktsia',
            'disposable': 'odnorazova-produktsia',
            'rukavychky': 'odnorazova-produktsia',
            'masochky': 'odnorazova-produktsia',
            'dezinfekciya': 'dezinfektsiya-ta-sterylizatsiya',
            'sterilizaciya': 'dezinfektsiya-ta-sterylizatsiya',
            'dezinfektsiya': 'dezinfektsiya-ta-sterylizatsiya',
            'antiseptyk': 'dezinfektsiya-ta-sterylizatsiya',
            'mebli': 'mebli-dlya-saloniv',
            'furniture': 'mebli-dlya-saloniv',
            'kreslo': 'mebli-dlya-saloniv',
            'kushetka': 'mebli-dlya-saloniv',
            'kosmetologiya': 'kosmetyka',
            'tara': 'odnorazova-produktsia',
            'sale': 'sale',
            'akciya': 'sale',
            'znuzhky': 'sale',
        }

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=200,
            help='Кількість товарів в одному батчі'
        )
        parser.add_argument(
            '--workers',
            type=int,
            default=2,
            help='Кількість паралельних потоків'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Максимальна кількість товарів для імпорту'
        )

    def handle(self, *args, **options):
        batch_size = options.get('batch_size', 200)
        workers = min(options.get('workers', 2), 3)
        limit = options.get('limit')
        
        self.stdout.write(self.style.SUCCESS('🚀 Автоматичний імпорт товарів для Render'))
        self.stdout.write('📡 Зображення завантажуються на Cloudinary\n')
        
        # Створюємо категорію за замовчуванням
        self.default_category, _ = Category.objects.get_or_create(
            slug='import-webosova',
            defaults={'name': 'Імпорт з Webosova', 'is_active': True}
        )
        
        try:
            # Отримуємо список URL товарів з sitemap
            product_urls = self.get_product_urls_from_sitemap()
            
            if not product_urls:
                self.stdout.write(self.style.ERROR('❌ Не знайдено товарів у sitemap'))
                return
            
            if limit:
                product_urls = product_urls[:limit]
            
            total_products = len(product_urls)
            self.stdout.write(f'📦 Знайдено товарів: {total_products}')
            self.stdout.write(f'⚙️  Батч: {batch_size}, Потоків: {workers}\n')
            
            # Обробляємо по батчам
            for batch_start in range(0, total_products, batch_size):
                batch_end = min(batch_start + batch_size, total_products)
                batch_urls = product_urls[batch_start:batch_end]
                
                self.stdout.write(f'\n📦 Батч {batch_start+1}-{batch_end}/{total_products}')
                
                # Імпортуємо товари паралельно
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = {
                        executor.submit(self.import_product, url): url 
                        for url in batch_urls
                    }
                    
                    for future in as_completed(futures):
                        url = futures[future]
                        try:
                            result = future.result(timeout=60)
                            if result:
                                self.stats['products'] += 1
                                if self.stats['products'] % 25 == 0:
                                    self.stdout.write(
                                        f'  ✓ {self.stats["products"]}/{total_products} '
                                        f'(📷 {self.stats["images"]} зобр.)'
                                    )
                        except TimeoutError:
                            self.stats['errors'] += 1
                        except Exception:
                            self.stats['errors'] += 1
                
                # Очищуємо пам'ять
                gc.collect()
                time.sleep(2)
            
            # Фінальна статистика
            gc.collect()
            
            self.stdout.write(self.style.SUCCESS(f'\n✅ Імпорт завершено!'))
            self.stdout.write(f'📊 Статистика:')
            self.stdout.write(f'  • Товарів імпортовано: {self.stats["products"]}')
            self.stdout.write(f'  • Зображень на Cloudinary: {self.stats["images"]}')
            self.stdout.write(f'  • Пропущено (дублікати): {self.stats["skipped"]}')
            if self.stats['errors'] > 0:
                self.stdout.write(self.style.WARNING(f'  • Помилок: {self.stats["errors"]}'))
            
            self.stdout.write('\n📂 Товари додані в категорії та готові до фільтрації!')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Критична помилка: {str(e)}'))
            raise
        finally:
            gc.collect()

    def get_product_urls_from_sitemap(self):
        """Отримує всі URL товарів з sitemap.xml"""
        self.stdout.write('🗺️  Завантаження sitemap.xml...')
        
        try:
            response = self.session.get(f'{self.base_url}/sitemap.xml', timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'xml')
            urls = []
            
            # Перевіряємо чи це sitemap index
            sitemap_locs = soup.find_all('sitemap')
            if sitemap_locs:
                for sitemap in sitemap_locs:
                    loc = sitemap.find('loc')
                    if loc:
                        urls.extend(self.parse_single_sitemap(loc.get_text()))
            else:
                urls = self.parse_single_sitemap(f'{self.base_url}/sitemap.xml')
            
            return urls
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Помилка: {str(e)}'))
            return []
    
    def parse_single_sitemap(self, sitemap_url):
        """Парсить окремий sitemap файл"""
        try:
            response = self.session.get(sitemap_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'xml')
            
            urls = []
            for loc in soup.find_all('loc'):
                url = loc.get_text()
                # Пропускаємо російську версію
                if '/ru/' in url:
                    continue
                # Товари мають формат /pXXXXXX
                if re.search(r'/p\d+', url):
                    urls.append(url)
            
            return urls
        except Exception:
            return []

    def import_product(self, product_url):
        """Імпортує один товар з зображеннями на Cloudinary"""
        try:
            # Завантажуємо сторінку товару з retry
            for attempt in range(2):
                try:
                    response = self.session.get(product_url, timeout=30, stream=True)
                    response.raise_for_status()
                    break
                except Exception:
                    if attempt == 0:
                        time.sleep(1)
                        continue
                    raise
            
            # Обмежуємо розмір для економії
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > 1024 * 1024:
                    break
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Парсимо дані товару
            data = self.parse_product_page(soup, product_url)
            
            if not data.get('name'):
                return None
            
            # Визначаємо категорію
            category = self.detect_category_from_url(product_url)
            
            # Генеруємо унікальний slug
            base_slug = slugify(data['name'])
            slug = base_slug
            counter = 1
            
            # Перевіряємо дублікати
            while Product.objects.filter(slug=slug).exists():
                if counter == 1 and Product.objects.filter(name=data['name'][:200]).exists():
                    self.stats['skipped'] += 1
                    return None
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Створюємо товар з усіма полями
            product = Product.objects.create(
                name=data['name'][:200],
                slug=slug,
                category=category,
                description=data.get('description', '')[:2000],
                retail_price=data['price'],
                is_active=True,
                stock=100,
                # Додаткові поля для фільтрації
                is_new=False,
                is_top=False,
                is_sale=False,
                is_featured=False,
            )
            
            # Завантажуємо зображення (автоматично на Cloudinary в production)
            if data.get('images'):
                self.download_images_to_cloudinary(product, data['images'])
            
            # Додаємо характеристики
            if data.get('attributes'):
                self.create_attributes(product, data['attributes'])
            
            return product
            
        except Exception as e:
            raise Exception(f'Помилка імпорту {product_url}: {str(e)}')

    def parse_product_page(self, soup, url):
        """Парсить дані зі сторінки товару"""
        data = {'images': [], 'attributes': []}
        
        # Назва
        h1 = soup.find('h1')
        if h1:
            data['name'] = h1.get_text(strip=True)
        
        # Ціна
        product_block = soup.find(id='product') or soup.find('div', class_=re.compile('product-info'))
        if product_block:
            price_elem = product_block.find(class_=re.compile('price'))
            if price_elem:
                price_text = price_elem.get_text()
                price_match = re.search(r'(\d+(?:\.\d+)?)\s*грн', price_text)
                if price_match:
                    data['price'] = Decimal(price_match.group(1))
        
        if 'price' not in data:
            data['price'] = Decimal('100.00')
        
        # Опис
        desc_blocks = soup.find_all(['div', 'section'], class_=re.compile('description|tab-description|product-desc'))
        for desc in desc_blocks:
            text = desc.get_text(strip=True)
            if len(text) > 50:
                data['description'] = text[:2000]
                break
        
        # Зображення - збираємо всі можливі
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-lazy')
            if src and ('catalog' in src or 'product' in src):
                if 'icon' not in src and 'logo' not in src and 'banner' not in src:
                    full_url = urljoin(url, src)
                    # Конвертуємо webp на jpg
                    full_url = full_url.replace('/cachewebp/', '/cache/').replace('.webp', '.jpg')
                    if full_url not in data['images']:
                        data['images'].append(full_url)
        
        # Характеристики - парсимо з таблиць
        tables = soup.find_all('table', class_=re.compile('attr|char|spec|properties'))
        for table in tables:
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    name = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if name and value:
                        data['attributes'].append({'name': name, 'value': value})
        
        return data

    def download_images_to_cloudinary(self, product, image_urls):
        """Завантажує зображення на Cloudinary"""
        for idx, img_url in enumerate(image_urls[:3]):
            try:
                response = self.session.get(img_url, timeout=20)
                response.raise_for_status()
                
                if len(response.content) > 5 * 1024 * 1024:
                    continue
                
                ext = 'jpg'
                if 'content-type' in response.headers and 'png' in response.headers['content-type']:
                    ext = 'png'
                
                filename = f"{product.slug}_{idx+1}.{ext}"
                
                product_image = ProductImage(
                    product=product,
                    is_main=(idx == 0),
                    sort_order=idx,
                    alt_text=product.name
                )
                # Зберігаємо безпосередньо на Cloudinary без оптимізації
                product_image.image.save(filename, ContentFile(response.content), save=True)
                
                self.stats['images'] += 1
                del response
                
            except Exception as e:
                # Детальне логування помилок
                import sys
                print(f"⚠️  Помилка завантаження зображення {img_url[:80]}: {str(e)}", file=sys.stderr)
                pass

    def detect_category_from_url(self, url):
        """Визначає категорію на основі URL товару"""
        url_lower = url.lower()
        
        for url_part, category_slug in self.URL_CATEGORY_MAP.items():
            if f'/{url_part}/' in url_lower or f'/{url_part}-' in url_lower or f'-{url_part}/' in url_lower:
                if category_slug not in self.category_cache:
                    cat = Category.objects.filter(slug=category_slug).first()
                    self.category_cache[category_slug] = cat if cat else self.default_category
                return self.category_cache[category_slug]
        
        return self.default_category
    
    def create_attributes(self, product, attributes):
        """Створює характеристики товару для фільтрації"""
        for idx, attr in enumerate(attributes[:30]):  # До 30 характеристик
            try:
                ProductAttribute.objects.create(
                    product=product,
                    name=attr['name'][:100],
                    value=attr['value'][:200],
                    sort_order=idx
                )
            except Exception:
                pass  # Ігноруємо дублікати

