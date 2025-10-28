"""
Адмін панель для акцій та промокодів
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Promotion, PromoCode


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    """Адміністрування акцій"""
    
    list_display = [
        'name', 'get_period', 'get_status', 'get_discounts', 
        'get_products_count', 'priority', 'is_active'
    ]
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['products', 'categories']
    date_hierarchy = 'start_date'
    ordering = ['-priority', '-start_date']
    save_on_top = True
    
    fieldsets = (
        ('📋 Основна інформація', {
            'fields': ('name', 'description', 'is_active', 'priority')
        }),
        ('🎯 Товари та категорії', {
            'fields': ('products', 'categories'),
            'description': 'Оберіть конкретні товари або цілі категорії для застосування акції'
        }),
        ('💰 Знижки на різні типи цін', {
            'fields': (
                'retail_discount_percent',
                'wholesale_discount_percent',
                'qty3_discount_percent',
                'qty5_discount_percent',
            ),
            'description': 'Вкажіть відсоток знижки для кожного типу ціни. Залиште порожнім, якщо знижка не потрібна'
        }),
        ('📅 Період дії', {
            'fields': (('start_date', 'end_date'),)
        }),
    )
    
    def get_period(self, obj):
        """Відображення періоду"""
        start = obj.start_date.strftime('%d.%m.%Y')
        end = obj.end_date.strftime('%d.%m.%Y')
        return f"{start} - {end}"
    get_period.short_description = 'Період'
    
    def get_status(self, obj):
        """Статус акції"""
        if obj.is_valid():
            days_left = (obj.end_date - timezone.now()).days
            return format_html(
                '<span class="badge badge-success">Активна ({} дн.)</span>',
                days_left
            )
        elif obj.end_date < timezone.now():
            return format_html('<span class="badge badge-secondary">Завершена</span>')
        else:
            return format_html('<span class="badge badge-warning">Очікується</span>')
    get_status.short_description = 'Статус'
    
    def get_discounts(self, obj):
        """Відображення знижок"""
        discounts = []
        if obj.retail_discount_percent:
            discounts.append(f"Роздріб: {obj.retail_discount_percent}%")
        if obj.wholesale_discount_percent:
            discounts.append(f"Опт: {obj.wholesale_discount_percent}%")
        if obj.qty3_discount_percent:
            discounts.append(f"3+: {obj.qty3_discount_percent}%")
        if obj.qty5_discount_percent:
            discounts.append(f"5+: {obj.qty5_discount_percent}%")
        return format_html('<br>'.join(discounts)) if discounts else '—'
    get_discounts.short_description = 'Знижки'
    
    def get_products_count(self, obj):
        """Кількість товарів"""
        direct = obj.products.count()
        from_categories = 0
        for cat in obj.categories.all():
            from_categories += cat.product_set.filter(is_active=True).count()
        
        total = direct + from_categories
        return format_html('<span class="badge badge-info">{} товарів</span>', total)
    get_products_count.short_description = 'Товарів'
    
    actions = ['apply_to_products_action', 'remove_from_products_action', 'activate', 'deactivate']
    
    def apply_to_products_action(self, request, queryset):
        """Застосувати акції до товарів"""
        total = 0
        for promotion in queryset:
            if promotion.is_valid():
                count = promotion.apply_to_products()
                total += count
        from django.contrib import messages
        self.message_user(request, f'✅ Застосовано акції до {total} товарів', messages.SUCCESS)
    apply_to_products_action.short_description = '✓ Застосувати акції до товарів'
    
    def remove_from_products_action(self, request, queryset):
        """Видалити акції з товарів"""
        total = 0
        for promotion in queryset:
            count = promotion.remove_from_products()
            total += count
        from django.contrib import messages
        self.message_user(request, f'❌ Видалено акції з {total} товарів', messages.SUCCESS)
    remove_from_products_action.short_description = '✕ Видалити акції з товарів'
    
    def activate(self, request, queryset):
        """Активувати акції"""
        updated = queryset.update(is_active=True)
        from django.contrib import messages
        self.message_user(request, f'✅ Активовано {updated} акцій', messages.SUCCESS)
    activate.short_description = '✓ Активувати акції'
    
    def deactivate(self, request, queryset):
        """Деактивувати акції"""
        updated = queryset.update(is_active=False)
        from django.contrib import messages
        self.message_user(request, f'❌ Деактивовано {updated} акцій', messages.SUCCESS)
    deactivate.short_description = '✕ Деактивувати акції'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    """Адміністрування промокодів"""
    
    list_display = [
        'code', 'get_discount', 'get_usage', 'get_period', 
        'get_status', 'min_order_amount', 'is_active'
    ]
    list_filter = ['is_active', 'discount_type', 'start_date', 'end_date']
    search_fields = ['code', 'description']
    readonly_fields = ['used_count']
    date_hierarchy = 'start_date'
    ordering = ['-created_at']
    save_on_top = True
    
    fieldsets = (
        ('📋 Основна інформація', {
            'fields': ('code', 'description', 'is_active')
        }),
        ('💰 Знижка', {
            'fields': (
                ('discount_type', 'discount_value'),
                'min_order_amount',
            )
        }),
        ('📊 Обмеження використання', {
            'fields': (('max_uses', 'used_count'),),
            'description': 'Залиште "Максимум використань" порожнім для необмеженої кількості'
        }),
        ('📅 Період дії', {
            'fields': (('start_date', 'end_date'),)
        }),
    )
    
    def get_discount(self, obj):
        """Відображення знижки"""
        if obj.discount_type == 'percentage':
            return format_html('<strong>-{}%</strong>', obj.discount_value)
        else:
            return format_html('<strong>-{} ₴</strong>', obj.discount_value)
    get_discount.short_description = 'Знижка'
    
    def get_usage(self, obj):
        """Статистика використання"""
        if obj.max_uses:
            percent = (obj.used_count / obj.max_uses) * 100
            color = 'success' if percent < 80 else 'warning' if percent < 100 else 'danger'
            return format_html(
                '<span class="badge badge-{}">{}/{}</span>',
                color, obj.used_count, obj.max_uses
            )
        return format_html('<span class="badge badge-info">{}</span>', obj.used_count)
    get_usage.short_description = 'Використано'
    
    def get_period(self, obj):
        """Відображення періоду"""
        start = obj.start_date.strftime('%d.%m.%Y')
        end = obj.end_date.strftime('%d.%m.%Y')
        return f"{start} - {end}"
    get_period.short_description = 'Період'
    
    def get_status(self, obj):
        """Статус промокоду"""
        is_valid, message = obj.is_valid()
        if is_valid:
            return format_html('<span class="badge badge-success">✓ Активний</span>')
        else:
            return format_html('<span class="badge badge-danger">{}</span>', message)
    get_status.short_description = 'Статус'
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)

