"""
Моделі замовлень
"""
from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from apps.products.models import Product


class Order(models.Model):
    """Замовлення"""
    
    STATUS_CHOICES = [
        ('pending', 'Очікує підтвердження'),
        ('confirmed', 'Підтверджено'),
        ('processing', 'В обробці'),
        ('shipped', 'Відправлено'),
        ('delivered', 'Доставлено'),
        ('cancelled', 'Скасовано'),
        ('completed', 'Завершено'),
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
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and not self.order_number:
            self.order_number = f"BS{self.id:06d}"
            super().save(update_fields=['order_number'])
    
    def get_total_cost(self):
        """Повертає загальну вартість замовлення"""
        return self.subtotal + self.delivery_cost - self.discount
    
    def get_customer_name(self):
        """Повертає повне ім'я клієнта"""
        return f"{self.first_name} {self.last_name}"
    
    def can_be_cancelled(self):
        """Чи може бути скасовано замовлення"""
        return self.status in ['pending', 'confirmed']
    
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


class Promotion(models.Model):
    """Акції та промокоди"""
    
    name = models.CharField('Назва акції', max_length=200)
    code = models.CharField('Промокод', max_length=50, unique=True, blank=True)
    discount_type = models.CharField('Тип знижки', max_length=20, choices=[
        ('percentage', 'Відсоток'),
        ('fixed', 'Фіксована сума'),
        ('free_shipping', 'Безкоштовна доставка'),
    ])
    discount_value = models.DecimalField('Розмір знижки', max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField('Мінімальна сума замовлення', max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField('Максимальна кількість використань', null=True, blank=True)
    uses_count = models.PositiveIntegerField('Кількість використань', default=0)
    
    is_active = models.BooleanField('Активна', default=True)
    start_date = models.DateTimeField('Дата початку')
    end_date = models.DateTimeField('Дата закінчення')
    
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Акція'
        verbose_name_plural = 'Акції'
        ordering = ['-created_at']
    
    def is_valid(self):
        """Перевіряє чи дійсна акція"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if now < self.start_date or now > self.end_date:
            return False
        
        if self.max_uses and self.uses_count >= self.max_uses:
            return False
        
        return True
    
    def apply_discount(self, order_total):
        """Застосовує знижку до суми замовлення"""
        if order_total < self.min_order_amount:
            return 0
        
        if self.discount_type == 'percentage':
            return order_total * (self.discount_value / 100)
        elif self.discount_type == 'fixed':
            return min(self.discount_value, order_total)
        
        return 0
    
    def __str__(self):
        return self.name


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
