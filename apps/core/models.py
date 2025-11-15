"""
Моделі для core додатку - банери головної сторінки
"""
from django.db import models
from django.core.validators import FileExtensionValidator


class Banner(models.Model):
    """Модель для банерів на головній сторінці"""
    
    title = models.CharField(
        max_length=200,
        verbose_name="Назва банера",
        help_text="Назва для ідентифікації в адмін панелі"
    )
    
    # Зображення для різних пристроїв
    desktop_image = models.ImageField(
        upload_to='banners/desktop/',
        verbose_name="Зображення для десктопу",
        help_text="Розмір: 1200×400 пікселів (співвідношення 3:1)",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    
    mobile_image = models.ImageField(
        upload_to='banners/mobile/',
        verbose_name="Зображення для мобільного",
        help_text="Розмір: 375×280 пікселів (співвідношення 1.34:1)",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    
    # Посилання
    link_url = models.URLField(
        verbose_name="Посилання",
        help_text="URL на який переходити при натисканні на банер",
        blank=True,
        null=True
    )
    
    # Додаткові поля
    alt_text = models.CharField(
        max_length=255,
        verbose_name="Alt текст",
        help_text="Текст для accessibility та SEO",
        default="Банер Beauty Shop"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активний",
        help_text="Показувати банер на сайті"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок сортування",
        help_text="Менше число = вище в списку"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Створено"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Оновлено"
    )
    
    class Meta:
        verbose_name = "Банер"
        verbose_name_plural = "Банери"
        ordering = ['order', '-created_at']
        
    def __str__(self):
        return f"{self.title} ({'Активний' if self.is_active else 'Неактивний'})"
        
    def save(self, *args, **kwargs):
        # Автоматично генеруємо alt_text якщо не заповнений
        if not self.alt_text:
            self.alt_text = f"Банер: {self.title}"
        super().save(*args, **kwargs)


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
        db_table = 'orders_newsletter'
    
    def __str__(self):
        return self.email
