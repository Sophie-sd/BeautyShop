"""
Адміністративна панель для оптових клієнтів
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    """Додаткова інформація про клієнта"""
    model = UserProfile
    can_delete = False
    fields = ['company_name', 'tax_number', 'address', 'notes']
    verbose_name = "Додаткова інформація"
    verbose_name_plural = "Додаткова інформація"


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Адміністрування оптових клієнтів"""
    
    inlines = [UserProfileInline]
    
    # Змінюємо назву в адмінці
    verbose_name = "Оптовий клієнт"
    verbose_name_plural = "Оптові клієнти"
    
    list_display = [
        'username', 
        'first_name',
        'email', 
        'phone',
        'email_verified',
        'is_active',
        'date_joined'
    ]
    
    list_filter = [
        'email_verified',
        'is_active',
        'is_staff',
        'date_joined'
    ]
    
    search_fields = [
        'username',
        'email',
        'phone',
        'first_name',
        'last_name'
    ]
    
    readonly_fields = [
        'email_verified',
        'created_at',
        'date_joined',
        'last_login'
    ]
    
    fieldsets = UserAdmin.fieldsets + (
        ('Контактні дані', {
            'fields': ('phone', 'date_of_birth'),
            'description': 'Телефон та інша контактна інформація'
        }),
        ('Email верифікація', {
            'fields': ('email_verified', 'email_verification_token'),
            'classes': ('collapse',),
            'description': 'Статус підтвердження email'
        }),
        ('Системні дати', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Основна інформація', {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'phone',
                'first_name',
                'last_name',
                'date_of_birth',
                'password1',
                'password2',
            ),
        }),
        ('Статус', {
            'fields': ('is_active',),
        }),
    )
    
    actions = ['verify_email_action', 'activate_users_action']
    
    def verify_email_action(self, request, queryset):
        """Підтвердити email вручну"""
        updated = queryset.update(email_verified=True, is_active=True, email_verification_token='')
        self.message_user(request, f'{updated} клієнтів підтверджено та активовано.')
    verify_email_action.short_description = 'Підтвердити email та активувати'
    
    def activate_users_action(self, request, queryset):
        """Активувати клієнтів"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} клієнтів активовано.')
    activate_users_action.short_description = 'Активувати клієнтів'


# Видаляємо окрему реєстрацію UserProfile - тепер він тільки inline
admin.site.unregister(UserProfile) if admin.site.is_registered(UserProfile) else None

# Приховуємо "Групи" з адміністративної панелі (не використовуються в проекті)
admin.site.unregister(Group)
