"""
Моделі товарів та категорій з підтримкою оптових цін
"""
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from decimal import Decimal
from PIL import Image
import os
import time


class Brand(models.Model):
    """Бренди товарів"""
    
    name = models.CharField('Назва бренду', max_length=100, unique=True)
    slug = models.SlugField('URL', max_length=100, unique=True, blank=True)
    logo = models.ImageField('Логотип', upload_to='brands/', blank=True)
    description = models.TextField('Опис', blank=True)
    is_active = models.BooleanField('Активний', default=True)
    sort_order = models.PositiveIntegerField('Порядок сортування', default=0)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренди'
        ordering = ['sort_order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class ProductGroup(models.Model):
    """Групи товарів для фільтрації"""
    
    name = models.CharField('Назва групи', max_length=100, unique=True)
    slug = models.SlugField('URL', max_length=100, unique=True, blank=True)
    description = models.TextField('Опис', blank=True)
    is_active = models.BooleanField('Активна', default=True)
    sort_order = models.PositiveIntegerField('Порядок сортування', default=0)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Група товарів'
        verbose_name_plural = 'Групи товарів'
        ordering = ['sort_order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class ProductPurpose(models.Model):
    """Призначення товарів"""
    
    name = models.CharField('Призначення', max_length=100, unique=True)
    slug = models.SlugField('URL', max_length=100, unique=True, blank=True)
    description = models.TextField('Опис', blank=True)
    is_active = models.BooleanField('Активне', default=True)
    sort_order = models.PositiveIntegerField('Порядок сортування', default=0)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Призначення товару'
        verbose_name_plural = 'Призначення товарів'
        ordering = ['sort_order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """Категорії товарів з підтримкою ієрархії"""
    
    name = models.CharField('Назва', max_length=200)
    slug = models.SlugField('URL', max_length=200, unique=True, blank=True)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name='Батьківська категорія'
    )
    image = models.ImageField('Зображення', upload_to='categories/', blank=True)
    description = models.TextField('Опис', blank=True)
    is_active = models.BooleanField('Активна', default=True)
    sort_order = models.PositiveIntegerField('Порядок сортування', default=0)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    
    # SEO поля
    meta_title = models.CharField('SEO заголовок', max_length=200, blank=True)
    meta_description = models.TextField('SEO опис', max_length=300, blank=True)
    
    class Meta:
        verbose_name = 'Категорія'
        verbose_name_plural = 'Категорії'
        ordering = ['sort_order', 'name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:category', kwargs={'slug': self.slug})
    
    def get_all_children(self):
        """Повертає всі дочірні категорії рекурсивно"""
        children = []
        for child in self.children.filter(is_active=True):
            children.append(child)
            children.extend(child.get_all_children())
        return children
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name


class Product(models.Model):
    """Товари з підтримкою роздрібних та оптових цін"""
    
    name = models.CharField('Назва', max_length=200)
    slug = models.SlugField('URL', max_length=200, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='Категорія')
    description = models.TextField('Опис', blank=True)
    
    # ТИМЧАСОВО ЗАКОМЕНТОВАНО - додамо після міграції
    # brand = models.ForeignKey(
    #     Brand, 
    #     on_delete=models.SET_NULL, 
    #     null=True, 
    #     blank=True, 
    #     verbose_name='Бренд'
    # )
    # product_group = models.ForeignKey(
    #     ProductGroup, 
    #     on_delete=models.SET_NULL, 
    #     null=True, 
    #     blank=True, 
    #     verbose_name='Група товару'
    # )
    # purpose = models.ForeignKey(
    #     ProductPurpose, 
    #     on_delete=models.SET_NULL, 
    #     null=True, 
    #     blank=True, 
    #     verbose_name='Призначення'
    # )
    
    # Ціни
    retail_price = models.DecimalField('Роздрібна ціна', max_digits=10, decimal_places=2)
    wholesale_price = models.DecimalField(
        'Оптова ціна', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Ціна для оптових клієнтів'
    )
    
    # Знижки
    is_sale = models.BooleanField('Акційний товар', default=False)
    sale_price = models.DecimalField(
        'Акційна ціна', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    sale_start_date = models.DateTimeField(
        'Дата початку акції',
        null=True,
        blank=True,
        help_text='Акція почнеться автоматично з цієї дати'
    )
    sale_end_date = models.DateTimeField(
        'Дата закінчення акції',
        null=True,
        blank=True,
        help_text='Акція завершиться автоматично після цієї дати'
    )
    active_promotion_name = models.CharField(
        'Назва активної акції',
        max_length=100,
        blank=True,
        help_text='Назва акції для відображення на бейджі'
    )
    
    # Градація цін
    price_3_qty = models.DecimalField(
        'Ціна від 3 шт', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Ціна при покупці від 3 штук'
    )
    price_5_qty = models.DecimalField(
        'Ціна від 5 шт', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Ціна при покупці від 5 штук'
    )
    
    # Кількісні знижки (залишаємо для зворотної сумісності)
    min_quantity_discount = models.PositiveIntegerField(
        'Мінімальна кількість для знижки', 
        default=1,
        help_text='Мінімальна кількість для отримання знижки'
    )
    quantity_discount_price = models.DecimalField(
        'Ціна при великій кількості', 
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    # Стікери
    is_top = models.BooleanField('Топ', default=False)
    is_new = models.BooleanField('Новинка', default=False)
    # is_sale вже є вище для акційних товарів
    
    # Додаткові поля
    sku = models.CharField('Артикул', max_length=50, unique=True, blank=True)
    stock = models.PositiveIntegerField('Кількість на складі', default=0)
    is_active = models.BooleanField('Активний', default=True)
    is_featured = models.BooleanField('Рекомендований', default=False)
    sort_order = models.PositiveIntegerField('Порядок сортування', default=0)
    
    # Дати
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)
    
    # Зв'язки
    tags = models.ManyToManyField(
        'ProductTag', 
        verbose_name='Теги', 
        blank=True,
        help_text='Теги для фільтрації товарів'
    )
    
    # SEO поля
    meta_title = models.CharField('SEO заголовок', max_length=200, blank=True)
    meta_description = models.TextField('SEO опис', max_length=300, blank=True)
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товари'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'is_sale', 'is_new', 'is_top']),
            models.Index(fields=['sku']),
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        # Генерація slug з назви
        if not self.slug:
            self.slug = slugify(self.name)
        
        # Генерація SKU тільки якщо не вказано
        generate_sku = not self.sku
        
        if generate_sku:
            # Тимчасово встановлюємо унікальний тимчасовий SKU
            self.sku = f"TEMP{int(time.time() * 1000000)}"
        
        # Зберігаємо товар
        super().save(*args, **kwargs)
        
        # Після збереження генеруємо правильний SKU
        if generate_sku:
            self.sku = f"BS{self.id:05d}"
            # Оновлюємо тільки поле SKU
            Product.objects.filter(pk=self.pk).update(sku=self.sku)
    
    def get_absolute_url(self):
        return reverse('products:detail', kwargs={'slug': self.slug})
    
    @property
    def main_image(self):
        """Повертає головне зображення товару"""
        return self.images.filter(is_main=True).first() or self.images.first()
    
    def is_sale_active(self):
        """Перевіряє чи активна акція зараз"""
        if not self.is_sale or not self.sale_price:
            return False
        
        # Якщо дати не вказані - акція завжди активна
        if not self.sale_start_date and not self.sale_end_date:
            return True
        
        from django.utils import timezone
        now = timezone.now()
        
        # Перевіряємо чи в межах періоду
        if self.sale_start_date and now < self.sale_start_date:
            return False
        if self.sale_end_date and now > self.sale_end_date:
            return False
        
        return True
    
    def get_price_for_user(self, user=None, quantity=1):
        """
        Повертає ціну для конкретного користувача з урахуванням:
        - Оптового статусу
        - Градації цін (3 шт, 5 шт)
        - Кількісних знижок
        - Акційних цін (з перевіркою періоду)
        
        Пріоритет застосування (найвигідніша для клієнта):
        1. Акційна ціна (якщо активна)
        2. Ціна від 5 шт (якщо qty >= 5)
        3. Ціна від 3 шт (якщо qty >= 3)
        4. Оптова ціна (для зареєстрованих)
        5. Базова роздрібна ціна
        """
        # Базова ціна
        if user and user.is_authenticated and hasattr(user, 'is_wholesale') and user.is_wholesale and self.wholesale_price:
            base_price = self.wholesale_price
        else:
            base_price = self.retail_price
        
        # Акційна ціна (з перевіркою періоду)
        if self.is_sale_active():
            base_price = min(base_price, self.sale_price)
        
        # Градація цін (нова система)
        if quantity >= 5 and self.price_5_qty:
            base_price = min(base_price, self.price_5_qty)
        elif quantity >= 3 and self.price_3_qty:
            base_price = min(base_price, self.price_3_qty)
        
        # Стара система кількісних знижок (для зворотної сумісності)
        if quantity >= self.min_quantity_discount and self.quantity_discount_price:
            base_price = min(base_price, self.quantity_discount_price)
        
        return base_price
    
    def get_all_prices(self):
        """Повертає всі доступні ціни для відображення"""
        prices = {
            'retail': self.retail_price,
            'wholesale': self.wholesale_price,
            'sale': self.sale_price if self.is_sale_active() else None,
            'qty_3': self.price_3_qty,
            'qty_5': self.price_5_qty,
        }
        return {k: v for k, v in prices.items() if v is not None}
    
    def get_stickers(self):
        """Повертає список активних стікерів (бейджів)"""
        stickers = []
        if self.is_top:
            stickers.append({'type': 'top', 'text': 'Хіт', 'class': 'badge-top'})
        if self.is_new:
            stickers.append({'type': 'new', 'text': 'Новинка', 'class': 'badge-new'})
        if self.is_sale_active():
            # Якщо є назва акції - показуємо її, інакше відсоток
            if self.active_promotion_name:
                stickers.append({'type': 'sale', 'text': self.active_promotion_name, 'class': 'badge-sale'})
            else:
                discount = self.get_discount_percentage()
                if discount > 0:
                    stickers.append({'type': 'sale', 'text': f'-{discount}%', 'class': 'badge-sale'})
                else:
                    stickers.append({'type': 'sale', 'text': 'Акція', 'class': 'badge-sale'})
        return stickers
    
    def get_similar_products(self, limit=4):
        """Повертає схожі товари з тієї ж категорії"""
        return Product.objects.filter(
            category=self.category,
            is_active=True
        ).exclude(id=self.id).order_by('?')[:limit]
    
    def get_discount_percentage(self):
        """Розраховує відсоток знижки"""
        if self.is_sale_active() and self.sale_price and self.retail_price > 0:
            discount = ((self.retail_price - self.sale_price) / self.retail_price) * 100
            return round(discount)
        return 0
    
    def get_discount_amount(self):
        """Повертає суму знижки"""
        if self.is_sale and self.sale_price:
            return self.retail_price - self.sale_price
        return 0
    
    def is_in_stock(self):
        """Перевіряє чи є товар в наявності"""
        return self.stock > 0
    
    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """Зображення товарів"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField('Зображення', upload_to='products/')
    alt_text = models.CharField('Alt текст', max_length=200, blank=True)
    is_main = models.BooleanField('Головне зображення', default=False)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    
    class Meta:
        verbose_name = 'Зображення товару'
        verbose_name_plural = 'Зображення товарів'
        ordering = ['sort_order']
    
    def save(self, *args, **kwargs):
        # Пропускаємо оптимізацію для Cloudinary
        from django.conf import settings
        skip_optimization = kwargs.pop('skip_optimization', False)
        
        # Оптимізуємо зображення перед збереженням (тільки для локального storage)
        if (not skip_optimization and 
            self.image and 
            hasattr(self.image, 'file') and 
            'cloudinary' not in str(settings.DEFAULT_FILE_STORAGE).lower()):
            try:
                from io import BytesIO
                from django.core.files.uploadedfile import InMemoryUploadedFile
                
                # Відкриваємо зображення з файлу
                img = Image.open(self.image)
                
                # Перевіряємо чи потрібна оптимізація
                if img.height > 800 or img.width > 800:
                    # Конвертуємо RGBA в RGB якщо потрібно
                    if img.mode in ('RGBA', 'LA', 'P'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = background
                    
                    # Зменшуємо розмір
                    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                    
                    # Зберігаємо в BytesIO
                    output = BytesIO()
                    img.save(output, format='JPEG', optimize=True, quality=85)
                    output.seek(0)
                    
                    # Оновлюємо файл
                    self.image = InMemoryUploadedFile(
                        output,
                        'ImageField',
                        f"{self.image.name.split('.')[0]}.jpg",
                        'image/jpeg',
                        output.getbuffer().nbytes,
                        None
                    )
            except Exception as e:
                # Якщо оптимізація не вдалась, просто зберігаємо оригінал
                pass
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Зображення для {self.product.name}"


class ProductTag(models.Model):
    """Теги товарів для фільтрації"""
    
    name = models.CharField('Назва тегу', max_length=50, unique=True)
    slug = models.SlugField('URL', max_length=50, unique=True, blank=True)
    is_active = models.BooleanField('Активний', default=True)
    
    class Meta:
        verbose_name = 'Тег товару'
        verbose_name_plural = 'Теги товарів'
        ordering = ['name']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class ProductAttribute(models.Model):
    """Характеристики товарів"""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    name = models.CharField('Назва характеристики', max_length=100)
    value = models.CharField('Значення', max_length=200)
    sort_order = models.PositiveIntegerField('Порядок', default=0)
    
    class Meta:
        verbose_name = 'Характеристика товару'
        verbose_name_plural = 'Характеристики товарів'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.name}: {self.value}"


class NewProduct(models.Model):
    """Новинки на головній сторінці"""
    
    product = models.OneToOneField(
        Product, 
        on_delete=models.CASCADE, 
        verbose_name='Товар',
        limit_choices_to={'is_active': True},
        related_name='new_product_entry'
    )
    sort_order = models.PositiveIntegerField('Порядок відображення', default=0)
    is_active = models.BooleanField('Активний', default=True)
    created_at = models.DateTimeField('Додано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Новинка'
        verbose_name_plural = 'Новинки'
        ordering = ['sort_order', '-created_at']
    
    def __str__(self):
        return f"{self.product.name} (позиція {self.sort_order})"
    
    def save(self, *args, **kwargs):
        """При збереженні автоматично встановлюємо is_new=True для товару"""
        super().save(*args, **kwargs)
        if not self.product.is_new:
            Product.objects.filter(pk=self.product.pk).update(is_new=True)
    
    def delete(self, *args, **kwargs):
        """При видаленні знімаємо is_new з товару"""
        product_id = self.product.pk
        super().delete(*args, **kwargs)
        Product.objects.filter(pk=product_id).update(is_new=False)


# ============================================
#        НОВІ МОДЕЛІ ДЛЯ РОЗШИРЕНОЇ АДМІНКИ
# ============================================

class CategoryFilterConfig(models.Model):
    """Конфігурація фільтрів для категорій"""
    
    category = models.OneToOneField(
        Category,
        on_delete=models.CASCADE,
        related_name='filter_config',
        verbose_name='Категорія'
    )
    
    # Активні фільтри для цієї категорії
    show_brand_filter = models.BooleanField('Показувати фільтр Бренд', default=True)
    show_group_filter = models.BooleanField('Показувати фільтр Група', default=True)
    show_purpose_filter = models.BooleanField('Показувати фільтр Призначення', default=True)
    show_price_filter = models.BooleanField('Показувати фільтр Ціна', default=True)
    show_availability_filter = models.BooleanField('Показувати фільтр Наявність', default=True)
    
    # Додаткові атрибути (JSON)
    custom_filters = models.JSONField(
        'Кастомні фільтри',
        default=dict,
        blank=True,
        help_text='Додаткові фільтри у форматі JSON'
    )
    
    class Meta:
        verbose_name = 'Конфігурація фільтрів категорії'
        verbose_name_plural = 'Конфігурації фільтрів категорій'
    
    def __str__(self):
        return f"Фільтри для {self.category.name}"


class ProductChangeLog(models.Model):
    """Логування змін критичних полів товарів"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='change_logs',
        verbose_name='Товар'
    )
    user = models.ForeignKey(
        'users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Користувач'
    )
    
    field_name = models.CharField('Поле', max_length=50)
    old_value = models.TextField('Старе значення', blank=True)
    new_value = models.TextField('Нове значення', blank=True)
    
    change_type = models.CharField(
        'Тип зміни',
        max_length=20,
        choices=[
            ('price', 'Зміна ціни'),
            ('status', 'Зміна статусу'),
            ('visibility', 'Зміна видимості'),
            ('stock', 'Зміна кількості'),
            ('sale', 'Зміна акції'),
            ('other', 'Інше'),
        ],
        default='other'
    )
    
    created_at = models.DateTimeField('Дата зміни', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Лог змін товару'
        verbose_name_plural = 'Логи змін товарів'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', '-created_at']),
            models.Index(fields=['change_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.field_name} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"

