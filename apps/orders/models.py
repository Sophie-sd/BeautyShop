"""
Моделі замовлень
"""
from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from apps.products.models import Product


class PendingPayment(models.Model):
    """Тимчасове зберігання даних pending платежів для захисту від дублів"""
    
    transaction_ref = models.CharField('Transaction ID', max_length=100, unique=True, db_index=True)
    order_data = models.JSONField('Дані замовлення')
    is_processed = models.BooleanField('Оброблено', default=False, db_index=True)
    created_order = models.ForeignKey('Order', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Створене замовлення')
    created_at = models.DateTimeField('Створено', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Pending платіж'
        verbose_name_plural = 'Pending платежі'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_ref', 'is_processed']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Pending {self.transaction_ref} - {'Оброблено' if self.is_processed else 'Очікує'}"


class Order(models.Model):
    """Замовлення"""
    
    STATUS_CHOICES = [
        ('pending', 'Очікує підтвердження'),
        ('confirmed', 'Підтверджено'),
        ('shipped', 'Відправлено'),
        ('delivered', 'Доставлено'),
        ('completed', 'Завершено'),
        ('cancelled', 'Скасовано'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Готівка при отриманні'),
        ('card', 'Оплата карткою'),
        ('bank_transfer', 'Банківський переказ'),
        ('liqpay', 'LiqPay'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('nova_poshta', 'Нова Пошта'),
        ('ukrposhta', 'Укрпошта'),
        ('pickup', 'Самовивіз'),
    ]
    
    DELIVERY_TYPE_CHOICES = [
        ('warehouse', 'Відділення'),
        ('postomat', 'Поштомат'),
    ]
    
    # Основна інформація
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        verbose_name='Користувач',
        null=True,
        blank=True
    )
    order_number = models.CharField('Номер замовлення', max_length=20, unique=True, blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Контактні дані
    first_name = models.CharField('Ім\'я', max_length=100)
    last_name = models.CharField('Прізвище', max_length=100)
    middle_name = models.CharField('По-батькові', max_length=100, blank=True, default='')
    email = models.EmailField('Email')
    phone = models.CharField('Телефон', max_length=20)
    
    # Доставка
    delivery_method = models.CharField('Спосіб доставки', max_length=20, choices=DELIVERY_METHOD_CHOICES)
    delivery_city = models.CharField('Місто доставки', max_length=100)
    delivery_address = models.TextField('Адреса доставки')
    delivery_cost = models.DecimalField('Вартість доставки', max_digits=10, decimal_places=2, default=0)
    
    # Дані Нової Пошти
    np_city_ref = models.CharField('Ref міста НП', max_length=100, blank=True, default='')
    np_warehouse_ref = models.CharField('Ref відділення НП', max_length=100, blank=True, default='')
    delivery_type = models.CharField('Тип доставки', max_length=20, choices=DELIVERY_TYPE_CHOICES, blank=True, default='')
    
    # Оплата
    payment_method = models.CharField('Спосіб оплати', max_length=20, choices=PAYMENT_METHOD_CHOICES)
    is_paid = models.BooleanField('Оплачено', default=False)
    payment_date = models.DateTimeField('Дата оплати', null=True, blank=True)
    
    # Ціни
    subtotal = models.DecimalField('Сума товарів', max_digits=10, decimal_places=2)
    discount = models.DecimalField('Знижка', max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField('Загальна сума', max_digits=10, decimal_places=2)
    
    # Промокод та детальна розшифровка знижок
    promo_code_used = models.CharField(
        'Використаний промокод',
        max_length=50,
        blank=True,
        default='',
        help_text='Промокод, який був застосований до замовлення'
    )
    discount_breakdown = models.JSONField(
        'Розшифровка знижок',
        default=dict,
        blank=True,
        help_text='Детальна інформація про всі застосовані знижки'
    )
    
    # Додаткові поля
    notes = models.TextField('Примітки до замовлення', blank=True)
    admin_notes = models.TextField('Примітки адміна', blank=True)
    
    # Дати
    created_at = models.DateTimeField('Дата створення', auto_now_add=True)
    updated_at = models.DateTimeField('Останнє оновлення', auto_now=True)
    
    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """Зберігає замовлення та генерує номер"""
        # Якщо це нове замовлення і немає номеру - генеруємо тимчасовий
        if not self.pk and not self.order_number:
            # Генеруємо унікальний номер на основі часу для уникнення конфліктів
            import time
            temp_number = f"TEMP-{int(time.time() * 1000)}"
            self.order_number = temp_number
        
        # Зберігаємо об'єкт
        super().save(*args, **kwargs)
        
        # Після збереження генеруємо фінальний номер
        if self.order_number.startswith('TEMP-'):
            self.order_number = f"BS{self.id:06d}"
            super().save(update_fields=['order_number'])
    
    def get_total_cost(self):
        """Повертає загальну вартість замовлення"""
        return self.subtotal + self.delivery_cost - self.discount
    
    def get_customer_name(self):
        """Повертає повне ім'я клієнта"""
        if self.middle_name:
            return f"{self.first_name} {self.last_name} {self.middle_name}"
        return f"{self.first_name} {self.last_name}"
    
    def can_be_cancelled(self):
        """Чи може бути скасовано замовлення"""
        return self.status in ['pending', 'confirmed']
    
    def get_discount_breakdown_display(self):
        """Повертає форматовану HTML-розшифровку знижок для відображення в адмінці"""
        from django.utils.safestring import mark_safe
        
        if not self.discount_breakdown or not isinstance(self.discount_breakdown, dict):
            return mark_safe('<p style="color: #718096;">Детальна інформація про знижки відсутня (замовлення створене до впровадження функції)</p>')
        
        summary = self.discount_breakdown.get('summary', {})
        
        # Перевірка чи є взагалі знижки
        total_discount = Decimal('0')
        price_grad_3 = Decimal(str(summary.get('price_gradation_3_discount', 0)))
        price_grad_5 = Decimal(str(summary.get('price_gradation_5_discount', 0)))
        wholesale = Decimal(str(summary.get('wholesale_discount', 0)))
        promotion = Decimal(str(summary.get('promotion_discount', 0)))
        promo_code = Decimal(str(summary.get('promo_code_discount', 0)))
        
        total_discount = price_grad_3 + price_grad_5 + wholesale + promotion + promo_code
        
        if total_discount == 0:
            return mark_safe('<p style="color: #718096;">Знижки не застосовувалися</p>')
        
        html = '<div style="background: #f0f9ff; padding: 15px; border-radius: 8px; border-left: 4px solid #0ea5e9;">'
        html += '<div style="font-weight: 600; color: #0c4a6e; margin-bottom: 12px; font-size: 14px;">📊 Застосовані знижки:</div>'
        
        # Градація цін від 3 шт
        if price_grad_3 > 0:
            html += f'''
            <div style="margin-bottom: 8px; display: flex; align-items: center;">
                <span style="font-size: 18px; margin-right: 8px;">💰</span>
                <span style="color: #047857; font-weight: 500;">Градація цін від 3 шт:</span>
                <span style="margin-left: auto; color: #dc2626; font-weight: 600;">-{float(price_grad_3):.2f} ₴</span>
            </div>
            '''
        
        # Градація цін від 5 шт
        if price_grad_5 > 0:
            html += f'''
            <div style="margin-bottom: 8px; display: flex; align-items: center;">
                <span style="font-size: 18px; margin-right: 8px;">💰</span>
                <span style="color: #047857; font-weight: 500;">Градація цін від 5 шт:</span>
                <span style="margin-left: auto; color: #dc2626; font-weight: 600;">-{float(price_grad_5):.2f} ₴</span>
            </div>
            '''
        
        # Оптова ціна
        if wholesale > 0:
            html += f'''
            <div style="margin-bottom: 8px; display: flex; align-items: center;">
                <span style="font-size: 18px; margin-right: 8px;">🏪</span>
                <span style="color: #1e40af; font-weight: 500;">Оптова ціна:</span>
                <span style="margin-left: auto; color: #dc2626; font-weight: 600;">-{float(wholesale):.2f} ₴</span>
            </div>
            '''
        
        # Акційні товари
        if promotion > 0:
            html += f'''
            <div style="margin-bottom: 8px; display: flex; align-items: center;">
                <span style="font-size: 18px; margin-right: 8px;">🎁</span>
                <span style="color: #c2410c; font-weight: 500;">Акційні товари:</span>
                <span style="margin-left: auto; color: #dc2626; font-weight: 600;">-{float(promotion):.2f} ₴</span>
            </div>
            '''
        
        # Промокод
        if promo_code > 0:
            promo_info = self.discount_breakdown.get('promo_code', {})
            promo_code_name = promo_info.get('code', self.promo_code_used or 'невідомий')
            html += f'''
            <div style="margin-bottom: 8px; display: flex; align-items: center;">
                <span style="font-size: 18px; margin-right: 8px;">🎟️</span>
                <span style="color: #7c3aed; font-weight: 500;">Промокод "{promo_code_name}":</span>
                <span style="margin-left: auto; color: #dc2626; font-weight: 600;">-{float(promo_code):.2f} ₴</span>
            </div>
            '''
        
        # Підсумок
        html += f'''
        <div style="margin-top: 12px; padding-top: 12px; border-top: 2px solid #bae6fd; display: flex; align-items: center;">
            <span style="color: #0c4a6e; font-weight: 600;">Всього знижок:</span>
            <span style="margin-left: auto; color: #dc2626; font-weight: 700; font-size: 16px;">-{float(total_discount):.2f} ₴</span>
        </div>
        '''
        
        html += '</div>'
        return mark_safe(html)
    
    def __str__(self):
        return f"Замовлення #{self.order_number} - {self.get_customer_name()}"


class OrderItem(models.Model):
    """Товар в замовленні"""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='Товар')
    quantity = models.PositiveIntegerField('Кількість')
    price = models.DecimalField('Ціна за одиницю', max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'Товар в замовленні'
        verbose_name_plural = 'Товари в замовленні'
    
    def get_cost(self):
        """Повертає вартість позиції"""
        return self.price * self.quantity
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class Newsletter(models.Model):
    """Підписка на розсилку"""
    
    email = models.EmailField('Email', unique=True)
    name = models.CharField('Ім\'я', max_length=200, blank=True)
    is_active = models.BooleanField('Активна підписка', default=True)
    created_at = models.DateTimeField('Дата підписки', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Підписка на розсилку'
        verbose_name_plural = 'Підписки на розсилку'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email


class RetailClient(Order):
    """Proxy модель для роздрібних клієнтів (гостьові замовлення)"""
    
    class Meta:
        proxy = True
        verbose_name = 'Роздрібний клієнт'
        verbose_name_plural = 'Роздрібні клієнти'


class EmailCampaign(models.Model):
    """Email розсилка"""
    
    STATUS_CHOICES = [
        ('draft', 'Чернетка'),
        ('scheduled', 'Заплановано'),
        ('sending', 'Відправляється'),
        ('sent', 'Відправлено'),
        ('failed', 'Помилка'),
    ]
    
    RECIPIENT_CHOICES = [
        ('newsletter', 'Підписники розсилки'),
        ('wholesale', 'Оптові клієнти'),
        ('retail', 'Роздрібні клієнти'),
    ]
    
    name = models.CharField('Назва розсилки', max_length=255)
    subject = models.CharField('Тема листа', max_length=255)
    content = models.TextField('Контент листа')
    image = models.ImageField('Зображення', upload_to='email_campaigns/', blank=True, null=True)
    
    recipients = models.JSONField('Отримувачі', default=list, help_text='Список типів отримувачів')
    
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField('Час відправки', null=True, blank=True)
    
    sent_count = models.PositiveIntegerField('Відправлено', default=0)
    failed_count = models.PositiveIntegerField('Помилок', default=0)
    
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)
    sent_at = models.DateTimeField('Відправлено', null=True, blank=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Створив'
    )
    
    class Meta:
        verbose_name = 'Email розсилка'
        verbose_name_plural = 'Email розсилки'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def get_recipients_list(self):
        """Отримати список email адрес для відправки (унікальні, без дублювання)"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        emails = set()
        
        for recipient_type in self.recipients:
            if recipient_type == 'newsletter':
                emails.update(
                    Newsletter.objects.filter(
                        is_active=True,
                        email__isnull=False
                    ).exclude(email='').values_list('email', flat=True)
                )
            elif recipient_type == 'wholesale':
                emails.update(
                    User.objects.filter(
                        is_wholesale=True,
                        email_verified=True,
                        is_staff=False,
                        is_superuser=False,
                        email__isnull=False
                    ).exclude(email='').values_list('email', flat=True)
                )
            elif recipient_type == 'retail':
                emails.update(
                    Order.objects.filter(
                        user__isnull=True,
                        email__isnull=False
                    ).exclude(email='').values_list('email', flat=True).distinct()
                )
        
        admin_emails = set(
            User.objects.filter(
                is_staff=True
            ).values_list('email', flat=True)
        ) | set(
            User.objects.filter(
                is_superuser=True
            ).values_list('email', flat=True)
        )
        
        emails = emails - admin_emails
        
        return list(emails)
    
    def send_campaign(self):
        """Відправка розсилки"""
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        
        if self.status not in ['draft', 'scheduled']:
            return False
        
        self.status = 'sending'
        self.save(update_fields=['status'])
        
        recipients = self.get_recipients_list()
        sent = 0
        failed = 0
        
        for email in recipients:
            try:
                html_content = render_to_string('emails/campaign.html', {
                    'campaign': self,
                    'email': email,
                })
                
                msg = EmailMultiAlternatives(
                    subject=self.subject,
                    body=self.content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                sent += 1
            except Exception as e:
                failed += 1
                print(f"Помилка відправки на {email}: {e}")
        
        self.sent_count = sent
        self.failed_count = failed
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['sent_count', 'failed_count', 'status', 'sent_at'])
        
        return True
