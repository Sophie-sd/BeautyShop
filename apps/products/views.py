from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from .models import Product, Category


class CategoryView(ListView):
    """Перегляд товарів категорії"""
    model = Product
    template_name = 'products/category.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        
        # Отримуємо всі підкатегорії цієї категорії
        subcategories = self.category.children.filter(is_active=True)
        category_ids = [self.category.id] + list(subcategories.values_list('id', flat=True))
        
        # Базовий queryset - товари з категорії та її підкатегорій
        queryset = Product.objects.filter(
            category_id__in=category_ids,
            is_active=True
        ).select_related('category').prefetch_related('images')
        
        # Фільтр по підкатегоріях (якщо обрано)
        selected_subcats = self.request.GET.getlist('subcategory')
        if selected_subcats:
            queryset = queryset.filter(category__slug__in=selected_subcats)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        
        # Підкатегорії для фільтрів
        context['subcategories'] = self.category.children.filter(is_active=True)
        
        # Обрані підкатегорії (для checkbox state)
        context['selected_subcategories'] = self.request.GET.getlist('subcategory')
        
        return context


class ProductDetailView(DetailView):
    """Детальна сторінка товару"""
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True)


class SaleProductsView(ListView):
    """Акції - показує товари з is_sale=True"""
    model = Product
    template_name = 'products/sale.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        return Product.objects.filter(
            is_sale=True,
            is_active=True
        ).prefetch_related('images').order_by('-created_at')
