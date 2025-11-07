"""
Повний аудит проекту: код, продуктивність, оптимізація
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Count, Q, F
from apps.products.models import Product, Category, ProductImage
import os
import time


class Command(BaseCommand):
    help = 'Повна перевірка проекту на помилки, дублювання, оптимізацію'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('ПОВНИЙ АУДИТ ПРОЕКТУ'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        self.check_commands()
        self.check_database()
        self.check_performance()
        self.check_code_quality()
        self.final_recommendations()
    
    def check_commands(self):
        """Перевірка management команд"""
        self.stdout.write(self.style.SUCCESS('1. MANAGEMENT КОМАНДИ\n'))
        
        commands_dir = 'apps/products/management/commands'
        commands = []
        
        for f in os.listdir(commands_dir):
            if f.endswith('.py') and f != '__init__.py':
                size = os.path.getsize(os.path.join(commands_dir, f))
                commands.append((f, size))
        
        # Групуємо за призначенням
        categories = {
            'IMPORT': [],
            'IMAGES': [],
            'CHECK': [],
            'EXPORT': [],
            'SETUP': [],
        }
        
        for name, size in commands:
            if 'import' in name:
                categories['IMPORT'].append((name, size))
            elif any(x in name for x in ['fetch', 'scrape', 'link', 'analyze', 'image']):
                categories['IMAGES'].append((name, size))
            elif 'check' in name:
                categories['CHECK'].append((name, size))
            elif 'export' in name:
                categories['EXPORT'].append((name, size))
            else:
                categories['SETUP'].append((name, size))
        
        total = len(commands)
        self.stdout.write(f'Всього команд: {total}\n')
        
        for cat, items in categories.items():
            if items:
                self.stdout.write(f'{cat}: {len(items)} команд')
                for name, size in items:
                    size_kb = size / 1024
                    self.stdout.write(f'  • {name} ({size_kb:.1f}KB)')
        
        # Рекомендації
        if len(categories['IMAGES']) > 5:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Занадто багато команд для зображень ({len(categories["IMAGES"])}), можна об\'єднати'))
        
        if len(categories['IMPORT']) > 5:
            self.stdout.write(self.style.WARNING(f'⚠️  Занадто багато команд для імпорту ({len(categories["IMPORT"])}), можна об\'єднати'))
    
    def check_database(self):
        """Перевірка БД"""
        self.stdout.write(self.style.SUCCESS('\n\n2. БАЗА ДАНИХ\n'))
        
        # Статистика
        products = Product.objects.count()
        categories = Category.objects.count()
        images = ProductImage.objects.count()
        
        self.stdout.write(f'Товарів: {products}')
        self.stdout.write(f'Категорій: {categories}')
        self.stdout.write(f'Зображень: {images}')
        
        # Перевірка цілісності
        issues = []
        
        # Товари без категорій
        no_cat = Product.objects.filter(category__isnull=True).count()
        if no_cat > 0:
            issues.append(f'{no_cat} товарів без категорії')
        
        # Дублікати
        dup_sku = Product.objects.values('sku').annotate(c=Count('id')).filter(c__gt=1).count()
        if dup_sku > 0:
            issues.append(f'{dup_sku} дублікатів SKU')
        
        dup_slug = Product.objects.values('slug').annotate(c=Count('id')).filter(c__gt=1).count()
        if dup_slug > 0:
            issues.append(f'{dup_slug} дублікатів slug')
        
        # Некоректні ціни
        bad_prices = Product.objects.filter(
            Q(retail_price__isnull=True) | Q(retail_price__lte=0)
        ).count()
        if bad_prices > 0:
            issues.append(f'{bad_prices} товарів з некоректною ціною')
        
        # Логіка цін
        wrong_wholesale = Product.objects.filter(
            wholesale_price__isnull=False,
            wholesale_price__gt=F('retail_price')
        ).count()
        if wrong_wholesale > 0:
            issues.append(f'{wrong_wholesale} товарів де оптова > роздрібної')
        
        wrong_sale = Product.objects.filter(
            is_sale=True,
            sale_price__gte=F('retail_price')
        ).count()
        if wrong_sale > 0:
            issues.append(f'{wrong_sale} товарів де акційна >= роздрібної')
        
        if issues:
            self.stdout.write(self.style.ERROR('\n❌ Проблеми:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'  • {issue}'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ БД без помилок'))
    
    def check_performance(self):
        """Перевірка продуктивності"""
        self.stdout.write(self.style.SUCCESS('\n\n3. ПРОДУКТИВНІСТЬ\n'))
        
        # Тест CategoryView запиту
        connection.queries_log.clear()
        
        start = time.time()
        category = Category.objects.filter(is_active=True).first()
        if category:
            products = Product.objects.filter(
                category=category,
                is_active=True
            ).select_related('category').prefetch_related('images')[:12]
            list(products)
        end = time.time()
        
        query_time = (end - start) * 1000
        query_count = len(connection.queries)
        
        self.stdout.write(f'CategoryView запит:')
        self.stdout.write(f'  Час: {query_time:.2f}ms')
        self.stdout.write(f'  Запитів: {query_count}')
        
        if query_time < 50:
            self.stdout.write(self.style.SUCCESS('  ✅ Відмінна швидкість'))
        elif query_time < 200:
            self.stdout.write(self.style.SUCCESS('  ✅ Хороша швидкість'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Повільно, потрібна оптимізація'))
        
        # N+1 проблема
        connection.queries_log.clear()
        products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')[:5]
        for p in products:
            _ = p.category.name
            _ = list(p.images.all())
        optimized_queries = len(connection.queries)
        
        self.stdout.write(f'\nN+1 перевірка:')
        self.stdout.write(f'  З оптимізацією: {optimized_queries} запитів')
        
        if optimized_queries <= 2:
            self.stdout.write(self.style.SUCCESS('  ✅ Оптимально'))
        else:
            self.stdout.write(self.style.WARNING('  ⚠️  Можна покращити'))
    
    def check_code_quality(self):
        """Перевірка якості коду"""
        self.stdout.write(self.style.SUCCESS('\n\n4. ЯКІСТЬ КОДУ\n'))
        
        # Перевірка views.py
        views_file = 'apps/products/views.py'
        if os.path.exists(views_file):
            with open(views_file, 'r') as f:
                content = f.read()
                
                has_select_related = 'select_related' in content
                has_prefetch = 'prefetch_related' in content
                
                self.stdout.write('views.py:')
                if has_select_related and has_prefetch:
                    self.stdout.write(self.style.SUCCESS('  ✅ Використовує select_related/prefetch_related'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠️  Немає оптимізації запитів'))
        
        # Перевірка models.py
        models_file = 'apps/products/models.py'
        if os.path.exists(models_file):
            with open(models_file, 'r') as f:
                content = f.read()
                
                has_indexes = 'indexes = [' in content or 'Index(' in content
                has_select_related_meta = 'select_related' in content
                
                self.stdout.write('\nmodels.py:')
                if has_indexes:
                    self.stdout.write(self.style.SUCCESS('  ✅ Визначені індекси'))
                else:
                    self.stdout.write(self.style.WARNING('  ⚠️  Немає індексів'))
        
        # Перевірка JS файлів
        catalog_js = 'static/js/catalog.js'
        if os.path.exists(catalog_js):
            size = os.path.getsize(catalog_js)
            self.stdout.write(f'\ncatalog.js: {size/1024:.1f}KB')
            if size > 100000:  # 100KB
                self.stdout.write(self.style.WARNING('  ⚠️  Великий розмір, можна мінімізувати'))
            else:
                self.stdout.write(self.style.SUCCESS('  ✅ Оптимальний розмір'))
    
    def final_recommendations(self):
        """Фінальні рекомендації"""
        self.stdout.write(self.style.SUCCESS('\n\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('РЕКОМЕНДАЦІЇ'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        recommendations = []
        
        # Перевірка команд
        commands_dir = 'apps/products/management/commands'
        command_count = len([f for f in os.listdir(commands_dir) if f.endswith('.py') and f != '__init__.py'])
        
        if command_count > 15:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Код',
                'text': f'Забагато команд ({command_count}). Об\'єднати схожі (fetch_images, scrape_images, link_images)'
            })
        
        # Перевірка зображень
        products_count = Product.objects.count()
        images_count = Product.objects.filter(images__isnull=False).distinct().count()
        coverage = (images_count / products_count * 100) if products_count > 0 else 0
        
        if coverage < 50:
            recommendations.append({
                'priority': 'LOW',
                'category': 'Контент',
                'text': f'Покриття зображеннями {coverage:.1f}%. Поступово додавати фото'
            })
        
        # Перевірка описів
        no_desc = Product.objects.filter(
            is_active=True
        ).filter(
            Q(description='') | Q(description__isnull=True)
        ).count()
        
        if no_desc > 0:
            recommendations.append({
                'priority': 'LOW',
                'category': 'Контент',
                'text': f'{no_desc} товарів без опису'
            })
        
        # Виводимо рекомендації
        if not recommendations:
            self.stdout.write(self.style.SUCCESS('✅ Проект в відмінному стані!'))
            self.stdout.write(self.style.SUCCESS('   Немає критичних проблем'))
        else:
            priorities = {'HIGH': [], 'MEDIUM': [], 'LOW': []}
            for rec in recommendations:
                priorities[rec['priority']].append(rec)
            
            if priorities['HIGH']:
                self.stdout.write(self.style.ERROR('🔴 ВИСОКИЙ ПРІОРИТЕТ:'))
                for rec in priorities['HIGH']:
                    self.stdout.write(f'  [{rec["category"]}] {rec["text"]}')
            
            if priorities['MEDIUM']:
                self.stdout.write(self.style.WARNING('\n🟡 СЕРЕДНІЙ ПРІОРИТЕТ:'))
                for rec in priorities['MEDIUM']:
                    self.stdout.write(f'  [{rec["category"]}] {rec["text"]}')
            
            if priorities['LOW']:
                self.stdout.write('\n🟢 НИЗЬКИЙ ПРІОРИТЕТ:')
                for rec in priorities['LOW']:
                    self.stdout.write(f'  [{rec["category"]}] {rec["text"]}')
        
        self.stdout.write('\n')

