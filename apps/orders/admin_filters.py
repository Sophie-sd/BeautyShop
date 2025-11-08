from django.contrib import admin


class RecipientTypeFilter(admin.SimpleListFilter):
    """Фільтр для швидкого вибору типів отримувачів"""
    
    title = 'Тип отримувача (для розсилки)'
    parameter_name = 'recipient_type'
    
    def lookups(self, request, model_admin):
        return (
            ('newsletter_only', 'Тільки підписники розсилки'),
            ('registered_only', 'Тільки зареєстровані'),
            ('order_only', 'Тільки клієнти без реєстрації'),
            ('wholesale_only', 'Тільки оптові'),
            ('retail_only', 'Тільки роздрібні'),
            ('active_all', 'Всі активні'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'newsletter_only':
            return queryset.filter(source='newsletter', is_active=True)
        elif self.value() == 'registered_only':
            return queryset.filter(source='registered', is_active=True)
        elif self.value() == 'order_only':
            return queryset.filter(source='order', is_active=True)
        elif self.value() == 'wholesale_only':
            return queryset.filter(is_wholesale=True, is_active=True)
        elif self.value() == 'retail_only':
            return queryset.filter(is_wholesale=False, is_active=True)
        elif self.value() == 'active_all':
            return queryset.filter(is_active=True)
        return queryset

