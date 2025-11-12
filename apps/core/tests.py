"""
Smoke тести для критичних флоу Beauty Shop
"""
from django.test import TestCase, Client
from django.urls import reverse
from apps.products.models import Product, Category
from apps.users.models import CustomUser


class SmokeTests(TestCase):
    """Швидкі smoke-тести для критичних флоу"""
    
    def setUp(self):
        """Налаштування тестових даних"""
        self.client = Client()
        
        # Створюємо категорію
        self.category = Category.objects.create(
            name='Тестова категорія',
            slug='test-category',
            is_active=True
        )
        
        # Створюємо товар
        self.product = Product.objects.create(
            name='Тестовий товар',
            slug='test-product',
            category=self.category,
            retail_price=100.00,
            stock=10,
            is_active=True
        )
        
        # Створюємо користувача
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            first_name='Тест',
            last_name='Користувач',
            is_active=True
        )
    
    def test_homepage_loads(self):
        """Тест: головна сторінка завантажується"""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beauty Shop')
    
    def test_category_page_loads(self):
        """Тест: сторінка категорії завантажується"""
        response = self.client.get(
            reverse('products:category', kwargs={'slug': self.category.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)
    
    def test_product_detail_loads(self):
        """Тест: сторінка товару завантажується"""
        response = self.client.get(
            reverse('products:detail', kwargs={'slug': self.product.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
    
    def test_search_functionality(self):
        """Тест: пошук працює"""
        response = self.client.get(reverse('core:search'), {'q': 'Тестовий'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product.name)
    
    def test_add_to_cart(self):
        """Тест: додавання товару в кошик"""
        response = self.client.post(
            reverse('cart:add', kwargs={'product_id': self.product.id}),
            {'quantity': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
    
    def test_cart_page_loads(self):
        """Тест: сторінка кошика завантажується"""
        response = self.client.get(reverse('cart:detail'))
        self.assertEqual(response.status_code, 200)
    
    def test_wishlist_toggle(self):
        """Тест: додавання в список бажань"""
        response = self.client.post(
            reverse('wishlist:toggle', kwargs={'product_id': self.product.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
    
    def test_user_login_page(self):
        """Тест: сторінка входу завантажується"""
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)
    
    def test_user_registration_page(self):
        """Тест: сторінка реєстрації завантажується"""
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
    
    def test_sale_products_page(self):
        """Тест: сторінка акцій завантажується"""
        response = self.client.get(reverse('products:sale'))
        self.assertEqual(response.status_code, 200)


class SecurityTests(TestCase):
    """Тести безпеки"""
    
    def setUp(self):
        self.client = Client()
    
    def test_security_headers_on_homepage(self):
        """Тест: security headers присутні на головній"""
        response = self.client.get(reverse('core:home'))
        
        # Перевіряємо основні security headers
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
    
    def test_private_pages_no_cache(self):
        """Тест: приватні сторінки не кешуються"""
        # Створюємо користувача і логінимось
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            is_active=True
        )
        self.client.login(username='test@example.com', password='TestPass123!')
        
        # Перевіряємо Cache-Control на сторінці профілю
        response = self.client.get(reverse('users:profile'))
        cache_control = response.get('Cache-Control', '')
        
        # Має містити no-store для приватних сторінок
        self.assertIn('no-store', cache_control.lower())


class PerformanceTests(TestCase):
    """Тести продуктивності (базові)"""
    
    def setUp(self):
        self.client = Client()
        
        # Створюємо категорію
        self.category = Category.objects.create(
            name='Тестова категорія',
            slug='test-category',
            is_active=True
        )
        
        # Створюємо 20 товарів
        for i in range(20):
            Product.objects.create(
                name=f'Товар {i}',
                slug=f'product-{i}',
                category=self.category,
                retail_price=100.00,
                stock=10,
                is_active=True
            )
    
    def test_category_page_query_count(self):
        """Тест: кількість запитів на сторінці категорії"""
        from django.test.utils import override_settings
        from django.db import connection
        from django.test import override_settings
        
        with self.assertNumQueries(6):  # Оптимізовано: має бути < 10 запитів
            response = self.client.get(
                reverse('products:category', kwargs={'slug': self.category.slug})
            )
            self.assertEqual(response.status_code, 200)

