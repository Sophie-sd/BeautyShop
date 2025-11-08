from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.cart.cart import Cart
from decimal import Decimal
from .models import Newsletter


MINIMUM_WHOLESALE_ORDER = Decimal('5000.00')


def order_create(request):
    """Створення замовлення"""
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, 'Ваш кошик порожній')
        return redirect('cart:detail')
    
    # Перевірка мінімальної суми для авторизованих користувачів (оптових клієнтів, НЕ адміністраторів)
    total_price = cart.get_total_price()
    is_wholesale_user = (
        request.user.is_authenticated and 
        not request.user.is_staff and 
        not request.user.is_superuser
    )
    
    if is_wholesale_user and total_price < MINIMUM_WHOLESALE_ORDER:
        messages.error(
            request, 
            f'Мінімальна сума замовлення для оптових клієнтів становить {MINIMUM_WHOLESALE_ORDER} грн. '
            f'Ваша поточна сума: {total_price} грн. '
            'Будь ласка, додайте ще товарів або вийдіть з особистого кабінету для замовлення без обмежень.'
        )
        return redirect('cart:detail')
    
    if request.method == 'POST':
        # Повторна перевірка при POST запиті
        if is_wholesale_user and total_price < MINIMUM_WHOLESALE_ORDER:
            messages.error(
                request, 
                f'Мінімальна сума замовлення для оптових клієнтів становить {MINIMUM_WHOLESALE_ORDER} грн.'
            )
            return redirect('cart:detail')
        
        # Тут буде логіка створення замовлення
        # Поки що просто очищуємо кошик
        cart.clear()
        messages.success(request, 'Ваше замовлення прийнято!')
        return redirect('orders:success')
    
    return render(request, 'orders/create.html', {'cart': cart})


def order_success(request):
    """Сторінка успішного замовлення"""
    return render(request, 'orders/success.html')


@require_POST
def newsletter_subscribe(request):
    """Підписка на розсилку"""
    try:
        email = request.POST.get('email', '').strip().lower()
        name = request.POST.get('name', '').strip()
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Email обов\'язковий'
            })
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if User.objects.filter(email__iexact=email, is_staff=True).exists():
            return JsonResponse({
                'success': False,
                'message': 'Некоректна email адреса'
            })
        
        if User.objects.filter(email__iexact=email, is_superuser=True).exists():
            return JsonResponse({
                'success': False,
                'message': 'Некоректна email адреса'
            })
        
        newsletter, created = Newsletter.objects.get_or_create(
            email=email,
            defaults={'name': name, 'is_active': True}
        )
        
        if not created:
            newsletter.is_active = True
            newsletter.save(update_fields=['is_active'])
        
        return JsonResponse({
            'success': True,
            'message': 'Дякуємо! Ви успішно підписалися на розсилку.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Помилка при підписці. Спробуйте пізніше.'
        })
