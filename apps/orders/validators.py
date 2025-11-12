"""
Валідатори для замовлень
"""
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


def validate_ukrainian_phone(phone: str) -> bool:
    """
    Валідує український номер телефону
    Формат: +380XXXXXXXXX
    """
    if not phone:
        return False
    
    pattern = r'^\+380\d{9}$'
    return bool(re.match(pattern, phone))


def validate_order_email(email: str) -> bool:
    """Валідує email"""
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def validate_order_data(data: dict) -> tuple[bool, str]:
    """
    Валідує дані замовлення
    
    Returns:
        tuple: (is_valid, error_message)
    """
    required_fields = ['first_name', 'last_name', 'middle_name', 'email', 'phone', 'delivery_method', 'payment_method']
    
    for field in required_fields:
        if not data.get(field):
            return False, f"Поле '{field}' є обов'язковим"
    
    # Валідація email
    if not validate_order_email(data['email']):
        return False, "Невірний формат email"
    
    # Валідація телефону
    if not validate_ukrainian_phone(data['phone']):
        return False, "Невірний формат телефону. Використовуйте +380XXXXXXXXX"
    
    # Валідація імені (без цифр та спецсимволів)
    name_pattern = r'^[а-яА-ЯіІїЇєЄa-zA-Z\s\'-]+$'
    for field in ['first_name', 'last_name', 'middle_name']:
        if data.get(field) and not re.match(name_pattern, data[field]):
            return False, f"Поле '{field}' містить некоректні символи"
    
    return True, ""

