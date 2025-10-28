from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from decimal import Decimal
from apps.products.models import Product
from .cart import Cart


def cart_detail(request):
    """Перегляд кошика"""
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})


@require_POST
def cart_add(request, product_id):
    """Додавання товару в кошик (AJAX)"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override') == 'true'
    
    cart.add(product=product, quantity=quantity, override_quantity=override)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        product_id_str = str(product_id)
        cart_item = cart.cart.get(product_id_str, {})
        item_quantity = cart_item.get('quantity', 0)
        item_price = cart_item.get('price', 0)
        if not isinstance(item_price, (int, float)):
            item_price = float(item_price) if item_price else 0.0
        
        return JsonResponse({
            'success': True,
            'message': f'{product.name} додано в кошик',
            'cart': {
                'item_count': len(cart),
                'total_items': len(cart.cart),
                'total_price': float(cart.get_total_price()),
            },
            'item': {
                'product_id': product_id,
                'quantity': item_quantity,
                'price': item_price,
                'total': item_price * item_quantity,
            }
        })
    
    return redirect('cart:detail')


@require_POST
def cart_remove(request, product_id):
    """Видалення товару з кошика (AJAX)"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.name} видалено з кошика',
            'cart': {
                'item_count': len(cart),
                'total_items': len(cart.cart),
                'total_price': float(cart.get_total_price()),
            }
        })
    
    return redirect('cart:detail')


def cart_clear(request):
    """Очищення кошика"""
    cart = Cart(request)
    cart.clear()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Кошик очищено',
            'cart': {
                'item_count': 0,
                'total_items': 0,
                'total_price': 0,
            }
        })
    
    return redirect('cart:detail')


def cart_count(request):
    """Повертає кількість товарів у кошику (для badge)"""
    cart = Cart(request)
    return JsonResponse({'count': len(cart)})


@require_POST
def apply_promo_code(request):
    """Застосування промокоду"""
    from apps.promotions.models import PromoCode
    from django.utils import timezone
    
    promo_code = request.POST.get('code', '').strip().upper()
    
    if not promo_code:
        return JsonResponse({
            'success': False,
            'message': 'Введіть промокод'
        })
    
    try:
        promo = PromoCode.objects.get(
            code=promo_code,
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
        
        cart = Cart(request)
        total = cart.get_total_price()
        
        # Перевірка мінімальної суми
        if promo.min_order_amount and total < promo.min_order_amount:
            return JsonResponse({
                'success': False,
                'message': f'Мінімальна сума замовлення для цього промокоду: {promo.min_order_amount} ₴'
            })
        
        # Перевірка ліміту використань
        if promo.usage_limit and promo.used_count >= promo.usage_limit:
            return JsonResponse({
                'success': False,
                'message': 'Промокод вичерпано'
            })
        
        # Розрахунок знижки
        if promo.discount_type == 'percent':
            discount = total * (Decimal(str(promo.discount_value)) / Decimal('100'))
        else:  # fixed
            discount = Decimal(str(promo.discount_value))
        
        discount = min(discount, total)  # Знижка не може бути більше суми
        
        # Зберігаємо в сесії
        request.session['promo_code'] = promo_code
        request.session['promo_discount'] = float(-discount)
        request.session['promo_id'] = promo.id
        
        return JsonResponse({
            'success': True,
            'message': f'Промокод "{promo_code}" застосовано',
            'discount': float(discount),
            'new_total': float(total - discount)
        })
        
    except PromoCode.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Невірний промокод'
        })


def remove_promo_code(request):
    """Видалення промокоду"""
    if 'promo_code' in request.session:
        del request.session['promo_code']
    if 'promo_discount' in request.session:
        del request.session['promo_discount']
    if 'promo_id' in request.session:
        del request.session['promo_id']
    
    return JsonResponse({
        'success': True,
        'message': 'Промокод видалено'
    })
