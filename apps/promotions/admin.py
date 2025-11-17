"""
Адмін панель для акцій та промокодів
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django import forms
from .models import Promotion, PromoCode
from apps.core.admin_utils import AdminMediaMixin


class PromotionAdminForm(forms.ModelForm):
    """Форма для валідації акцій"""
    
    class Meta:
        model = Promotion
        fields = '__all__'
    
    def clean(self):
        """Викликаємо валідацію моделі"""
        cleaned_data = super().clean()
        
        # Створюємо тимчасовий об'єкт для валідації
        instance = self.instance
        for field, value in cleaned_data.items():
            setattr(instance, field, value)
        
        # Викликаємо clean() моделі для валідації
        try:
            instance.clean()
        except Exception as e:
            # ValidationError буде автоматично оброблений Django
            raise
        
        return cleaned_data


@admin.register(Promotion)
class PromotionAdmin(AdminMediaMixin, admin.ModelAdmin):
    """Адміністрування акцій"""
    
    form = PromotionAdminForm
    
    list_display = [
        'name', 'get_period', 'get_time_left', 'get_discounts', 
        'get_products_count', 'priority', 'get_active_status'
    ]
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    filter_horizontal = ['products', 'categories']
    date_hierarchy = 'start_date'
    ordering = ['-priority', '-start_date']
    save_on_top = True
    
    fieldsets = (
        ('📋 Основна інформація', {
            'fields': ('name', 'description', 'priority')
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
    
    def get_time_left(self, obj):
        """Лишилось часу до закінчення акції"""
        now = timezone.now()
        
        if obj.end_date < now:
            return format_html('<span class="badge badge-secondary">Завершена</span>')
        elif obj.start_date > now:
            days_until_start = (obj.start_date - now).days
            return format_html('<span class="badge badge-warning">Почнеться через {} дн.</span>', days_until_start)
        else:
            days_left = (obj.end_date - now).days
            hours_left = ((obj.end_date - now).seconds // 3600)
            if days_left > 0:
                return format_html('<span class="badge badge-success">{} дн.</span>', days_left)
            elif hours_left > 0:
                return format_html('<span class="badge badge-warning">{} год.</span>', hours_left)
            else:
                return format_html('<span class="badge badge-danger">Закінчується</span>')
    get_time_left.short_description = 'Лишилось часу'
    
    def get_active_status(self, obj):
        """Статус активності акції"""
        if obj.is_active:
            return format_html('<span class="badge badge-success">✓ Активна</span>')
        else:
            return format_html('<span class="badge badge-secondary">Не активна</span>')
    get_active_status.short_description = 'Статус'
    
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
    
    def save_model(self, request, obj, form, change):
        """Зберігає акцію і автоматично застосовує якщо активна"""
        from django.contrib import messages
        from django.utils import timezone
        
        # Зберігаємо old_is_active для порівняння
        old_is_active = None
        if change:
            # Отримуємо старий стан з БД
            old_obj = Promotion.objects.get(pk=obj.pk)
            old_is_active = old_obj.is_active
        
        # Зберігаємо об'єкт
        super().save_model(request, obj, form, change)
        
        # Перевіряємо чи потрібно автоматично застосувати/зняти акцію
        now = timezone.now()
        is_in_period = obj.start_date <= now <= obj.end_date
        
        if obj.is_active and is_in_period:
            # Акція активна і в межах періоду - застосовуємо
            if not change or (change and old_is_active is False):
                # Новa акція або щойно активована - застосовуємо
                count = obj.apply_to_products()
                self.message_user(
                    request, 
                    f'✅ Акцію "{obj.name}" збережено і автоматично застосовано до {count} товарів', 
                    messages.SUCCESS
                )
            else:
                self.message_user(
                    request, 
                    f'✅ Акцію "{obj.name}" оновлено. Якщо потрібно перезастосувати - використайте дію "Активувати акції"', 
                    messages.SUCCESS
                )
        elif change and old_is_active is True and obj.is_active is False:
            # Акція була деактивована - знімаємо з товарів
            count = obj.remove_from_products()
            self.message_user(
                request, 
                f'✅ Акцію "{obj.name}" деактивовано і знято з {count} товарів', 
                messages.SUCCESS
            )
        else:
            # Просто збереження без змін активності
            if not is_in_period and obj.is_active:
                self.message_user(
                    request, 
                    f'⚠️ Акція "{obj.name}" збережена, але не в періоді дії. Вона буде застосована автоматично коли почнеться', 
                    messages.WARNING
                )
            else:
                self.message_user(
                    request, 
                    f'✅ Акцію "{obj.name}" збережено', 
                    messages.SUCCESS
                )
    
    actions = ['activate_promotions', 'deactivate_promotions', 'delete_promotions']
    
    def activate_promotions(self, request, queryset):
        """Активувати акції та застосувати до товарів"""
        total_promotions = 0
        total_products = 0
        
        for promotion in queryset:
            promotion.is_active = True
            promotion.save()
            total_promotions += 1
            
            count = promotion.apply_to_products()
            total_products += count
        
        from django.contrib import messages
        self.message_user(
            request, 
            f'✅ Активовано {total_promotions} акцій та застосовано до {total_products} товарів', 
            messages.SUCCESS
        )
    activate_promotions.short_description = '✓ Активувати акції'
    
    def deactivate_promotions(self, request, queryset):
        """Деактивувати акції та зняти з товарів"""
        total_promotions = 0
        total_products = 0
        
        for promotion in queryset:
            count = promotion.remove_from_products()
            total_products += count
            
            promotion.is_active = False
            promotion.save()
            total_promotions += 1
        
        from django.contrib import messages
        self.message_user(
            request, 
            f'✅ Деактивовано {total_promotions} акцій, знято з {total_products} товарів', 
            messages.SUCCESS
        )
    deactivate_promotions.short_description = '✕ Деактивувати акції'
    
    def delete_promotions(self, request, queryset):
        """Видалити обрані акції"""
        total_products = 0
        for promotion in queryset:
            if promotion.is_active:
                count = promotion.remove_from_products()
                total_products += count
        
        count = queryset.count()
        queryset.delete()
        
        from django.contrib import messages
        self.message_user(
            request, 
            f'✅ Видалено {count} акцій, знято з {total_products} товарів', 
            messages.SUCCESS
        )
    delete_promotions.short_description = '🗑 Видалити обрані акції'
    
    def get_actions(self, request):
        """Видаляємо стандартну дію видалення"""
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions


@admin.register(PromoCode)
class PromoCodeAdmin(AdminMediaMixin, admin.ModelAdmin):
    """Адміністрування промокодів"""
    
    list_display = [
        'code', 'get_discount', 'get_usage', 'get_period', 
        'get_status', 'min_order_amount'
    ]
    list_filter = ['discount_type', 'start_date', 'end_date']
    search_fields = ['code']
    readonly_fields = ['used_count']
    date_hierarchy = 'start_date'
    ordering = ['-created_at']
    save_on_top = True
    
    fieldsets = (
        ('📋 Основна інформація', {
            'fields': ('code',)
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
        value = float(obj.discount_value)
        if obj.discount_type == 'percentage':
            return format_html('<strong>-{}%</strong>', f'{value:.2f}')
        else:
            return format_html('<strong>-{} ₴</strong>', f'{value:.2f}')
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


# Налаштування відображення в адмінці
Promotion._meta.verbose_name = 'Акція'
Promotion._meta.verbose_name_plural = 'Акції'

PromoCode._meta.verbose_name = 'Промокод'
PromoCode._meta.verbose_name_plural = 'Промокоди'
