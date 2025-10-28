"""
Адміністративна панель для замовлень
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    can_delete = True
    fields = ['product', 'quantity', 'price']
    
    def has_add_permission(self, request, obj=None):
        """Дозволити додавання тільки при редагуванні існуючого замовлення"""
        if obj and obj.pk:
            return True
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Адміністрування замовлень з розширеними фільтрами"""
    
    list_display = [
        'order_number', 'get_customer_name', 'get_status_badge',
        'get_total_display', 'payment_method', 'get_payment_status', 'created_at'
    ]
    list_filter = [
        'status', 
        'payment_method', 
        'delivery_method', 
        'is_paid', 
        ('created_at', admin.DateFieldListFilter),
    ]
    search_fields = [
        'order_number', 'first_name', 'last_name', 
        'email', 'phone', 'delivery_city'
    ]
    readonly_fields = [
        'order_number', 'created_at', 'updated_at',
        'get_total_cost', 'get_customer_info', 'get_items_list'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    inlines = [OrderItemInline]
    
    def has_add_permission(self, request):
        """Заборонити створення замовлень через адмінку"""
        return False
    
    fieldsets = (
        ('📋 Основна інформація', {
            'fields': ('order_number', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('🛒 Товари', {
            'fields': ('get_items_list',),
            'description': 'Товари в замовленні'
        }),
        ('👤 Клієнт', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'get_customer_info')
        }),
        ('🚚 Доставка', {
            'fields': (
                'delivery_method', 'delivery_city', 
                'delivery_address', 'delivery_cost'
            )
        }),
        ('💳 Оплата', {
            'fields': (
                'payment_method', 'is_paid', 'payment_date',
                'subtotal', 'discount', 'total'
            )
        }),
        ('📝 Примітки', {
            'fields': ('notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered',
        'export_orders_csv', 'send_order_confirmation'
    ]
    
    def get_queryset(self, request):
        """Оптимізуємо запити"""
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')
    
    def get_status_badge(self, obj):
        """Відображення статусу з кольоровим бейджем"""
        status_colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'processing': 'info',
            'shipped': 'primary',
            'delivered': 'success',
            'cancelled': 'danger',
            'completed': 'success',
        }
        color = status_colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'
    
    def get_payment_status(self, obj):
        """Статус оплати"""
        if obj.is_paid:
            return format_html('<span class="badge badge-success">✓ Оплачено</span>')
        return format_html('<span class="badge badge-warning">⏳ Не оплачено</span>')
    get_payment_status.short_description = 'Оплата'
    
    def get_total_display(self, obj):
        """Загальна сума"""
        return format_html('<strong>{:.2f} ₴</strong>', obj.total)
    get_total_display.short_description = 'Сума'
    
    def get_customer_info(self, obj):
        """Інформація про клієнта"""
        if obj.user:
            return format_html(
                '<strong>{}</strong><br>📧 {}<br>📞 {}<br>🔥 Оптовий клієнт',
                obj.get_customer_name(),
                obj.email,
                obj.phone
            )
        return format_html(
            '<strong>{}</strong><br>📧 {}<br>📞 {}<br>👤 Гість',
            obj.get_customer_name(),
            obj.email,
            obj.phone
        )
    get_customer_info.short_description = "Інформація про клієнта"
    
    def get_items_list(self, obj):
        """Список товарів в замовленні"""
        items = obj.items.all()
        if not items:
            return "Немає товарів"
        
        html = '<table style="width:100%; border-collapse: collapse;">'
        html += '<tr style="background: #f7fafc;"><th style="padding: 8px; text-align: left;">Товар</th><th style="padding: 8px;">Кількість</th><th style="padding: 8px;">Ціна</th><th style="padding: 8px;">Сума</th></tr>'
        
        for item in items:
            html += f'''
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 8px;">{item.product.name}</td>
                    <td style="padding: 8px; text-align: center;">{item.quantity} шт</td>
                    <td style="padding: 8px; text-align: right;">{item.price} ₴</td>
                    <td style="padding: 8px; text-align: right;"><strong>{item.get_cost()} ₴</strong></td>
                </tr>
            '''
        
        html += f'''
            <tr style="background: #f7fafc; font-weight: bold;">
                <td colspan="3" style="padding: 8px; text-align: right;">Разом:</td>
                <td style="padding: 8px; text-align: right;">{obj.subtotal} ₴</td>
            </tr>
        '''
        
        if obj.delivery_cost > 0:
            html += f'''
                <tr>
                    <td colspan="3" style="padding: 8px; text-align: right;">Доставка:</td>
                    <td style="padding: 8px; text-align: right;">{obj.delivery_cost} ₴</td>
                </tr>
            '''
        
        if obj.discount > 0:
            html += f'''
                <tr style="color: #f56565;">
                    <td colspan="3" style="padding: 8px; text-align: right;">Знижка:</td>
                    <td style="padding: 8px; text-align: right;">-{obj.discount} ₴</td>
                </tr>
            '''
        
        html += f'''
            <tr style="background: #ebf8ff; font-weight: bold; font-size: 16px;">
                <td colspan="3" style="padding: 8px; text-align: right;">Всього до сплати:</td>
                <td style="padding: 8px; text-align: right; color: #4299e1;">{obj.total} ₴</td>
            </tr>
        '''
        
        html += '</table>'
        return format_html(html)
    get_items_list.short_description = "Товари в замовленні"
    
    def get_total_cost(self, obj):
        """Загальна вартість з доставкою"""
        return format_html(
            '<strong style="color: green;">{:.2f} грн</strong>',
            obj.get_total_cost()
        )
    get_total_cost.short_description = "Загальна вартість"
    
    def mark_as_confirmed(self, request, queryset):
        """Підтвердити замовлення"""
        updated = queryset.update(status='confirmed')
        self.message_user(request, f"Підтверджено {updated} замовлень")
    
    mark_as_confirmed.short_description = "Підтвердити замовлення"
    
    def mark_as_shipped(self, request, queryset):
        """Відправити замовлення"""
        updated = queryset.update(status='shipped')
        self.message_user(request, f"Відправлено {updated} замовлень")
    
    mark_as_shipped.short_description = "Відправити замовлення"
    
    def mark_as_delivered(self, request, queryset):
        """Доставлено замовлення"""
        updated = queryset.update(status='delivered')
        self.message_user(request, f"Доставлено {updated} замовлень")
    
    mark_as_delivered.short_description = "Доставлено замовлення"
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)


# Налаштування відображення в адмінці
Order._meta.verbose_name = "Замовлення"
Order._meta.verbose_name_plural = "📦 Замовлення"
