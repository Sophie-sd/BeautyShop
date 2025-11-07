"""
Моделі користувачів з підтримкою оптових цін
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from decimal import Decimal
import secrets


class CustomUser(AbstractUser):
    """Розширена модель користувача"""
    
    phone_validator = RegexValidator(
        regex=r'^\+380\d{9}$',
        message='Невірний формат телефону. Використовуйте формат +380XXXXXXXXX'
    )
    
    middle_name = models.CharField(
        'По-батькові',
        max_length=100,
        blank=True,
        help_text='Необов\'язкове поле'
    )
    phone = models.CharField(
        'Телефон', 
        max_length=20, 
        blank=True,
        null=True,
        unique=True,
        validators=[phone_validator],
        help_text='Формат: +380XXXXXXXXX'
    )
    date_of_birth = models.DateField('Дата народження', null=True, blank=True)
    
    # Email верифікація
    email_verified = models.BooleanField('Email підтверджено', default=False)
    email_verification_token = models.CharField('Токен верифікації', max_length=100, blank=True)
    
    is_wholesale = models.BooleanField(
        'Оптовий клієнт', 
        default=True,
        help_text='Всі зареєстровані користувачі мають доступ до оптових цін'
    )
    created_at = models.DateTimeField('Дата реєстрації', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'
    
    def generate_email_verification_token(self):
        """Генерує токен для верифікації email"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.save(update_fields=['email_verification_token'])
        return self.email_verification_token
    
    def verify_email(self, token):
        """Верифікує email якщо токен збігається"""
        if self.email_verification_token and self.email_verification_token == token:
            self.email_verified = True
            self.is_active = True
            self.is_wholesale = True  # Надаємо оптовий статус при підтвердженні email
            self.email_verification_token = ''
            self.save(update_fields=['email_verified', 'is_active', 'is_wholesale', 'email_verification_token'])
            return True
        return False
    
    def get_price_for_product(self, product):
        """
        Повертає ціну товару залежно від статусу користувача.
        Зареєстровані користувачі бачать оптові ціни.
        """
        if self.is_wholesale and product.wholesale_price:
            return product.wholesale_price
        return product.retail_price
    
    def __str__(self):
        return f"{self.username} (Оптовий клієнт)"


class UserProfile(models.Model):
    """Додаткова інформація про користувача"""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    company_name = models.CharField('Назва компанії', max_length=200, blank=True)
    tax_number = models.CharField('Податковий номер', max_length=50, blank=True)
    address = models.TextField('Адреса', blank=True)
    notes = models.TextField('Примітки', blank=True)
    
    class Meta:
        verbose_name = 'Профіль користувача'
        verbose_name_plural = 'Профілі користувачів'
    
    def __str__(self):
        return f"Профіль {self.user.username}"
