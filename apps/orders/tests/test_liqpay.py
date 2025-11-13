"""
Тести для оплати через LiqPay
"""
import json
import base64
import hashlib
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.orders.models import Order, OrderItem, PendingPayment
from apps.products.models import Product, Category
from apps.cart.cart import Cart

User = get_user_model()


class LiqPayPaymentTest(TestCase):
    """Тести оплати через LiqPay"""
    
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name='Test Category', slug='test-category')
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            retail_price=Decimal('100.00'),
            wholesale_price=Decimal('80.00'),
            stock=10
        )
        
        self.order_data = {
            'first_name': 'Іван',
            'last_name': 'Тестовий',
            'middle_name': 'Петрович',
            'email': 'test@example.com',
            'phone': '+380501234567',
            'delivery_method': 'nova_poshta',
            'delivery_city': 'Київ',
            'delivery_address': 'Відділення №1',
            'payment_method': 'liqpay',
            'notes': 'Test order'
        }
    
    def test_pending_payment_creation(self):
        """Тест створення pending платежу"""
        session = self.client.session
        session['cart'] = {
            str(self.product.id): {
                'quantity': 2,
                'price': float(self.product.retail_price)
            }
        }
        session.save()
        
        response = self.client.post(reverse('orders:create'), self.order_data)
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PendingPayment.objects.exists())
        pending = PendingPayment.objects.first()
        self.assertFalse(pending.is_processed)
        self.assertEqual(pending.order_data['email'], 'test@example.com')
    
    def test_liqpay_payment_pending_page(self):
        """Тест сторінки очікування оплати"""
        pending_payment = PendingPayment.objects.create(
            transaction_ref='temp_123456',
            order_data=self.order_data | {
                'total': '200.00',
                'subtotal': '200.00',
                'discount': '0.00',
                'order_items': [{
                    'product_id': self.product.id,
                    'quantity': 2,
                    'price': '100.00'
                }]
            }
        )
        
        session = self.client.session
        session['pending_transaction_ref'] = 'temp_123456'
        session.save()
        
        response = self.client.get(reverse('orders:liqpay_payment_pending'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Оплата замовлення')
        self.assertContains(response, 'test@example.com')
    
    def test_liqpay_callback_success(self):
        """Тест успішного callback від LiqPay"""
        pending_payment = PendingPayment.objects.create(
            transaction_ref='temp_123456',
            order_data=self.order_data | {
                'total': '200.00',
                'subtotal': '200.00',
                'discount': '0.00',
                'order_items': [{
                    'product_id': self.product.id,
                    'quantity': 2,
                    'price': '100.00'
                }],
                'user_id': None
            }
        )
        
        from django.conf import settings
        LIQPAY_PRIVATE_KEY = settings.LIQPAY_PRIVATE_KEY
        
        callback_data = {
            'order_id': 'temp_123456',
            'status': 'success',
            'transaction_id': '12345678'
        }
        
        data_json = json.dumps(callback_data)
        data = base64.b64encode(data_json.encode('utf-8')).decode('utf-8')
        sign_string = LIQPAY_PRIVATE_KEY + data + LIQPAY_PRIVATE_KEY
        signature = base64.b64encode(hashlib.sha1(sign_string.encode('utf-8')).digest()).decode('utf-8')
        
        response = self.client.post(
            reverse('orders:liqpay_callback'),
            {'data': data, 'signature': signature}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        pending_payment.refresh_from_db()
        self.assertTrue(pending_payment.is_processed)
        self.assertIsNotNone(pending_payment.created_order)
        
        order = pending_payment.created_order
        self.assertTrue(order.is_paid)
        self.assertEqual(order.email, 'test@example.com')
        self.assertEqual(order.items.count(), 1)
    
    def test_liqpay_callback_duplicate_prevention(self):
        """Тест захисту від дублюючих callback-ів"""
        pending_payment = PendingPayment.objects.create(
            transaction_ref='temp_123456',
            order_data=self.order_data | {
                'total': '200.00',
                'subtotal': '200.00',
                'discount': '0.00',
                'order_items': [{
                    'product_id': self.product.id,
                    'quantity': 2,
                    'price': '100.00'
                }],
                'user_id': None
            }
        )
        
        from django.conf import settings
        LIQPAY_PRIVATE_KEY = settings.LIQPAY_PRIVATE_KEY
        
        callback_data = {
            'order_id': 'temp_123456',
            'status': 'success',
            'transaction_id': '12345678'
        }
        
        data_json = json.dumps(callback_data)
        data = base64.b64encode(data_json.encode('utf-8')).decode('utf-8')
        sign_string = LIQPAY_PRIVATE_KEY + data + LIQPAY_PRIVATE_KEY
        signature = base64.b64encode(hashlib.sha1(sign_string.encode('utf-8')).digest()).decode('utf-8')
        
        self.client.post(
            reverse('orders:liqpay_callback'),
            {'data': data, 'signature': signature}
        )
        
        response = self.client.post(
            reverse('orders:liqpay_callback'),
            {'data': data, 'signature': signature}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data.get('message'), 'Already processed')
        
        self.assertEqual(Order.objects.count(), 1)
    
    def test_liqpay_callback_failed_payment(self):
        """Тест неуспішної оплати"""
        pending_payment = PendingPayment.objects.create(
            transaction_ref='temp_123456',
            order_data=self.order_data | {
                'total': '200.00',
                'subtotal': '200.00',
                'discount': '0.00',
                'order_items': [{
                    'product_id': self.product.id,
                    'quantity': 2,
                    'price': '100.00'
                }],
                'user_id': None
            }
        )
        
        from django.conf import settings
        LIQPAY_PRIVATE_KEY = settings.LIQPAY_PRIVATE_KEY
        
        callback_data = {
            'order_id': 'temp_123456',
            'status': 'failure',
            'transaction_id': '12345678'
        }
        
        data_json = json.dumps(callback_data)
        data = base64.b64encode(data_json.encode('utf-8')).decode('utf-8')
        sign_string = LIQPAY_PRIVATE_KEY + data + LIQPAY_PRIVATE_KEY
        signature = base64.b64encode(hashlib.sha1(sign_string.encode('utf-8')).digest()).decode('utf-8')
        
        response = self.client.post(
            reverse('orders:liqpay_callback'),
            {'data': data, 'signature': signature}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        
        pending_payment.refresh_from_db()
        self.assertTrue(pending_payment.is_processed)
        self.assertIsNone(pending_payment.created_order)
        
        self.assertEqual(Order.objects.count(), 0)
    
    def test_liqpay_callback_invalid_signature(self):
        """Тест невалідного підпису"""
        callback_data = {
            'order_id': 'temp_123456',
            'status': 'success',
            'transaction_id': '12345678'
        }
        
        data_json = json.dumps(callback_data)
        data = base64.b64encode(data_json.encode('utf-8')).decode('utf-8')
        invalid_signature = 'invalid_signature'
        
        response = self.client.post(
            reverse('orders:liqpay_callback'),
            {'data': data, 'signature': invalid_signature}
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['error'], 'Invalid signature')

