"""
Моделі користувачів з підтримкою оптових цін
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from decimal import Decimal
from datetime import timedelta
import secrets
import random


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
    
    # Код верифікації email (6 цифр)
    email_verification_code = models.CharField('Код верифікації email', max_length=6, blank=True)
    email_verification_code_created_at = models.DateTimeField('Час створення коду верифікації', null=True, blank=True)
    email_verification_attempts = models.IntegerField('Спроби введення коду', default=0)
    
    # Код відновлення паролю (6 цифр)
    password_reset_code = models.CharField('Код відновлення паролю', max_length=6, blank=True)
    password_reset_code_created_at = models.DateTimeField('Час створення коду відновлення', null=True, blank=True)
    password_reset_attempts = models.IntegerField('Спроби введення коду відновлення', default=0)
    
    is_wholesale = models.BooleanField(
        'Оптовий клієнт', 
        default=False,
        help_text='Встановлюється True після підтвердження email'
    )
    created_at = models.DateTimeField('Дата реєстрації', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'
    
    def generate_email_verification_token(self):
        """Генерує токен для верифікації email (старий метод)"""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.save(update_fields=['email_verification_token'])
        return self.email_verification_token
    
    def generate_email_verification_code(self):
        """Генерує 6-значний код для верифікації email"""
        self.email_verification_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.email_verification_code_created_at = timezone.now()
        self.email_verification_attempts = 0
        self.save(update_fields=['email_verification_code', 'email_verification_code_created_at', 'email_verification_attempts'])
        return self.email_verification_code
    
    def verify_email_code(self, code):
        """Верифікує email код"""
        if not self.email_verification_code or not self.email_verification_code_created_at:
            return False, 'Код не знайдено. Будь ласка, запросіть новий код.'
        
        # Перевіряємо термін дії (15 хвилин)
        time_limit = timedelta(minutes=15)
        if timezone.now() - self.email_verification_code_created_at > time_limit:
            return False, 'Термін дії коду минув. Будь ласка, запросіть новий код.'
        
        # Перевіряємо кількість спроб (максимум 5)
        if self.email_verification_attempts >= 5:
            return False, 'Перевищено кількість спроб. Будь ласка, запросіть новий код.'
        
        # Збільшуємо лічильник спроб
        self.email_verification_attempts += 1
        self.save(update_fields=['email_verification_attempts'])
        
        # Перевіряємо код
        if self.email_verification_code == code:
            self.email_verified = True
            self.is_active = True
            self.is_wholesale = True
            self.email_verification_code = ''
            self.email_verification_code_created_at = None
            self.email_verification_attempts = 0
            self.save(update_fields=['email_verified', 'is_active', 'is_wholesale', 'email_verification_code', 'email_verification_code_created_at', 'email_verification_attempts'])
            return True, 'Email успішно підтверджено!'
        
        return False, f'Невірний код. Залишилось спроб: {5 - self.email_verification_attempts}'
    
    def generate_password_reset_code(self):
        """Генерує 6-значний код для відновлення паролю"""
        self.password_reset_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.password_reset_code_created_at = timezone.now()
        self.password_reset_attempts = 0
        self.save(update_fields=['password_reset_code', 'password_reset_code_created_at', 'password_reset_attempts'])
        return self.password_reset_code
    
    def verify_password_reset_code(self, code):
        """Верифікує код відновлення паролю"""
        if not self.password_reset_code or not self.password_reset_code_created_at:
            return False, 'Код не знайдено. Будь ласка, запросіть новий код.'
        
        # Перевіряємо термін дії (15 хвилин)
        time_limit = timedelta(minutes=15)
        if timezone.now() - self.password_reset_code_created_at > time_limit:
            return False, 'Термін дії коду минув. Будь ласка, запросіть новий код.'
        
        # Перевіряємо кількість спроб (максимум 5)
        if self.password_reset_attempts >= 5:
            return False, 'Перевищено кількість спроб. Будь ласка, запросіть новий код.'
        
        # Збільшуємо лічильник спроб
        self.password_reset_attempts += 1
        self.save(update_fields=['password_reset_attempts'])
        
        # Перевіряємо код
        if self.password_reset_code == code:
            return True, 'Код підтверджено!'
        
        return False, f'Невірний код. Залишилось спроб: {5 - self.password_reset_attempts}'
    
    def clear_password_reset_code(self):
        """Очищає код відновлення паролю після використання"""
        self.password_reset_code = ''
        self.password_reset_code_created_at = None
        self.password_reset_attempts = 0
        self.save(update_fields=['password_reset_code', 'password_reset_code_created_at', 'password_reset_attempts'])
    
    def verify_email(self, token):
        """Верифікує email якщо токен збігається (старий метод)"""
        if self.email_verification_token and self.email_verification_token == token:
            self.email_verified = True
            self.is_active = True
            self.is_wholesale = True
            self.email_verification_token = ''
            self.save(update_fields=['email_verified', 'is_active', 'is_wholesale', 'email_verification_token'])
            return True
        return False
    
    def get_price_for_product(self, product):
        """
        Повертає ціну товару залежно від статусу користувача.
        Зареєстровані оптові користувачі (НЕ адміністратори) бачать оптові ціни.
        """
        if self.is_wholesale and product.wholesale_price and not self.is_staff and not self.is_superuser:
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


class WholesaleClient(CustomUser):
    """Proxy модель для оптових клієнтів"""
    
    class Meta:
        proxy = True
        verbose_name = 'Оптовий клієнт'
        verbose_name_plural = 'Оптові клієнти'
