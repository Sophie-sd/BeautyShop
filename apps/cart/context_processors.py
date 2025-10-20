"""
Context processor для відображення кошика в шаблонах
"""
from .cart import Cart


def cart(request):
    """Додає об'єкт кошика в контекст всіх шаблонів"""
    return {'cart': Cart(request)}

