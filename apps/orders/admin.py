"""
Адміністративна панель для замовлень
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q, Count, Max
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta
from .models import Order, OrderItem, RetailClient, EmailSubscriber, EmailCampaign
from .admin_filters import RecipientTypeFilter


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
            'fields': ('first_name', 'last_name', 'middle_name', 'email', 'phone', 'get_customer_info')
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


@admin.register(RetailClient)
class RetailClientAdmin(admin.ModelAdmin):
    """Адміністрування роздрібних клієнтів (гості без реєстрації)"""
    
    list_display = [
        'get_full_name_display', 'email', 'get_phone_display',
        'get_orders_count', 'get_last_order_date'
    ]
    search_fields = [
        'first_name', 'last_name', 'middle_name', 'email', 'phone'
    ]
    ordering = ['-created_at']
    list_per_page = 50
    
    def get_queryset(self, request):
        """Показуємо тільки замовлення без користувача (унікальні по email)"""
        qs = super().get_queryset(request)
        guest_orders = qs.filter(user__isnull=True).order_by('email', '-created_at')
        
        seen_emails = set()
        unique_orders_ids = []
        
        for order in guest_orders:
            email_lower = order.email.lower()
            if email_lower not in seen_emails:
                seen_emails.add(email_lower)
                unique_orders_ids.append(order.id)
        
        return qs.filter(id__in=unique_orders_ids).order_by('-created_at')
    
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
        """Телефон"""
        return obj.phone if obj.phone else 'не вказано'
    get_phone_display.short_description = 'Телефон'
    
    def get_orders_count(self, obj):
        """Кількість замовлень клієнта"""
        return Order.objects.filter(user__isnull=True, email=obj.email).count()
    get_orders_count.short_description = 'Кількість замовлень'
    
    def get_last_order_date(self, obj):
        """Дата останнього замовлення"""
        last_order = Order.objects.filter(user__isnull=True, email=obj.email).order_by('-created_at').first()
        if last_order:
            return last_order.created_at.strftime('%d.%m.%Y %H:%M')
        return 'немає замовлень'
    get_last_order_date.short_description = 'Дата останнього замовлення'
    
    def has_add_permission(self, request):
        """Заборона створення через цей розділ"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Заборона видалення"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Дозвіл тільки на перегляд"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Переопределяем changelist_view для відображення унікальних клієнтів"""
        return super().changelist_view(request, extra_context)


@admin.register(EmailSubscriber)
class EmailSubscriberAdmin(admin.ModelAdmin):
    """Адміністрування email адрес"""
    
    list_display = ['email', 'name', 'get_source_badge', 'get_type_badge', 'is_active', 'created_at']
    list_filter = [RecipientTypeFilter, 'source', 'is_wholesale', 'is_active', ('created_at', admin.DateFieldListFilter)]
    search_fields = ['email', 'name']
    ordering = ['-created_at']
    list_per_page = 50
    readonly_fields = ['created_at', 'updated_at']
    actions = ['activate_subscribers', 'deactivate_subscribers', 'export_to_csv']
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('email', 'name', 'source', 'is_active', 'is_wholesale')
        }),
        ('Дати', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_source_badge(self, obj):
        """Джерело з бейджем"""
        colors = {
            'newsletter': 'info',
            'registered': 'success',
            'order': 'warning',
        }
        color = colors.get(obj.source, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_source_display()
        )
    get_source_badge.short_description = 'Джерело'
    
    def get_type_badge(self, obj):
        """Тип клієнта"""
        if obj.is_wholesale:
            return format_html('<span class="badge badge-primary">Оптовий</span>')
        return format_html('<span class="badge badge-secondary">Роздрібний</span>')
    get_type_badge.short_description = 'Тип'
    
    def activate_subscribers(self, request, queryset):
        """Активувати підписників"""
        updated = queryset.update(is_active=True)
        messages.success(request, f'Активовано {updated} підписників')
    activate_subscribers.short_description = 'Активувати вибрані email адреси'
    
    def deactivate_subscribers(self, request, queryset):
        """Деактивувати підписників"""
        updated = queryset.update(is_active=False)
        messages.success(request, f'Деактивовано {updated} підписників')
    deactivate_subscribers.short_description = 'Деактивувати вибрані email адреси'
    
    def export_to_csv(self, request, queryset):
        """Експорт в CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="email_subscribers.csv"'
        response.write('\ufeff'.encode('utf8'))
        
        writer = csv.writer(response)
        writer.writerow(['Email', 'Ім\'я', 'Джерело', 'Тип', 'Активний', 'Дата додавання'])
        
        for subscriber in queryset:
            writer.writerow([
                subscriber.email,
                subscriber.name,
                subscriber.get_source_display(),
                'Оптовий' if subscriber.is_wholesale else 'Роздрібний',
                'Так' if subscriber.is_active else 'Ні',
                subscriber.created_at.strftime('%d.%m.%Y %H:%M')
            ])
        
        return response
    export_to_csv.short_description = 'Експортувати в CSV'


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    """Адміністрування email розсилок"""
    
    from .forms import EmailCampaignForm
    form = EmailCampaignForm
    
    list_display = ['name', 'subject', 'get_status_badge', 'get_recipients_display', 'sent_count', 'failed_count', 'created_at', 'get_actions_display']
    list_filter = ['status', ('created_at', admin.DateFieldListFilter), ('sent_at', admin.DateFieldListFilter)]
    search_fields = ['name', 'subject', 'content']
    ordering = ['-created_at']
    list_per_page = 30
    readonly_fields = ['status', 'sent_count', 'failed_count', 'created_at', 'updated_at', 'sent_at', 'created_by', 'get_recipients_count']
    actions = ['duplicate_campaign', 'mark_as_draft']
    
    def get_fieldsets(self, request, obj=None):
        """Динамічні fieldsets в залежності від наявності об'єкта"""
        fieldsets = [
            ('Основна інформація', {
                'fields': ('name', 'subject')
            }),
            ('Контент', {
                'fields': ('content', 'image')
            }),
            ('Отримувачі', {
                'fields': ('recipients', 'get_recipients_count')
            }),
            ('Налаштування відправки', {
                'fields': ('scheduled_at',)
            }),
        ]
        
        if obj and obj.pk:
            fieldsets.append(
                ('Статистика', {
                    'fields': ('status', 'sent_count', 'failed_count', 'created_at', 'updated_at', 'sent_at', 'created_by'),
                    'classes': ('collapse',)
                })
            )
        
        return fieldsets
    
    def get_urls(self):
        """Додаємо URL для відправки розсилки"""
        urls = super().get_urls()
        custom_urls = [
            path('<int:campaign_id>/send/', self.admin_site.admin_view(self.send_campaign_view), name='orders_emailcampaign_send'),
        ]
        return custom_urls + urls
    
    def get_status_badge(self, obj):
        """Статус з бейджем"""
        colors = {
            'draft': 'secondary',
            'scheduled': 'info',
            'sending': 'warning',
            'sent': 'success',
            'failed': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Статус'
    
    def get_recipients_display(self, obj):
        """Відображення отримувачів"""
        if not obj.recipients:
            return 'Не вибрано'
        
        recipient_labels = {
            'newsletter': 'Підписники розсилки',
            'wholesale': 'Оптові клієнти',
            'retail': 'Роздрібні клієнти',
        }
        
        labels = [recipient_labels.get(r, r) for r in obj.recipients]
        return ', '.join(labels)
    get_recipients_display.short_description = 'Отримувачі'
    
    def get_recipients_count(self, obj):
        """Кількість отримувачів"""
        if obj.pk:
            count = len(obj.get_recipients_list())
            return format_html(
                '<strong style="color: green;">{} адрес</strong>',
                count
            )
        return 'Збережіть розсилку для підрахунку'
    get_recipients_count.short_description = 'Кількість отримувачів'
    
    def get_actions_display(self, obj):
        """Кнопки дій"""
        if obj.status in ['draft', 'scheduled']:
            url = reverse('admin:orders_emailcampaign_send', args=[obj.pk])
            return format_html(
                '<a class="button" href="{}" style="background: #4CAF50; color: white; padding: 5px 15px; border-radius: 3px; text-decoration: none;">✉️ Відправити</a>',
                url
            )
        elif obj.status == 'sent':
            return format_html('<span style="color: green;">✓ Відправлено</span>')
        return '-'
    get_actions_display.short_description = 'Дії'
    
    def send_campaign_view(self, request, campaign_id):
        """View для відправки розсилки"""
        from django.template.response import TemplateResponse
        
        campaign = EmailCampaign.objects.get(pk=campaign_id)
        
        if request.method == 'POST':
            success = campaign.send_campaign()
            if success:
                messages.success(request, f'Розсилку "{campaign.name}" успішно відправлено!')
            else:
                messages.error(request, 'Помилка при відправці розсилки')
            return redirect('admin:orders_emailcampaign_changelist')
        
        recipients_count = len(campaign.get_recipients_list())
        
        context = {
            'campaign': campaign,
            'recipients_count': recipients_count,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
        }
        
        return TemplateResponse(request, 'admin/orders/email_campaign_send_confirm.html', context)
    
    def save_model(self, request, obj, form, change):
        """Зберігаємо автора розсилки"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        """Дозволити видалення тільки чернеток"""
        if obj and obj.status == 'sent':
            return False
        return super().has_delete_permission(request, obj)
    
    def duplicate_campaign(self, request, queryset):
        """Дублювати розсилку"""
        for campaign in queryset:
            campaign.pk = None
            campaign.id = None
            campaign.name = f"{campaign.name} (Копія)"
            campaign.status = 'draft'
            campaign.sent_count = 0
            campaign.failed_count = 0
            campaign.sent_at = None
            campaign.created_by = request.user
            campaign.save()
        
        messages.success(request, f'Продубльовано {queryset.count()} розсилок')
    duplicate_campaign.short_description = 'Дублювати вибрані розсилки'
    
    def mark_as_draft(self, request, queryset):
        """Повернути в чернетки"""
        updated = queryset.exclude(status='sent').update(status='draft')
        messages.success(request, f'Переведено в чернетки {updated} розсилок')
    mark_as_draft.short_description = 'Перевести в чернетки'
    
    class Media:
        css = {
            'all': ('admin/css/email_campaign.css',)
        }


# Налаштування відображення в адмінці
Order._meta.verbose_name = "Замовлення"
Order._meta.verbose_name_plural = "📦 Замовлення"

RetailClient._meta.verbose_name = 'Роздрібний клієнт'
RetailClient._meta.verbose_name_plural = '🛒 Роздрібні клієнти'
RetailClient._meta.app_label = 'users'

EmailSubscriber._meta.verbose_name = 'Email адреса'
EmailSubscriber._meta.verbose_name_plural = '📧 Email адреси'

EmailCampaign._meta.verbose_name = 'Email розсилка'
EmailCampaign._meta.verbose_name_plural = '✉️ Email розсилки'
