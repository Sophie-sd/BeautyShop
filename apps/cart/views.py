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
        item_price = Decimal(cart_item.get('price', product.get_price_for_user(cart.user, item_quantity)))
        
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
                'price': float(item_price),
                'total': float(item_price * item_quantity),
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
