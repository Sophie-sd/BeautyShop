"""
Тестова команда для перевірки доступу до старого сайту
"""
import requests
from django.core.management.base import BaseCommand
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Тестує доступ до старого сайту та виводить структуру'
    
    def handle(self, *args, **options):
        old_site_url = 'https://beautyshop-ukrane.com.ua'
        
        self.stdout.write(self.style.SUCCESS(f'\n=== ТЕСТУВАННЯ ДОСТУПУ ДО {old_site_url} ===\n'))
        
        # Тест 1: Головна сторінка
        try:
            response = requests.get(old_site_url, timeout=10)
            self.stdout.write(f'✓ Головна сторінка: {response.status_code}')
            
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.find('title')
            if title:
                self.stdout.write(f'  Title: {title.text.strip()}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Помилка доступу до головної: {e}'))
        
        # Тест 2: Каталог
        try:
            catalog_url = f'{old_site_url}/nigti'
            response = requests.get(catalog_url, timeout=10)
            self.stdout.write(f'\n✓ Каталог "Нігті": {response.status_code}')
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Шукаємо товари
            products = soup.find_all('div', class_=['product-thumb', 'product-layout'])
            self.stdout.write(f'  Знайдено товарів на сторінці: {len(products)}')
            
            if len(products) > 0:
                # Беремо перший товар
                first_product = products[0]
                link = first_product.find('a', href=True)
                if link:
                    self.stdout.write(f'  Перший товар URL: {link["href"]}')
                    
                    # Пробуємо отримати зображення з першого товару
                    img = first_product.find('img')
                    if img and img.get('src'):
                        self.stdout.write(f'  Зображення: {img["src"]}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Помилка доступу до каталогу: {e}'))
        
        # Тест 3: Пошук
        try:
            search_url = f'{old_site_url}/index.php?route=product/search&search=gel'
            response = requests.get(search_url, timeout=10)
            self.stdout.write(f'\n✓ Пошук (search=gel): {response.status_code}')
            
            soup = BeautifulSoup(response.content, 'html.parser')
            products = soup.find_all('div', class_=['product-thumb', 'product-layout'])
            self.stdout.write(f'  Знайдено товарів: {len(products)}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Помилка пошуку: {e}'))
        
        # Тест 4: Перевірка структури image URL
        self.stdout.write(self.style.SUCCESS('\n\n=== МОЖЛИВІ ШЛЯХИ ДО ЗОБРАЖЕНЬ ==='))
        self.stdout.write(f'{old_site_url}/image/catalog/...')
        self.stdout.write(f'{old_site_url}/image/cache/...')
        self.stdout.write(f'{old_site_url}/image/data/...')
        
        self.stdout.write('\n')

