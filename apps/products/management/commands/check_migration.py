"""
Команда для перевірки цілісності даних після міграції
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Min, Max, Avg, F
from django.db import models
from apps.products.models import Product, Category, ProductImage
from decimal import Decimal


class Command(BaseCommand):
    help = 'Перевіряє цілісність даних після міграції'
    
    def add_arguments(self, parser):
        parser.add_argument('--detailed', action='store_true', help='Детальний звіт з списками')
    
    def handle(self, *args, **options):
        detailed = options['detailed']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('ЗВІТ ПЕРЕВІРКИ МІГРАЦІЇ'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        errors = []
        warnings = []
        info = []
        
        # 1. КАТЕГОРІЇ
        self.stdout.write(self.style.SUCCESS('1. КАТЕГОРІЇ'))
        total_categories = Category.objects.count()
        active_categories = Category.objects.filter(is_active=True).count()
        parent_categories = Category.objects.filter(parent__isnull=True).count()
        subcategories = Category.objects.filter(parent__isnull=False).count()
        
        self.stdout.write(f'   Всього категорій: {total_categories}')
        self.stdout.write(f'   - Активних: {active_categories}')
        self.stdout.write(f'   - Головних: {parent_categories}')
        self.stdout.write(f'   - Підкатегорій: {subcategories}')
        
        if parent_categories == 0:
            errors.append('Немає головних категорій')
        
        # Перевірка порожніх категорій (лише листових, без підкатегорій)
        empty_leaf_categories = Category.objects.filter(
            is_active=True,
            children__isnull=True  # Тільки категорії без підкатегорій
        ).annotate(
            products_count=Count('product', filter=Q(product__is_active=True))
        ).filter(products_count=0)
        
        if empty_leaf_categories.exists():
            warnings.append(f'{empty_leaf_categories.count()} порожніх категорій без підкатегорій')
            if detailed:
                self.stdout.write(self.style.WARNING('   Порожні категорії:'))
                for cat in empty_leaf_categories[:10]:
                    self.stdout.write(f'     - {cat.name}')
        
        # 2. ТОВАРИ
        self.stdout.write(self.style.SUCCESS('\n2. ТОВАРИ'))
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        
        self.stdout.write(f'   Всього товарів: {total_products}')
        self.stdout.write(f'   - Активних: {active_products}')
        
        if total_products == 0:
            errors.append('Немає товарів у БД')
        
        # Товари без SKU
        no_sku = Product.objects.filter(Q(sku='') | Q(sku__isnull=True))
        if no_sku.exists():
            errors.append(f'{no_sku.count()} товарів без SKU')
        
        # Дублікати SKU
        duplicate_skus = Product.objects.values('sku').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicate_skus.exists():
            errors.append(f'{duplicate_skus.count()} дублікатів SKU')
            if detailed:
                self.stdout.write(self.style.ERROR('   Дублікати SKU:'))
                for dup in duplicate_skus[:10]:
                    self.stdout.write(f'     - {dup["sku"]}: {dup["count"]} товарів')
        
        # Товари без категорій
        no_category = Product.objects.filter(category__isnull=True)
        if no_category.exists():
            errors.append(f'{no_category.count()} товарів без категорії')
        
        # Товари без опису
        no_description = Product.objects.filter(is_active=True).filter(
            Q(description='') | Q(description__isnull=True)
        )
        if no_description.exists():
            warnings.append(f'{no_description.count()} активних товарів без опису')
        
        # 3. ЦІНИ
        self.stdout.write(self.style.SUCCESS('\n3. ЦІНИ'))
        
        # Товари без ціни
        no_price = Product.objects.filter(
            Q(retail_price__isnull=True) | Q(retail_price__lte=0)
        )
        if no_price.exists():
            errors.append(f'{no_price.count()} товарів без роздрібної ціни або ціна ≤ 0')
        
        # Акційні ціни більші за роздрібні
        wrong_sale_price = Product.objects.filter(
            is_sale=True, 
            sale_price__gte=F('retail_price')
        )
        if wrong_sale_price.exists():
            errors.append(f'{wrong_sale_price.count()} товарів з акційною ціною ≥ роздрібної')
        
        # Статистика цін
        price_stats = Product.objects.filter(is_active=True).aggregate(
            min_price=Min('retail_price'),
            max_price=Max('retail_price'),
            avg_price=Avg('retail_price')
        )
        
        self.stdout.write(f'   Діапазон цін: {price_stats["min_price"]}₴ - {price_stats["max_price"]}₴')
        self.stdout.write(f'   Середня ціна: {price_stats["avg_price"]:.2f}₴' if price_stats["avg_price"] else '   Середня ціна: N/A')
        
        # Акційні товари
        sale_products = Product.objects.filter(is_active=True, is_sale=True)
        self.stdout.write(f'   Акційних товарів: {sale_products.count()}')
        
        # 4. ЗОБРАЖЕННЯ
        self.stdout.write(self.style.SUCCESS('\n4. ЗОБРАЖЕННЯ'))
        
        total_images = ProductImage.objects.count()
        products_with_images = Product.objects.filter(
            is_active=True, images__isnull=False
        ).distinct().count()
        products_without_images = Product.objects.filter(
            is_active=True, images__isnull=True
        ).distinct().count()
        
        self.stdout.write(f'   Всього зображень: {total_images}')
        self.stdout.write(f'   Товарів з фото: {products_with_images}')
        self.stdout.write(f'   Товарів без фото (плейсхолдер 📦): {products_without_images}')
        
        if active_products > 0:
            coverage = (products_with_images / active_products) * 100
            self.stdout.write(f'   Покриття реальними фото: {coverage:.1f}%')
            self.stdout.write(self.style.WARNING(f'   ⓘ Товари без фото показують плейсхолдер 📦 на сайті'))
            
            if coverage < 10:
                errors.append(f'Критично мало товарів мають зображення ({coverage:.1f}%)')
            elif coverage < 50:
                warnings.append(f'Бажано додати більше зображень (покриття: {coverage:.1f}%)')
        
        # Товари без головного зображення
        products_no_main_image = Product.objects.filter(
            is_active=True,
            images__isnull=False
        ).exclude(
            images__is_main=True
        ).distinct()
        
        if products_no_main_image.exists():
            warnings.append(f'{products_no_main_image.count()} товарів без головного зображення')
        
        # 5. СКЛАД
        self.stdout.write(self.style.SUCCESS('\n5. СКЛАД'))
        
        in_stock = Product.objects.filter(is_active=True, stock__gt=0).count()
        out_of_stock = Product.objects.filter(is_active=True, stock=0).count()
        
        self.stdout.write(f'   В наявності: {in_stock}')
        self.stdout.write(f'   Немає на складі: {out_of_stock}')
        
        if active_products > 0:
            in_stock_percent = (in_stock / active_products) * 100
            self.stdout.write(f'   % в наявності: {in_stock_percent:.1f}%')
        
        # Активні товари без наявності
        active_no_stock = Product.objects.filter(is_active=True, stock=0)
        if active_no_stock.count() > active_products * 0.5:
            warnings.append(f'Більше 50% активних товарів без наявності')
        
        # 6. СТАТУСИ ТА БЕЙДЖІ
        self.stdout.write(self.style.SUCCESS('\n6. СТАТУСИ ТА БЕЙДЖІ'))
        
        top_products = Product.objects.filter(is_active=True, is_top=True).count()
        new_products = Product.objects.filter(is_active=True, is_new=True).count()
        featured_products = Product.objects.filter(is_active=True, is_featured=True).count()
        
        self.stdout.write(f'   ХІТ (is_top): {top_products}')
        self.stdout.write(f'   НОВИНКИ (is_new): {new_products}')
        self.stdout.write(f'   РЕКОМЕНДОВАНІ (is_featured): {featured_products}')
        self.stdout.write(f'   АКЦІЙНІ (is_sale): {sale_products.count()}')
        
        # ПІДСУМОК
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('ПІДСУМОК'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        if errors:
            self.stdout.write(self.style.ERROR(f'❌ КРИТИЧНІ ПОМИЛКИ ({len(errors)}):'))
            for error in errors:
                self.stdout.write(self.style.ERROR(f'   - {error}'))
            self.stdout.write('')
        
        if warnings:
            self.stdout.write(self.style.WARNING(f'⚠️  ПОПЕРЕДЖЕННЯ ({len(warnings)}):'))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'   - {warning}'))
            self.stdout.write('')
        
        if not errors and not warnings:
            self.stdout.write(self.style.SUCCESS('✅ Всі перевірки пройдені успішно!'))
        elif not errors:
            self.stdout.write(self.style.SUCCESS('✅ Критичних помилок немає'))
            self.stdout.write(self.style.WARNING('⚠️  Є попередження, рекомендується виправити'))
        else:
            self.stdout.write(self.style.ERROR('❌ Виявлені критичні помилки, потрібно виправити'))
        
        self.stdout.write('')

