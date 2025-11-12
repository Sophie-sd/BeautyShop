"""
Адміністративна панель для клієнтів
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, Max
from .models import CustomUser, UserProfile, WholesaleClient
from apps.core.admin_utils import AdminMediaMixin


class UserProfileInline(admin.StackedInline):
    """Інлайн для профілю користувача"""
    model = UserProfile
    can_delete = False
    verbose_name = 'Профіль'
    verbose_name_plural = 'Профіль'
    fields = ['company_name', 'tax_number', 'address', 'notes']


class WholesaleClientAdmin(AdminMediaMixin, UserAdmin):
    """Адмінка для оптових клієнтів"""
    
    list_display = ['get_full_name_display', 'email', 'get_phone_display', 'get_orders_count', 'get_last_order_date', 'get_last_login_display']
    list_filter = ['email_verified', 'is_active', 'created_at', 'last_login']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'middle_name', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('username', 'password')
        }),
        ('Персональні дані', {
            'fields': ('first_name', 'last_name', 'middle_name', 'email', 'phone')
        }),
        ('Статус', {
            'fields': ('is_wholesale', 'email_verified', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Дати', {
            'fields': ('date_joined', 'last_login', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'created_at']
    
    inlines = [UserProfileInline]
    
    def get_queryset(self, request):
        """Показуємо тільки оптових клієнтів з анотаціями"""
        qs = super().get_queryset(request)
        return qs.filter(is_wholesale=True).annotate(
            orders_count=Count('order'),
            last_order_date=Max('order__created_at')
        )
    
    def get_full_name_display(self, obj):
        """Повне ім'я з по-батькові"""
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
    
    def get_phone_display(self, obj):
        """Телефон або повідомлення про його відсутність"""
        return obj.phone if obj.phone else 'не вказано'
    get_phone_display.short_description = 'Телефон'
    
    def get_orders_count(self, obj):
        """Кількість замовлень"""
        return obj.orders_count if hasattr(obj, 'orders_count') else obj.order_set.count()
    get_orders_count.short_description = 'Кількість замовлень'
    get_orders_count.admin_order_field = 'orders_count'
    
    def get_last_order_date(self, obj):
        """Дата останнього замовлення"""
        if hasattr(obj, 'last_order_date') and obj.last_order_date:
            return obj.last_order_date.strftime('%d.%m.%Y %H:%M')
        last_order = obj.order_set.order_by('-created_at').first()
        if last_order:
            return last_order.created_at.strftime('%d.%m.%Y %H:%M')
        return 'не робив замовлень'
    get_last_order_date.short_description = 'Дата останнього замовлення'
    get_last_order_date.admin_order_field = 'last_order_date'
    
    def get_last_login_display(self, obj):
        """Дата останнього заходу в особистий кабінет"""
        if obj.last_login:
            return obj.last_login.strftime('%d.%m.%Y %H:%M')
        return 'ще не заходив'
    get_last_login_display.short_description = 'Останній вхід'
    get_last_login_display.admin_order_field = 'last_login'
    
    def has_add_permission(self, request):
        """Заборона створення нових користувачів через цей розділ"""
        return False


admin.site.register(WholesaleClient, WholesaleClientAdmin)
admin.site.unregister(Group)

WholesaleClient._meta.verbose_name = 'Оптовий клієнт'
WholesaleClient._meta.verbose_name_plural = '💼 Оптові клієнти'
WholesaleClient._meta.app_label = 'users'
