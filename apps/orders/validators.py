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
    required_fields = ['first_name', 'last_name', 'email', 'phone', 'delivery_method', 'payment_method']
    
    for field in required_fields:
        if not data.get(field):
            field_names = {
                'first_name': 'Ім\'я',
                'last_name': 'Прізвище',
                'email': 'Email',
                'phone': 'Телефон',
                'delivery_method': 'Спосіб доставки',
                'payment_method': 'Спосіб оплати'
            }
            return False, f"Поле '{field_names.get(field, field)}' є обов'язковим"
    
    # Валідація email
    if not validate_order_email(data['email']):
        return False, "Невірний формат email"
    
    # Валідація телефону
    if not validate_ukrainian_phone(data['phone']):
        return False, "Невірний формат телефону. Використовуйте +380XXXXXXXXX"
    
    # Валідація імені (дозволяємо літери, пробіли, дефіс, апостроф та типографічні апострофи)
    # Підтримка як ASCII апострофу ('), так і Unicode апострофів (' ' ʼ)
    name_pattern = r'^[а-яА-ЯіІїЇєЄҐґa-zA-Z\s\'\'\'\`ʼ\-]+$'
    for field in ['first_name', 'last_name', 'middle_name']:
        if data.get(field) and data[field].strip():
            value = data[field].strip()
            if not re.match(name_pattern, value):
                field_names = {
                    'first_name': 'Ім\'я',
                    'last_name': 'Прізвище',
                    'middle_name': 'По-батькові'
                }
                return False, f"Поле '{field_names.get(field, field)}' містить некоректні символи. Використовуйте тільки літери, пробіли, дефіс та апостроф."
    
    return True, ""

