"""
Адміністративна панель товарів з розширеним функціоналом
Архітектура: централізоване управління товарами, цінами, акціями, фільтрами
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal

from .models import (
    Category, Product, ProductImage, ProductAttribute, 
    NewProduct, CategoryFilterConfig
)
from .forms import ProductAdminForm


# ============================================
#              INLINE АДМІНІСТРУВАННЯ
# ============================================

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['get_image_preview', 'image', 'alt_text', 'is_main', 'sort_order']
    readonly_fields = ['get_image_preview']
    classes = ['collapse']
    verbose_name = 'Зображення товару'
    verbose_name_plural = '📷 Зображення товару (перше буде головним)'
    
    def get_image_preview(self, obj):
        """Попередній перегляд зображення"""
        if obj.image:
            return format_html(
                '<img src="{}" class="admin-thumbnail" />',
                obj.image.url
            )
        return "Немає зображення"
    get_image_preview.short_description = 'Превью'


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1
    fields = ['name', 'value', 'sort_order']
    classes = ['collapse']
    verbose_name = 'Характеристика'
    verbose_name_plural = '📝 Характеристики товару (об\'єм, бренд, тип тощо)'


class CategoryFilterConfigInline(admin.StackedInline):
    """Inline для конфігурації фільтрів категорії"""
    model = CategoryFilterConfig
    can_delete = False
    verbose_name = 'Конфігурація фільтрів'
    verbose_name_plural = '⚙️ Конфігурація фільтрів для фронтенду'
    
    fieldsets = (
        ('Які фільтри показувати на сайті для цієї категорії', {
            'fields': (
                ('show_brand_filter', 'show_group_filter'),
                ('show_purpose_filter', 'show_price_filter'),
                'show_availability_filter',
            ),
            'description': 'Вкажіть які фільтри будуть доступні користувачам при перегляді товарів цієї категорії'
        }),
    )


# ============================================
#              КАТЕГОРІЇ
# ============================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Адміністрування категорій з конфігурацією фільтрів"""
    
    list_display = ['get_category_image', 'name', 'parent', 'get_products_count', 'get_filter_config', 'is_active', 'sort_order']
    list_display_links = ['get_category_image', 'name']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order', 'name']
    save_on_top = True
    
    inlines = [CategoryFilterConfigInline]
    
    fieldsets = (
        ('📂 Основна інформація', {
            'fields': ('name', 'slug', 'parent', 'image', 'description')
        }),
        ('⚙️ Налаштування', {
            'fields': (('is_active', 'sort_order'),)
        }),
        ('🔍 SEO (необов\'язково)', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )
    
    def get_category_image(self, obj):
        """Мініатюра зображення категорії"""
        if obj.image:
            return format_html(
                '<img src="{}" class="admin-thumbnail-small" />',
                obj.image.url
            )
        return format_html('<div class="admin-icon-placeholder">📂</div>')
    get_category_image.short_description = 'Фото'
    
    def get_products_count(self, obj):
        """Кількість товарів у категорії"""
        count = obj.product_set.filter(is_active=True).count()
        return format_html('<span class="badge badge-info">{}</span>', count)
    get_products_count.short_description = 'Товарів'
    
    def get_filter_config(self, obj):
        """Показує які фільтри активні"""
        try:
            config = obj.filter_config
            filters = []
            if config.show_brand_filter:
                filters.append('Бренд')
            if config.show_group_filter:
                filters.append('Група')
            if config.show_purpose_filter:
                filters.append('Призначення')
            if config.show_price_filter:
                filters.append('Ціна')
            
            if filters:
                return format_html('<span class="filter-tags">{}</span>', ', '.join(filters))
            return '—'
        except CategoryFilterConfig.DoesNotExist:
            return format_html('<span class="text-warning">Не налаштовано</span>')
    get_filter_config.short_description = 'Активні фільтри'
    
    def get_queryset(self, request):
        """Оптимізація запитів"""
        qs = super().get_queryset(request)
        return qs.select_related('parent').prefetch_related('filter_config')
    
    def save_model(self, request, obj, form, change):
        """При збереженні створюємо конфіг фільтрів якщо його немає"""
        super().save_model(request, obj, form, change)
        # Створюємо конфіг фільтрів за замовчуванням
        CategoryFilterConfig.objects.get_or_create(category=obj)
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)


# ============================================
#              ТОВАРИ (ГОЛОВНИЙ РОЗДІЛ)
# ============================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Адміністрування товарів з розширеним функціоналом"""
    
    form = ProductAdminForm
    
    list_display = [
        'get_product_image', 'name', 'category', 'sku', 
        'get_price_display', 'get_sale_status',
        'stock', 'get_status_display', 'get_badges', 'updated_at'
    ]
    list_display_links = ['get_product_image', 'name']
    list_filter = [
        'is_active',
        'category',
        'is_sale',
        'is_top',
        'is_new',
        'is_featured',
        'created_at',
        'updated_at'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['stock']
    ordering = ['sort_order', '-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 50
    save_on_top = True
    
    # Autocomplete для швидкого пошуку
    autocomplete_fields = []
    search_help_text = "Пошук по назві, артикулу або опису товару"
    
    inlines = [ProductImageInline, ProductAttributeInline]
    
    fieldsets = (
        ('📋 Основна інформація', {
            'fields': (
                'name',
                'slug',
                'category',
                'sku',
                'description'
            ),
            'description': 'Назва, категорія та опис товару'
        }),
        ('💰 Ціноутворення', {
            'fields': (
                ('retail_price', 'wholesale_price'),
                ('price_3_qty', 'price_5_qty'),
            ),
            'description': mark_safe('''
                <div class="pricing-help">
                    <strong>Правило цін:</strong> 5+ ≤ 3+ ≤ Оптова ≤ Базова<br>
                    <strong>Роздрібна ціна</strong> — для незареєстрованих<br>
                    <strong>Оптова ціна</strong> — для зареєстрованих оптових клієнтів<br>
                    <strong>Ціна від 3/5 шт</strong> — знижка при покупці від 3 або 5 штук
                </div>
            ''')
        }),
        ('🔥 Акційне ціноутворення', {
            'fields': (
                'is_sale',
                'sale_price',
                ('sale_start_date', 'sale_end_date'),
            ),
            'classes': ('collapse',),
            'description': mark_safe('''
                <div class="sale-help">
                    <strong>Акційна ціна</strong> завжди має бути меншою за роздрібну<br>
                    Якщо не вказано дати - акція постійна<br>
                    Акція автоматично враховується при відображенні на сайті
                </div>
            ''')
        }),
        ('📦 Склад та наявність', {
            'fields': (
                ('stock', 'is_active'),
                'is_featured'
            ),
            'description': 'Кількість товару на складі та статус активності'
        }),
        ('🏷️ Позначки товару (Бейджі)', {
            'fields': (
                ('is_top', 'is_new'),
                'sort_order'
            ),
            'description': mark_safe('''
                <strong>Хіт</strong> — топовий/популярний товар<br>
                <strong>Новинка</strong> — новий товар<br>
                <strong>Акція</strong> — встановлюється автоматично при is_sale=True
            ''')
        }),
        ('🔍 SEO налаштування', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('📅 Системна інформація', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = [
        'activate_products', 
        'deactivate_products',
        'mark_as_sale',
        'unmark_as_sale',
        'mark_as_top',
        'mark_as_new',
        'set_sale_price_bulk',
        'clear_sale_prices',
        'export_to_csv',
    ]
    
    # ========== Методи відображення ==========
    
    def get_product_image(self, obj):
        """Мініатюра головного зображення товару"""
        main_image = obj.images.filter(is_main=True).first() or obj.images.first()
        if main_image:
            return format_html(
                '<img src="{}" class="admin-thumbnail-small" />',
                main_image.image.url
            )
        return format_html('<div class="admin-icon-placeholder">📦</div>')
    get_product_image.short_description = 'Фото'
    
    def get_price_display(self, obj):
        """Відображення цін"""
        prices = []
        prices.append(f"<strong>{obj.retail_price} ₴</strong>")
        
        if obj.wholesale_price:
            prices.append(f"Опт: {obj.wholesale_price} ₴")
        
        if obj.price_3_qty:
            prices.append(f"3+: {obj.price_3_qty} ₴")
        
        if obj.price_5_qty:
            prices.append(f"5+: {obj.price_5_qty} ₴")
        
        return format_html('<div class="price-stack">{}</div>', '<br>'.join(prices))
    get_price_display.short_description = 'Ціни'
    
    def get_sale_status(self, obj):
        """Статус акції"""
        if obj.is_sale and obj.sale_price:
            if obj.is_sale_active():
                discount = obj.get_discount_percentage()
                info = f'<span class="badge badge-sale">{obj.sale_price} ₴ (-{discount}%)</span>'
                
                if obj.sale_end_date:
                    days_left = (obj.sale_end_date - timezone.now()).days
                    if days_left <= 3:
                        info += f'<br><span class="text-danger">⏰ {days_left} дн.</span>'
                    else:
                        info += f'<br><span class="text-muted">{days_left} дн.</span>'
                
                return format_html(info)
            else:
                return format_html('<span class="badge badge-inactive">Неактивна</span>')
        return '—'
    get_sale_status.short_description = 'Акція'
    
    def get_status_display(self, obj):
        """Відображення статусу товару"""
        if obj.is_active:
            if obj.stock > 0:
                return format_html('<span class="status-active">● В наявності</span>')
            else:
                return format_html('<span class="status-warning">⚠ Немає на складі</span>')
        return format_html('<span class="status-inactive">✕ Неактивний</span>')
    get_status_display.short_description = 'Статус'
    
    def get_badges(self, obj):
        """Відображення бейджів"""
        stickers = obj.get_stickers()
        if not stickers:
            return '—'
        
        badges_html = []
        for sticker in stickers:
            badges_html.append(f'<span class="badge {sticker["class"]}">{sticker["text"]}</span>')
        
        return format_html(' '.join(badges_html))
    get_badges.short_description = 'Бейджі'
    
    # ========== Масові дії ==========
    
    def activate_products(self, request, queryset):
        """Активувати товари"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активовано {updated} товарів", messages.SUCCESS)
    activate_products.short_description = "✓ Активувати обрані товари"
    
    def deactivate_products(self, request, queryset):
        """Деактивувати товари"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивовано {updated} товарів", messages.SUCCESS)
    deactivate_products.short_description = "✕ Деактивувати обрані товари"
    
    def mark_as_sale(self, request, queryset):
        """Позначити як акційні"""
        count = 0
        for product in queryset:
            if product.sale_price:
                product.is_sale = True
                product.save(update_fields=['is_sale'])
                count += 1
        
        self.message_user(
            request, 
            f"Позначено як акційні: {count} товарів. Товари без вказаної акційної ціни пропущено.",
            messages.WARNING if count < queryset.count() else messages.SUCCESS
        )
    mark_as_sale.short_description = "🔥 Позначити як АКЦІЙНІ"
    
    def unmark_as_sale(self, request, queryset):
        """Зняти позначку акційний"""
        updated = queryset.update(is_sale=False)
        self.message_user(request, f"Знято позначку акційний: {updated} товарів", messages.SUCCESS)
    unmark_as_sale.short_description = "Зняти позначку АКЦІЙНИЙ"
    
    def mark_as_top(self, request, queryset):
        """Позначити як ХІТ"""
        updated = queryset.update(is_top=True)
        self.message_user(request, f"Позначено як ХІТ: {updated} товарів", messages.SUCCESS)
    mark_as_top.short_description = "⭐ Позначити як ХІТ"
    
    def mark_as_new(self, request, queryset):
        """Позначити як новинки"""
        updated = queryset.update(is_new=True)
        self.message_user(request, f"Позначено як новинки: {updated} товарів", messages.SUCCESS)
    mark_as_new.short_description = "✨ Позначити як НОВИНКИ"
    
    def clear_sale_prices(self, request, queryset):
        """Очистити акційні ціни"""
        queryset.update(
            is_sale=False,
            sale_price=None,
            sale_start_date=None,
            sale_end_date=None
        )
        self.message_user(request, f"Акційні ціни очищено для {queryset.count()} товарів", messages.SUCCESS)
    clear_sale_prices.short_description = "🗑️ Очистити акційні ціни"
    
    def export_to_csv(self, request, queryset):
        """Експорт товарів у CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
        response.write('\ufeff')  # BOM для коректного відображення кирилиці в Excel
        
        writer = csv.writer(response)
        writer.writerow([
            'SKU', 'Назва', 'Категорія', 'Роздрібна ціна', 'Оптова ціна',
            'Акційна ціна', 'Кількість', 'Статус'
        ])
        
        for product in queryset:
            writer.writerow([
                product.sku,
                product.name,
                product.category.name,
                product.retail_price,
                product.wholesale_price or '',
                product.sale_price or '',
                product.stock,
                'Активний' if product.is_active else 'Неактивний'
            ])
        
        self.message_user(request, f"Експортовано {queryset.count()} товарів", messages.SUCCESS)
        return response
    export_to_csv.short_description = "📊 Експортувати в CSV"
    
    # ========== Оптимізація ==========
    
    def get_queryset(self, request):
        """Оптимізуємо запити"""
        qs = super().get_queryset(request)
        return qs.select_related('category').prefetch_related('images')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Налаштування падаючого списку для категорій"""
        if db_field.name == "category":
            kwargs["queryset"] = Category.objects.filter(is_active=True).order_by('sort_order', 'name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)

# ============================================
#       НОВИНКИ, АКЦІЙНІ ПРОПОЗИЦІЇ
# ============================================

@admin.register(NewProduct)
class NewProductAdmin(admin.ModelAdmin):
    """Адміністрування новинок на головній сторінці"""
    
    list_display = ['product', 'get_is_new_status', 'sort_order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['product__name', 'product__sku']
    list_editable = ['sort_order']
    ordering = ['sort_order', '-created_at']
    autocomplete_fields = ['product']
    
    fieldsets = (
        (None, {
            'fields': ('product', 'sort_order', 'is_active'),
            'description': '✨ Додайте товар в блок "Новинки" на головній сторінці. Товар автоматично отримає статус "Новинка".'
        }),
    )
    
    def get_is_new_status(self, obj):
        """Відображення статусу is_new товару"""
        if obj.product.is_new:
            return format_html('<span class="badge badge-success">✅ Новинка</span>')
        return format_html('<span class="badge badge-danger">❌ Не новинка</span>')
    get_is_new_status.short_description = 'Статус NEW'
    
    def save_model(self, request, obj, form, change):
        """При збереженні встановлюємо is_new=True для товару"""
        super().save_model(request, obj, form, change)
        if not obj.product.is_new:
            obj.product.is_new = True
            obj.product.save(update_fields=['is_new'])
        self.message_user(request, f'✅ Товар "{obj.product.name}" додано в новинки і позначено статусом NEW')
    
    def delete_model(self, request, obj):
        """При видаленні знімаємо is_new з товару"""
        product_name = obj.product.name
        obj.product.is_new = False
        obj.product.save(update_fields=['is_new'])
        super().delete_model(request, obj)
        self.message_user(request, f'❌ Товар "{product_name}" видалено з новинок і знято статус NEW')
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)

# ============================================
#       НАЛАШТУВАННЯ ГРУПУВАННЯ В АДМІНЦІ
# ============================================

# Додаємо verbose_name_plural для правильного групування
Product._meta.verbose_name = "Товар"
Product._meta.verbose_name_plural = "📦 Товари"
Product._meta.app_label = "products"

Category._meta.verbose_name = "Категорія"
Category._meta.verbose_name_plural = "📂 Категорії"

NewProduct._meta.verbose_name = "Новинка"
NewProduct._meta.verbose_name_plural = "✨ Новинки"
