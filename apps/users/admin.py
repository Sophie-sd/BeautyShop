"""
Адміністративна панель для користувачів
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count
from .models import CustomUser, UserProfile, WholesaleClient


class UserProfileInline(admin.StackedInline):
    """Інлайн для профілю користувача"""
    model = UserProfile
    can_delete = False
    verbose_name = 'Профіль'
    verbose_name_plural = 'Профіль'
    fields = ['company_name', 'tax_number', 'address', 'notes']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Адмінка для всіх користувачів"""
    
    list_display = ['username', 'get_full_name_display', 'email', 'get_phone_display', 'is_wholesale', 'email_verified', 'is_active', 'created_at']
    list_filter = ['is_wholesale', 'email_verified', 'is_active', 'is_staff', 'created_at']
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
    
    add_fieldsets = (
        ('Основна інформація', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('Персональні дані', {
            'fields': ('first_name', 'last_name', 'middle_name', 'phone'),
        }),
        ('Статус', {
            'fields': ('is_wholesale', 'email_verified', 'is_active', 'is_staff'),
        }),
    )
    
    inlines = [UserProfileInline]
    
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
    
    def get_phone_display(self, obj):
        """Телефон або повідомлення про його відсутність"""
        return obj.phone if obj.phone else 'не вказано'
    get_phone_display.short_description = 'Телефон'


class WholesaleClientAdmin(UserAdmin):
    """Адмінка для оптових клієнтів"""
    
    list_display = ['get_full_name_display', 'email', 'get_phone_display', 'get_orders_count', 'get_last_login_display']
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
        """Показуємо тільки оптових клієнтів"""
        qs = super().get_queryset(request)
        return qs.filter(is_wholesale=True).annotate(orders_count=Count('order'))
    
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

CustomUser._meta.verbose_name = 'Користувач'
CustomUser._meta.verbose_name_plural = '👥 Користувачі'
