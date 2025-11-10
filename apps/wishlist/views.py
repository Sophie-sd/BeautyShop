"""
Views для списку бажань
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView
from apps.products.models import Product
from .wishlist import Wishlist


@method_decorator(ensure_csrf_cookie, name='dispatch')
class WishlistView(TemplateView):
    """Сторінка списку бажань"""
    template_name = 'wishlist/list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        wishlist = Wishlist(self.request)
        context['wishlist'] = wishlist
        context['products'] = wishlist.get_products()
        return context


@require_POST
def wishlist_add(request, product_id):
    """Додавання товару в список бажань (AJAX)"""
    try:
        wishlist = Wishlist(request)
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        added = wishlist.add(product)
        
        return JsonResponse({
            'success': True,
            'added': added,
            'count': len(wishlist),
            'message': 'Товар додано до обраного' if added else 'Товар вже в обраному'
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Товар не знайдено'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Помилка: {str(e)}'
        }, status=500)


@require_POST
def wishlist_remove(request, product_id):
    """Видалення товару зі списку бажань (AJAX)"""
    try:
        wishlist = Wishlist(request)
        product = get_object_or_404(Product, id=product_id)
        
        removed = wishlist.remove(product)
        
        return JsonResponse({
            'success': True,
            'removed': removed,
            'count': len(wishlist),
            'message': 'Товар видалено з обраного'
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Товар не знайдено'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Помилка: {str(e)}'
        }, status=500)


def wishlist_clear(request):
    """Очищення списку бажань"""
    wishlist = Wishlist(request)
    wishlist.clear()
    return redirect('wishlist:list')

