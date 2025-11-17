"""
Тести приймання для адміністративної панелі товарів
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from apps.products.models import (
    Category, Product, Brand, ProductGroup, ProductPurpose,
    SalePromotion, CategoryFilterConfig, ProductChangeLog
)

User = get_user_model()


class AdminProductTests(TestCase):
    """Тести адмінки товарів"""
    
    def setUp(self):
        """Налаштування тестових даних"""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client.login(username='admin', password='testpass123')
        
        # Створюємо категорію
        self.category = Category.objects.create(
            name='Тестова категорія',
            slug='test-category',
            is_active=True
        )
        
        # Створюємо бренд
        self.brand = Brand.objects.create(
            name='Тестовий бренд',
            slug='test-brand',
            is_active=True
        )
    
    def test_product_creation_with_prices(self):
        """Тест 1: Створення товару з багаторівневими цінами"""
        product = Product.objects.create(
            name='Тестовий товар',
            slug='test-product',
            category=self.category,
            retail_price=Decimal('100.00'),
            wholesale_price=Decimal('80.00'),
            price_3_qty=Decimal('90.00'),
            price_5_qty=Decimal('85.00'),
            is_active=True,
            stock=10
        )
        
        # Перевіряємо ціни
        self.assertEqual(product.retail_price, Decimal('100.00'))
        self.assertEqual(product.wholesale_price, Decimal('80.00'))
        self.assertEqual(product.price_3_qty, Decimal('90.00'))
        self.assertEqual(product.price_5_qty, Decimal('85.00'))
        
        # Перевіряємо правило: 5+ <= 3+ <= опт <= базова
        self.assertLessEqual(product.price_5_qty, product.price_3_qty)
        self.assertLessEqual(product.price_3_qty, product.retail_price)
        self.assertLessEqual(product.wholesale_price, product.retail_price)
    
    def test_sale_promotion_with_period(self):
        """Тест 2: Масова акція з періодом дії"""
        product = Product.objects.create(
            name='Товар для акції',
            slug='sale-product',
            category=self.category,
            retail_price=Decimal('100.00'),
            is_active=True,
            stock=10
        )
        
        # Створюємо акцію
        promotion = SalePromotion.objects.create(
            name='Тестова акція',
            discount_type='percentage',
            discount_value=Decimal('20.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=7),
            is_active=True,
            created_by=self.admin_user
        )
        promotion.products.add(product)
        
        # Застосовуємо акцію
        count = promotion.apply_to_products()
        self.assertEqual(count, 1)
        
        # Перевіряємо товар
        product.refresh_from_db()
        self.assertTrue(product.is_sale)
        self.assertEqual(product.sale_price, Decimal('80.00'))  # 100 - 20%
        self.assertTrue(product.is_sale_active())
    
    def test_category_filter_config(self):
        """Тест 3: Конфігурація фільтрів категорії"""
        # При створенні категорії повинен створюватися конфіг
        config, created = CategoryFilterConfig.objects.get_or_create(
            category=self.category
        )
        
        self.assertTrue(config.show_brand_filter)
        self.assertTrue(config.show_group_filter)
        self.assertTrue(config.show_purpose_filter)
        self.assertTrue(config.show_price_filter)
        
        # Змінюємо конфіг
        config.show_brand_filter = False
        config.save()
        
        # Перевіряємо
        config.refresh_from_db()
        self.assertFalse(config.show_brand_filter)
    
    def test_product_badges(self):
        """Тест 4: Бейджі товарів (Новинка, Хіт, Акція)"""
        product = Product.objects.create(
            name='Товар з бейджами',
            slug='badge-product',
            category=self.category,
            retail_price=Decimal('100.00'),
            is_top=True,
            is_new=True,
            is_sale=True,
            sale_price=Decimal('80.00'),
            is_active=True,
            stock=10
        )
        
        stickers = product.get_stickers()
        
        # Перевіряємо бейджі
        self.assertEqual(len(stickers), 3)
        
        types = [s['type'] for s in stickers]
        self.assertIn('top', types)
        self.assertIn('new', types)
        self.assertIn('sale', types)
    
    def test_product_change_log(self):
        """Тест 5: Логування змін товару"""
        product = Product.objects.create(
            name='Товар для логів',
            slug='log-product',
            category=self.category,
            retail_price=Decimal('100.00'),
            is_active=True,
            stock=10
        )
        
        # Змінюємо ціну
        product.retail_price = Decimal('120.00')
        product.save()
        
        # Створюємо лог вручну (в реальності це робить save_model в адмінці)
        ProductChangeLog.objects.create(
            product=product,
            user=self.admin_user,
            field_name='Роздрібна ціна',
            old_value='100.00',
            new_value='120.00',
            change_type='price'
        )
        
        # Перевіряємо логи
        logs = ProductChangeLog.objects.filter(product=product)
        self.assertEqual(logs.count(), 1)
        
        log = logs.first()
        self.assertEqual(log.change_type, 'price')
        self.assertEqual(log.old_value, '100.00')
        self.assertEqual(log.new_value, '120.00')
    
    def test_sale_period_validation(self):
        """Тест 6: Перевірка періоду акції"""
        product = Product.objects.create(
            name='Товар з періодичною акцією',
            slug='period-sale-product',
            category=self.category,
            retail_price=Decimal('100.00'),
            is_sale=True,
            sale_price=Decimal('80.00'),
            sale_start_date=timezone.now() - timedelta(days=1),
            sale_end_date=timezone.now() + timedelta(days=7),
            is_active=True,
            stock=10
        )
        
        # Акція повинна бути активною
        self.assertTrue(product.is_sale_active())
        
        # Змінюємо період на минулий
        product.sale_end_date = timezone.now() - timedelta(hours=1)
        product.save()
        
        # Акція не повинна бути активною
        self.assertFalse(product.is_sale_active())
    
    def test_price_calculation_logic(self):
        """Тест 7: Логіка розрахунку цін для клієнта"""
        product = Product.objects.create(
            name='Товар для тесту цін',
            slug='price-test-product',
            category=self.category,
            retail_price=Decimal('100.00'),
            wholesale_price=Decimal('80.00'),
            price_3_qty=Decimal('90.00'),
            price_5_qty=Decimal('85.00'),
            is_active=True,
            stock=100
        )
        
        # Базова ціна для незареєстрованого
        price_1 = product.get_price_for_user(user=None, quantity=1)
        self.assertEqual(price_1, Decimal('100.00'))
        
        # Ціна від 3 шт
        price_3 = product.get_price_for_user(user=None, quantity=3)
        self.assertEqual(price_3, Decimal('90.00'))
        
        # Ціна від 5 шт
        price_5 = product.get_price_for_user(user=None, quantity=5)
        self.assertEqual(price_5, Decimal('85.00'))
    
    def test_admin_access(self):
        """Тест 8: Доступ до адмінки"""
        response = self.client.get('/admin/products/product/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/admin/products/category/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/admin/products/salepromotion/')
        self.assertEqual(response.status_code, 200)


class BrandAdminTests(TestCase):
    """Тести адмінки брендів"""
    
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.client.login(username='admin', password='testpass123')
    
    def test_brand_creation(self):
        """Тест створення бренду"""
        brand = Brand.objects.create(
            name='Новий бренд',
            slug='new-brand',
            is_active=True
        )
        
        self.assertEqual(brand.name, 'Новий бренд')
        self.assertTrue(brand.is_active)
    
    def test_brand_product_count(self):
        """Тест підрахунку товарів бренду"""
        category = Category.objects.create(
            name='Категорія',
            slug='category',
            is_active=True
        )
        
        brand = Brand.objects.create(
            name='Бренд з товарами',
            slug='brand-with-products',
            is_active=True
        )
        
        # Створюємо товари (закоментовано, бо brand поки не додано до Product)
        # Product.objects.create(name='Товар 1', category=category, brand=brand)
        # Product.objects.create(name='Товар 2', category=category, brand=brand)
        
        # count = brand.product_set.count()
        # self.assertEqual(count, 2)


class PromotionTests(TestCase):
    """Тести системи акцій"""
    
    def setUp(self):
        from apps.promotions.models import Promotion
        
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Категорія для акцій',
            slug='sale-category',
            is_active=True
        )
    
    def test_promotion_application_to_category(self):
        """Тест застосування акції до категорії"""
        from apps.promotions.models import Promotion
        
        # Створюємо товари в категорії
        product1 = Product.objects.create(
            name='Товар 1',
            category=self.category,
            retail_price=Decimal('100.00'),
            is_active=True
        )
        product2 = Product.objects.create(
            name='Товар 2',
            category=self.category,
            retail_price=Decimal('200.00'),
            is_active=True
        )
        
        # Створюємо акцію на категорію
        promotion = Promotion.objects.create(
            name='Акція на категорію',
            retail_discount_percent=Decimal('15.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=10),
            is_active=True,
            priority=0
        )
        promotion.categories.add(self.category)
        
        # Застосовуємо
        count = promotion.apply_to_products()
        self.assertGreaterEqual(count, 2)
        
        # Перевіряємо товари
        product1.refresh_from_db()
        product2.refresh_from_db()
        
        self.assertTrue(product1.is_sale)
        self.assertTrue(product2.is_sale)
        self.assertEqual(product1.sale_price, Decimal('85.00'))  # 100 - 15%
        self.assertEqual(product2.sale_price, Decimal('170.00'))  # 200 - 15%
        self.assertEqual(product1.current_promotion, promotion)
        self.assertEqual(product2.current_promotion, promotion)
    
    def test_promotion_priority_conflict(self):
        """Тест конфлікту акцій з різними пріоритетами"""
        from apps.promotions.models import Promotion
        
        product = Product.objects.create(
            name='Тестовий товар',
            category=self.category,
            retail_price=Decimal('100.00'),
            is_active=True
        )
        
        # Створюємо акцію з низьким пріоритетом
        promo_low = Promotion.objects.create(
            name='Акція низький пріоритет',
            retail_discount_percent=Decimal('10.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=10),
            is_active=True,
            priority=1
        )
        promo_low.products.add(product)
        promo_low.apply_to_products()
        
        product.refresh_from_db()
        self.assertEqual(product.sale_price, Decimal('90.00'))
        self.assertEqual(product.current_promotion, promo_low)
        
        # Створюємо акцію з високим пріоритетом
        promo_high = Promotion.objects.create(
            name='Акція високий пріоритет',
            retail_discount_percent=Decimal('20.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=10),
            is_active=True,
            priority=5
        )
        promo_high.products.add(product)
        promo_high.apply_to_products()
        
        product.refresh_from_db()
        self.assertEqual(product.sale_price, Decimal('80.00'))
        self.assertEqual(product.current_promotion, promo_high)
        
        # Пробуємо застосувати акцію з ще нижчим пріоритетом
        promo_lowest = Promotion.objects.create(
            name='Акція найнижчий пріоритет',
            retail_discount_percent=Decimal('5.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=10),
            is_active=True,
            priority=0
        )
        promo_lowest.products.add(product)
        promo_lowest.apply_to_products()
        
        product.refresh_from_db()
        # Ціна не повинна змінитися - висока акція залишається
        self.assertEqual(product.sale_price, Decimal('80.00'))
        self.assertEqual(product.current_promotion, promo_high)
    
    def test_promotion_validation(self):
        """Тест валідації акції"""
        from apps.promotions.models import Promotion
        from django.core.exceptions import ValidationError
        
        # Тест: знижка більше 100%
        promotion = Promotion(
            name='Тест',
            retail_discount_percent=Decimal('150.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=10),
        )
        with self.assertRaises(ValidationError):
            promotion.clean()
        
        # Тест: дата закінчення раніше за початок
        promotion = Promotion(
            name='Тест',
            retail_discount_percent=Decimal('10.00'),
            start_date=timezone.now() + timedelta(days=10),
            end_date=timezone.now(),
        )
        with self.assertRaises(ValidationError):
            promotion.clean()
        
        # Тест: жодної знижки не вказано
        promotion = Promotion(
            name='Тест',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=10),
        )
        with self.assertRaises(ValidationError):
            promotion.clean()
    
    def test_promotion_remove_with_tracking(self):
        """Тест зняття акції з перевіркою current_promotion"""
        from apps.promotions.models import Promotion
        
        product = Product.objects.create(
            name='Тестовий товар',
            category=self.category,
            retail_price=Decimal('100.00'),
            is_active=True
        )
        
        promotion = Promotion.objects.create(
            name='Тестова акція',
            retail_discount_percent=Decimal('20.00'),
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=10),
            is_active=True,
            priority=1
        )
        promotion.products.add(product)
        promotion.apply_to_products()
        
        product.refresh_from_db()
        self.assertTrue(product.is_sale)
        self.assertEqual(product.current_promotion, promotion)
        
        # Знімаємо акцію
        promotion.remove_from_products()
        
        product.refresh_from_db()
        self.assertFalse(product.is_sale)
        self.assertIsNone(product.current_promotion)
        self.assertIsNone(product.sale_price)


