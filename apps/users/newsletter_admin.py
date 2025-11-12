"""
Адміністрування підписників розсилки
"""
from django.contrib import admin
from django.contrib import messages
from apps.orders.models import Newsletter
from apps.core.admin_utils import AdminMediaMixin


@admin.register(Newsletter)
class NewsletterAdmin(AdminMediaMixin, admin.ModelAdmin):
    """Адміністрування підписників розсилки - тільки перегляд"""
    
    list_display = ['email', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', ('created_at', admin.DateFieldListFilter)]
    search_fields = ['email', 'name']
    ordering = ['-created_at']
    list_per_page = 50
    readonly_fields = ['email', 'name', 'is_active', 'created_at']
    actions = ['activate_subscribers', 'deactivate_subscribers']
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('email', 'name', 'is_active', 'created_at')
        }),
    )
    
    def activate_subscribers(self, request, queryset):
        """Активувати підписників"""
        updated = queryset.update(is_active=True)
        messages.success(request, f'Активовано {updated} підписників')
    activate_subscribers.short_description = 'Активувати вибрані підписки'
    
    def deactivate_subscribers(self, request, queryset):
        """Деактивувати підписників"""
        updated = queryset.update(is_active=False)
        messages.success(request, f'Деактивовано {updated} підписників')
    deactivate_subscribers.short_description = 'Деактивувати вибрані підписки'
    
    def has_add_permission(self, request):
        """Заборона додавання через адмінку"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Дозволити видалення"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Тільки для перегляду та деактивації"""
        return True
    
    def save_model(self, request, obj, form, change):
        """Заборона змін через форму - дозволено тільки через actions"""
        if change:
            super().save_model(request, obj, form, change)


Newsletter._meta.verbose_name = 'Підписка на розсилку'
Newsletter._meta.verbose_name_plural = '📧 4. Підписка на розсилку'

