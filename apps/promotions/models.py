"""
Моделі акцій та промокодів
"""
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Promotion(models.Model):
    """Акція з можливістю встановлення різних акційних цін"""
    
    name = models.CharField('Назва акції', max_length=100, help_text='Буде відображатися на бейджі товару')
    description = models.TextField('Опис', blank=True)
    
    products = models.ManyToManyField(
        'products.Product',
        related_name='active_promotions',
        verbose_name='Товари',
        blank=True
    )
    
    categories = models.ManyToManyField(
        'products.Category',
        related_name='active_promotions',
        verbose_name='Категорії',
        blank=True,
        help_text='Застосувати акцію до всіх товарів цих категорій'
    )
    
    retail_discount_percent = models.DecimalField(
        'Знижка для роздрібних (%)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Відсоток знижки на роздрібну ціну'
    )
    
    wholesale_discount_percent = models.DecimalField(
        'Знижка для оптових (%)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Відсоток знижки на оптову ціну'
    )
    
    qty3_discount_percent = models.DecimalField(
        'Знижка від 3 шт (%)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Відсоток знижки на ціну від 3 шт'
    )
    
    qty5_discount_percent = models.DecimalField(
        'Знижка від 5 шт (%)',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Відсоток знижки на ціну від 5 шт'
    )
    
    start_date = models.DateTimeField('Дата початку')
    end_date = models.DateTimeField('Дата закінчення')
    
    is_active = models.BooleanField('Активна', default=True)
    priority = models.PositiveIntegerField('Пріоритет', default=0, help_text='Чим більше число, тим вищий пріоритет')
    
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Акція'
        verbose_name_plural = 'Акції'
        ordering = ['-priority', '-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')})"
    
    def is_valid(self):
        """Перевіряє чи дійсна акція зараз"""
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    def get_affected_products(self):
        """Повертає всі товари що підпадають під акцію"""
        from apps.products.models import Product
        
        products = set(self.products.filter(is_active=True))
        
        for category in self.categories.all():
            category_products = Product.objects.filter(category=category, is_active=True)
            products.update(category_products)
        
        return list(products)
    
    def apply_to_products(self):
        """Застосовує акцію до всіх товарів"""
        products = self.get_affected_products()
        count = 0
        
        for product in products:
            updated = False
            
            # Застосовуємо знижку на роздрібну ціну
            if self.retail_discount_percent and product.retail_price:
                discount = product.retail_price * (Decimal(str(self.retail_discount_percent)) / Decimal('100'))
                product.sale_price = product.retail_price - discount
                updated = True
            
            # Застосовуємо знижку на оптову ціну
            if self.wholesale_discount_percent and product.wholesale_price:
                discount = product.wholesale_price * (Decimal(str(self.wholesale_discount_percent)) / Decimal('100'))
                product.sale_wholesale_price = product.wholesale_price - discount
                updated = True
            
            # Застосовуємо знижку на ціну від 3 шт
            if self.qty3_discount_percent and product.price_3_qty:
                discount = product.price_3_qty * (Decimal(str(self.qty3_discount_percent)) / Decimal('100'))
                product.sale_price_3_qty = product.price_3_qty - discount
                updated = True
            
            # Застосовуємо знижку на ціну від 5 шт
            if self.qty5_discount_percent and product.price_5_qty:
                discount = product.price_5_qty * (Decimal(str(self.qty5_discount_percent)) / Decimal('100'))
                product.sale_price_5_qty = product.price_5_qty - discount
                updated = True
            
            if updated:
                product.is_sale = True
                product.sale_start_date = self.start_date
                product.sale_end_date = self.end_date
                product.active_promotion_name = self.name
                product.save()
                count += 1
        
        return count
    
    def remove_from_products(self):
        """Видаляє акцію з товарів"""
        products = self.get_affected_products()
        count = 0
        
        for product in products:
            if product.is_sale:
                product.is_sale = False
                product.sale_price = None
                product.sale_wholesale_price = None
                product.sale_price_3_qty = None
                product.sale_price_5_qty = None
                product.sale_start_date = None
                product.sale_end_date = None
                product.active_promotion_name = ''
                product.save()
                count += 1
        
        return count


class PromoCode(models.Model):
    """Промокоди для знижок"""
    
    code = models.CharField('Код', max_length=50, unique=True, help_text='Промокод для введення користувачем')
    
    discount_type = models.CharField(
        'Тип знижки',
        max_length=20,
        choices=[
            ('percentage', 'Відсоток'),
            ('fixed', 'Фіксована сума'),
        ],
        default='percentage'
    )
    
    discount_value = models.DecimalField(
        'Розмір знижки',
        max_digits=10,
        decimal_places=2,
        help_text='Відсоток або сума в гривнях'
    )
    
    min_order_amount = models.DecimalField(
        'Мінімальна сума замовлення',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Мінімальна сума для застосування промокоду'
    )
    
    max_uses = models.PositiveIntegerField(
        'Максимум використань',
        null=True,
        blank=True,
        help_text='Залиште порожнім для необмеженої кількості'
    )
    
    used_count = models.PositiveIntegerField('Використано разів', default=0, editable=False)
    
    start_date = models.DateTimeField('Дата початку')
    end_date = models.DateTimeField('Дата закінчення')
    
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоди'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} (-{self.discount_value}{'%' if self.discount_type == 'percentage' else '₴'})"
    
    def is_valid(self):
        """Перевіряє чи дійсний промокод"""
        now = timezone.now()
        
        if now < self.start_date:
            return False, "Промокод ще не активний"
        
        if now > self.end_date:
            return False, "Термін дії промокоду закінчився"
        
        if self.max_uses and self.used_count >= self.max_uses:
            return False, "Промокод вичерпано"
        
        return True, "OK"
    
    def apply_discount(self, order_amount):
        """Розраховує знижку для суми замовлення"""
        is_valid, message = self.is_valid()
        if not is_valid:
            return 0, message
        
        if self.min_order_amount and order_amount < self.min_order_amount:
            return 0, f"Мінімальна сума замовлення {self.min_order_amount} ₴"
        
        if self.discount_type == 'percentage':
            discount = order_amount * (self.discount_value / 100)
        else:
            discount = self.discount_value
        
        return min(discount, order_amount), "OK"

