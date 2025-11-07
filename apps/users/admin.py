"""
Адміністративна панель для користувачів
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import CustomUser, UserProfile


class UserProfileInline(admin.StackedInline):
    """Інлайн для профілю користувача"""
    model = UserProfile
    can_delete = False
    verbose_name = 'Профіль'
    verbose_name_plural = 'Профіль'
    fields = ['company_name', 'tax_number', 'address', 'notes']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Адмінка для користувачів"""
    
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone', 'is_wholesale', 'email_verified', 'is_active', 'created_at']
    list_filter = ['is_wholesale', 'email_verified', 'is_active', 'is_staff', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
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


# Приховуємо "Групи" з адміністративної панелі (не використовуються в проекті)
admin.site.unregister(Group)
