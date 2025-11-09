from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Min, Max, Q
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
        
        # Фільтр по підкатегоріях
        selected_subcats = self.request.GET.getlist('subcategory')
        if selected_subcats:
            queryset = queryset.filter(category__slug__in=selected_subcats)
        
        # Фільтр по ціні
        price_min = self.request.GET.get('price_min')
        price_max = self.request.GET.get('price_max')
        if price_min:
            try:
                queryset = queryset.filter(retail_price__gte=float(price_min))
            except ValueError:
                pass
        if price_max:
            try:
                queryset = queryset.filter(retail_price__lte=float(price_max))
            except ValueError:
                pass
        
        # Фільтр по наявності
        availability = self.request.GET.getlist('availability')
        if 'in_stock' in availability and 'out_of_stock' not in availability:
            queryset = queryset.filter(stock__gt=0)
        elif 'out_of_stock' in availability and 'in_stock' not in availability:
            queryset = queryset.filter(stock=0)
        
        # Фільтр по типу товару
        product_types = self.request.GET.getlist('type')
        if product_types:
            from django.utils import timezone
            now = timezone.now()
            type_filter = Q()
            if 'new' in product_types:
                type_filter |= Q(is_new=True)
            if 'sale' in product_types:
                type_filter |= (
                    Q(is_sale=True) &
                    (
                        Q(sale_start_date__isnull=True, sale_end_date__isnull=True) |
                        Q(sale_start_date__isnull=True, sale_end_date__gte=now) |
                        Q(sale_start_date__lte=now, sale_end_date__isnull=True) |
                        Q(sale_start_date__lte=now, sale_end_date__gte=now)
                    )
                )
            if type_filter:
                queryset = queryset.filter(type_filter)
        
        # Сортування
        sort = self.request.GET.get('sort', 'default')
        if sort == 'price_asc':
            queryset = queryset.order_by('retail_price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-retail_price')
        elif sort == 'name':
            queryset = queryset.order_by('name')
        elif sort == 'new':
            queryset = queryset.order_by('-created_at')
        elif sort == 'popular':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('sort_order', '-created_at')
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        
        # Підкатегорії для фільтрів
        context['subcategories'] = self.category.children.filter(is_active=True)
        
        # Отримуємо конфігурацію фільтрів для категорії
        try:
            filter_config = self.category.filter_config
        except:
            filter_config = None
        
        context['filter_config'] = filter_config
        
        # Базовий queryset для підрахунку доступних фільтрів
        base_category_ids = [self.category.id] + list(
            self.category.children.filter(is_active=True).values_list('id', flat=True)
        )
        base_queryset = Product.objects.filter(
            category_id__in=base_category_ids,
            is_active=True
        )
        
        # Діапазон цін
        if not filter_config or filter_config.show_price_filter:
            price_range = base_queryset.aggregate(
                min_price=Min('retail_price'),
                max_price=Max('retail_price')
            )
            context['price_range'] = price_range
        
        # Обрані фільтри (для збереження стану)
        context['selected_subcategories'] = self.request.GET.getlist('subcategory')
        context['selected_availability'] = self.request.GET.getlist('availability')
        context['selected_types'] = self.request.GET.getlist('type')
        context['selected_price_min'] = self.request.GET.get('price_min', '')
        context['selected_price_max'] = self.request.GET.get('price_max', '')
        context['selected_sort'] = self.request.GET.get('sort', 'default')
        
        return context


class ProductDetailView(DetailView):
    """Детальна сторінка товару"""
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True)


class SaleProductsView(ListView):
    """Акції - показує тільки товари з активними акціями"""
    model = Product
    template_name = 'products/sale.html'
    context_object_name = 'products'
    paginate_by = 15
    
    def get_queryset(self):
        from django.utils import timezone
        now = timezone.now()
        queryset = Product.objects.filter(
            Q(is_active=True) &
            Q(is_sale=True) &
            (
                Q(sale_start_date__isnull=True, sale_end_date__isnull=True) |
                Q(sale_start_date__isnull=True, sale_end_date__gte=now) |
                Q(sale_start_date__lte=now, sale_end_date__isnull=True) |
                Q(sale_start_date__lte=now, sale_end_date__gte=now)
            )
        ).prefetch_related('images')
        
        sort = self.request.GET.get('sort', 'default')
        if sort == 'name':
            queryset = queryset.order_by('name')
        elif sort == 'price_low':
            queryset = queryset.order_by('retail_price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-retail_price')
        elif sort == 'discount':
            queryset = queryset.order_by('-sale_price')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_sort'] = self.request.GET.get('sort', 'default')
        return context
