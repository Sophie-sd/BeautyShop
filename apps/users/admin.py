"""
Адміністративна панель для клієнтів
"""
from django.contrib import admin
from django.contrib.auth.models import Group
from django.db.models import Count, Max
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import CustomUser, UserProfile, WholesaleClient
from apps.core.admin_utils import AdminMediaMixin


class UserProfileInline(admin.StackedInline):
    """Інлайн для профілю користувача"""
    model = UserProfile
    can_delete = False
    verbose_name = 'Профіль'
    verbose_name_plural = 'Профіль'
    fields = ['company_name', 'tax_number', 'address', 'notes']


class WholesaleClientAdmin(AdminMediaMixin, admin.ModelAdmin):
    """Адмінка для оптових клієнтів - тільки перегляд"""
    
    list_display = ['get_full_name_display', 'email', 'get_phone_display', 'get_orders_count', 'get_total_amount', 'get_avg_order', 'get_last_order_date', 'get_last_login_display']
    list_filter = ['email_verified', 'is_active', 'created_at', 'last_login']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'middle_name', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        ('👤 Персональні дані', {
            'fields': ('get_full_name_readonly', 'email', 'phone'),
        }),
        ('📊 Статистика замовлень', {
            'fields': ('get_orders_stats', 'get_orders_timeline'),
        }),
        ('📅 Дати та статус', {
            'fields': ('email_verified', 'is_active', 'date_joined', 'last_login', 'created_at'),
        }),
    )
    
    readonly_fields = [
        'get_full_name_readonly', 'email', 'phone', 
        'get_orders_stats', 'get_orders_timeline',
        'email_verified', 'is_active', 'date_joined', 'last_login', 'created_at'
    ]
    
    def get_queryset(self, request):
        """Показуємо тільки оптових клієнтів з анотаціями"""
        from django.db.models import Sum
        qs = super().get_queryset(request)
        return qs.filter(is_wholesale=True).annotate(
            orders_count=Count('order'),
            total_spent=Sum('order__total'),
            last_order_date=Max('order__created_at')
        )
    
    def get_full_name_display(self, obj):
        """Повне ім'я для таблиці"""
        parts = []
        if obj.last_name:
            parts.append(obj.last_name)
        if obj.first_name:
            parts.append(obj.first_name)
        if obj.middle_name:
            parts.append(obj.middle_name)
        return ' '.join(parts) if parts else 'не вказано'
    get_full_name_display.short_description = 'ПІБ'
    get_full_name_display.admin_order_field = 'last_name'
    
    def get_full_name_readonly(self, obj):
        """Повне ім'я для форми"""
        return format_html(
            '<strong style="font-size: 16px;">{}</strong>',
            self.get_full_name_display(obj)
        )
    get_full_name_readonly.short_description = 'ПІБ'
    
    def get_phone_display(self, obj):
        """Телефон"""
        return obj.phone if obj.phone else 'не вказано'
    get_phone_display.short_description = 'Телефон'
    
    def get_orders_count(self, obj):
        """Кількість замовлень"""
        count = obj.orders_count if hasattr(obj, 'orders_count') else obj.order_set.count()
        return format_html('<strong>{}</strong>', count)
    get_orders_count.short_description = 'Замовлень'
    get_orders_count.admin_order_field = 'orders_count'
    
    def get_total_amount(self, obj):
        """Загальна сума замовлень"""
        total = obj.total_spent if hasattr(obj, 'total_spent') else 0
        if total:
            return format_html('<strong>{:.2f} ₴</strong>', float(total))
        return '—'
    get_total_amount.short_description = 'Загальна сума'
    get_total_amount.admin_order_field = 'total_spent'
    
    def get_avg_order(self, obj):
        """Середній чек"""
        count = obj.orders_count if hasattr(obj, 'orders_count') else obj.order_set.count()
        total = obj.total_spent if hasattr(obj, 'total_spent') else 0
        if count and total:
            avg = float(total) / count
            return format_html('<strong>{:.2f} ₴</strong>', avg)
        return '—'
    get_avg_order.short_description = 'Середній чек'
    
    def get_last_order_date(self, obj):
        """Дата останнього замовлення"""
        if hasattr(obj, 'last_order_date') and obj.last_order_date:
            from django.utils import timezone
            now = timezone.now()
            diff = now - obj.last_order_date
            days = diff.days
            
            date_str = obj.last_order_date.strftime('%d.%m.%Y о %H:%M')
            if days == 0:
                return format_html('<span style="color: #28a745;">{} (сьогодні)</span>', date_str)
            elif days < 7:
                return format_html('<span style="color: #ffc107;">{} ({} дн. тому)</span>', date_str, days)
            else:
                return date_str
        return 'не робив замовлень'
    get_last_order_date.short_description = 'Останнє замовлення'
    get_last_order_date.admin_order_field = 'last_order_date'
    
    def get_last_login_display(self, obj):
        """Дата останнього заходу"""
        if obj.last_login:
            from django.utils import timezone
            now = timezone.now()
            diff = now - obj.last_login
            days = diff.days
            
            date_str = obj.last_login.strftime('%d.%m.%Y о %H:%M')
            if days == 0:
                return format_html('<span style="color: #28a745;">{} (сьогодні)</span>', date_str)
            elif days < 7:
                return format_html('<span style="color: #ffc107;">{} ({} дн. тому)</span>', date_str, days)
            else:
                return date_str
        return 'ще не заходив'
    get_last_login_display.short_description = 'Останній вхід'
    get_last_login_display.admin_order_field = 'last_login'
    
    def get_orders_stats(self, obj):
        """Детальна статистика замовлень"""
        from apps.orders.models import Order
        
        orders = Order.objects.filter(user=obj)
        count = orders.count()
        
        if not count:
            return format_html('<p style="color: #6c757d;">Клієнт ще не робив замовлень</p>')
        
        total = sum(float(o.total) for o in orders)
        avg = total / count if count else 0
        
        paid_count = orders.filter(is_paid=True).count()
        completed_count = orders.filter(status='completed').count()
        
        html = f'''
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff;">
            <div style="margin-bottom: 8px;">
                <strong>Всього замовлень:</strong> {count}
            </div>
            <div style="margin-bottom: 8px;">
                <strong>Загальна сума:</strong> <span style="color: #28a745; font-weight: 600;">{total:.2f} ₴</span>
            </div>
            <div style="margin-bottom: 8px;">
                <strong>Середній чек:</strong> <span style="color: #007bff; font-weight: 600;">{avg:.2f} ₴</span>
            </div>
            <div style="margin-bottom: 8px;">
                <strong>Оплачено:</strong> {paid_count} з {count}
            </div>
            <div>
                <strong>Завершено:</strong> {completed_count} з {count}
            </div>
        </div>
        '''
        return mark_safe(html)
    get_orders_stats.short_description = 'Статистика'
    
    def get_orders_timeline(self, obj):
        """Останні 5 замовлень"""
        from apps.orders.models import Order
        
        orders = Order.objects.filter(user=obj).order_by('-created_at')[:5]
        
        if not orders:
            return format_html('<p style="color: #6c757d;">Немає замовлень</p>')
        
        html = '<div style="background: #fff; border: 1px solid #dee2e6; border-radius: 8px; overflow: hidden;">'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #f8f9fa;"><th style="padding: 8px; text-align: left; font-size: 12px;">№</th><th style="padding: 8px; text-align: left; font-size: 12px;">Дата</th><th style="padding: 8px; text-align: right; font-size: 12px;">Сума</th><th style="padding: 8px; text-align: center; font-size: 12px;">Статус</th></tr>'
        
        for order in orders:
            status_colors = {
                'pending': '#ffc107',
                'confirmed': '#17a2b8',
                'shipped': '#fd7e14',
                'delivered': '#28a745',
                'completed': '#218838',
                'cancelled': '#dc3545',
            }
            color = status_colors.get(order.status, '#6c757d')
            
            html += f'''
            <tr style="border-bottom: 1px solid #dee2e6;">
                <td style="padding: 8px; font-size: 12px;">{order.order_number}</td>
                <td style="padding: 8px; font-size: 12px;">{order.created_at.strftime('%d.%m.%Y %H:%M')}</td>
                <td style="padding: 8px; text-align: right; font-weight: 600; font-size: 12px;">{float(order.total):.2f} ₴</td>
                <td style="padding: 8px; text-align: center;"><span style="padding: 2px 8px; background: {color}; color: white; border-radius: 4px; font-size: 11px;">{order.get_status_display()}</span></td>
            </tr>
            '''
        
        html += '</table></div>'
        
        if orders.count() == 5:
            from django.urls import reverse
            url = reverse('admin:orders_order_changelist') + f'?user__id__exact={obj.id}'
            html += f'<p style="margin-top: 10px;"><a href="{url}" style="color: #007bff;">Переглянути всі замовлення →</a></p>'
        
        return mark_safe(html)
    get_orders_timeline.short_description = 'Останні замовлення'
    
    def has_add_permission(self, request):
        """Заборона створення"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Заборона видалення"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Дозволити тільки перегляд"""
        return True
    
    def save_model(self, request, obj, form, change):
        """Заборона збереження змін"""
        pass


admin.site.register(WholesaleClient, WholesaleClientAdmin)
admin.site.unregister(Group)

WholesaleClient._meta.verbose_name = 'Оптовий клієнт'
WholesaleClient._meta.verbose_name_plural = '💼 2. Оптові клієнти'
WholesaleClient._meta.app_label = 'users'
