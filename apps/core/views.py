"""
Core Views - основні представлення сайту
"""
from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.db.models import Q
from apps.products.models import Product, Category, NewProduct
from apps.blog.models import Article
from .models import Banner


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HomeView(TemplateView):
    """Головна сторінка"""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Отримуємо активні банери
        banners = Banner.objects.filter(is_active=True).order_by('order', '-created_at')
        
        # Отримуємо новинки
        # 1. Товари з is_new=True (автоматично)
        # 2. Товари додані вручну через NewProduct
        new_products = NewProduct.objects.filter(
            is_active=True,
            product__is_active=True,
            product__is_new=True
        ).select_related('product').prefetch_related('product__images')[:12]
        
        # Отримуємо акційні товари з валідними датами або без дат (завжди активні)
        from django.utils import timezone
        now = timezone.now()
        promotion_products = Product.objects.filter(
            Q(is_active=True) &
            Q(is_sale=True) &
            (
                Q(sale_start_date__isnull=True, sale_end_date__isnull=True) |
                Q(sale_start_date__isnull=True, sale_end_date__gte=now) |
                Q(sale_start_date__lte=now, sale_end_date__isnull=True) |
                Q(sale_start_date__lte=now, sale_end_date__gte=now)
            )
        ).select_related('category').prefetch_related('images')[:20]
        
        context.update({
            'banners': banners,
            'new_products': [np.product for np in new_products],
            'promotion_products': promotion_products,
            'categories': Category.objects.filter(parent=None, is_active=True).order_by('sort_order', 'name'),
        })
        return context


class CatalogView(TemplateView):
    """Каталог категорій"""
    template_name = 'core/catalog.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent=None, is_active=True).order_by('sort_order', 'name')
        return context


class DeliveryView(TemplateView):
    """Доставка та оплата"""
    template_name = 'core/delivery.html'


class ReturnsView(TemplateView):
    """Повернення та обмін"""
    template_name = 'core/returns.html'


class AboutView(TemplateView):
    """Про нас"""
    template_name = 'core/about.html'


class ContactsView(TemplateView):
    """Контакти"""
    template_name = 'core/contacts.html'


class TermsView(TemplateView):
    """Умови використання"""
    template_name = 'core/terms.html'


class PrivacyView(TemplateView):
    """Політика конфіденційності"""
    template_name = 'core/privacy.html'


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SearchView(TemplateView):
    """Пошук товарів"""
    template_name = 'core/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        
        if query:
            # Спочатку отримуємо всі результати для підрахунку
            all_products = Product.objects.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(category__name__icontains=query),
                is_active=True
            ).distinct()
            
            # Підраховуємо загальну кількість
            total_count = all_products.count()
            
            # Берем тільки перші 20 для відображення з оптимізацією запитів
            products = all_products.select_related('category').prefetch_related('images')[:20]
            
            context.update({
                'products': products,
                'query': query,
                'results_count': total_count,
            })
        
        return context
