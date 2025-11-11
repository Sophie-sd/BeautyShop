"""
Адміністративна панель для замовлень
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Q, Count, Max
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import path, reverse
from datetime import datetime, timedelta
from .models import Order, OrderItem, RetailClient, EmailCampaign, Newsletter


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
        'order_number', 'get_customer_name', 'get_status_colored',
        'get_total_display', 'get_payment_colored', 'created_at'
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
        'get_customer_full_info', 'get_delivery_full_info',
        'get_payment_full_info', 'get_items_table'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 50
    
    inlines = []
    
    def has_add_permission(self, request):
        """Заборонити створення замовлень через адмінку"""
        return False
    
    fieldsets = (
        ('📋 Основна інформація', {
            'fields': ('order_number', 'status', 'created_at', 'updated_at')
        }),
        ('🛒 Товари', {
            'fields': ('get_items_table',),
        }),
        ('👤 Клієнт', {
            'fields': ('get_customer_full_info',)
        }),
        ('🚚 Доставка', {
            'fields': ('get_delivery_full_info',)
        }),
        ('💳 Оплата', {
            'fields': ('get_payment_full_info',)
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
    
    def get_list_display_links(self, request, list_display):
        """Робимо весь рядок кліка бельним"""
        return ('order_number',)
    
    def get_row_css(self, obj):
        """CSS класи для рядків таблиці"""
        if obj.status == 'completed':
            return 'completed-row'
        return ''
    
    def get_status_colored(self, obj):
        """Статус з кольоровим кодуванням"""
        colors = {
            'pending': '#dc3545',
            'confirmed': '#0056b3', 
            'processing': '#17a2b8',
            'shipped': '#fd7e14',
            'delivered': '#28a745',
            'completed': '#218838',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return mark_safe(f'<span style="color: {color}; font-weight: 600;">●</span> {obj.get_status_display()}')
    get_status_colored.short_description = 'Статус'
    
    def get_payment_colored(self, obj):
        """Оплата з кольоровим кодуванням"""
        if obj.is_paid:
            return mark_safe('<span style="color: #28a745; font-weight: 600;">✓ Оплачено</span>')
        return mark_safe('<span style="color: #dc3545; font-weight: 600;">✗ Не оплачено</span>')
    get_payment_colored.short_description = 'Оплата'
    
    def get_total_display(self, obj):
        """Загальна сума"""
        return mark_safe(f'<strong>{float(obj.total):.2f} ₴</strong>')
    get_total_display.short_description = 'Сума'
    
    def get_customer_full_info(self, obj):
        """Повна інформація про клієнта - тільки для читання"""
        client_type = "Гість"
        if obj.user:
            if obj.user.is_staff or obj.user.is_superuser:
                client_type = "Адміністратор"
            else:
                client_type = "Оптовий клієнт"
        else:
            client_type = "Роздрібний клієнт"
        
        html = f'''
        <div style="background: #f7fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #4299e1;">
            <div style="margin-bottom: 12px;">
                <strong style="color: #2d3748;">ПІБ:</strong> 
                <span style="color: #1a202c;">{obj.get_customer_name()}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #2d3748;">Email:</strong> 
                <span style="color: #1a202c;">{obj.email}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #2d3748;">Телефон:</strong> 
                <span style="color: #1a202c;">{obj.phone}</span>
            </div>
            <div>
                <strong style="color: #2d3748;">Тип клієнта:</strong> 
                <span style="color: #4299e1; font-weight: 600;">{client_type}</span>
            </div>
        </div>
        '''
        return mark_safe(html)
    get_customer_full_info.short_description = "Інформація про клієнта"
    
    def get_delivery_full_info(self, obj):
        """Повна інформація про доставку - тільки для читання"""
        delivery_method_display = obj.get_delivery_method_display()
        
        html = f'''
        <div style="background: #f7fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #48bb78;">
            <div style="margin-bottom: 12px;">
                <strong style="color: #2d3748;">Спосіб доставки:</strong> 
                <span style="color: #1a202c;">{delivery_method_display}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #2d3748;">Місто:</strong> 
                <span style="color: #1a202c;">{obj.delivery_city}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #2d3748;">Адреса:</strong> 
                <span style="color: #1a202c;">{obj.delivery_address}</span>
            </div>
        </div>
        '''
        return mark_safe(html)
    get_delivery_full_info.short_description = "Інформація про доставку"
    
    def get_payment_full_info(self, obj):
        """Повна інформація про оплату - тільки для читання"""
        payment_method_display = obj.get_payment_method_display()
        payment_status = "Оплачено ✓" if obj.is_paid else "Не оплачено ✗"
        payment_status_color = "#28a745" if obj.is_paid else "#dc3545"
        payment_date_display = obj.payment_date.strftime('%d.%m.%Y %H:%M') if obj.payment_date else "—"
        
        html = f'''
        <div style="background: #f7fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #f6ad55;">
            <div style="margin-bottom: 12px;">
                <strong style="color: #2d3748;">Спосіб оплати:</strong> 
                <span style="color: #1a202c;">{payment_method_display}</span>
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #2d3748;">Статус оплати:</strong> 
                <span style="color: {payment_status_color}; font-weight: 600;">{payment_status}</span>
                {f'<span style="color: #718096;"> ({payment_date_display})</span>' if obj.is_paid else ''}
            </div>
            <div style="margin-bottom: 12px;">
                <strong style="color: #2d3748;">Сума товарів:</strong> 
                <span style="color: #1a202c;">{float(obj.subtotal):.2f} ₴</span>
            </div>
        '''
        
        if obj.discount > 0:
            html += f'''
            <div style="margin-bottom: 12px;">
                <strong style="color: #2d3748;">Знижка:</strong> 
                <span style="color: #f56565;">-{float(obj.discount):.2f} ₴</span>
            </div>
            '''
        
        html += f'''
            <div style="margin-top: 16px; padding-top: 16px; border-top: 2px solid #e2e8f0;">
                <strong style="color: #2d3748; font-size: 16px;">Загальна сума:</strong> 
                <span style="color: #4299e1; font-weight: 700; font-size: 18px;">{float(obj.total):.2f} ₴</span>
            </div>
        </div>
        '''
        return mark_safe(html)
    get_payment_full_info.short_description = "Інформація про оплату"
    
    def get_items_table(self, obj):
        """Таблиця товарів в замовленні"""
        items = obj.items.all()
        if not items:
            return mark_safe('<p style="color: #718096;">Немає товарів</p>')
        
        html = '<table style="width:100%; border-collapse: collapse; margin-top: 10px;">'
        html += '<tr style="background: #f7fafc;"><th style="padding: 12px; text-align: left; border-bottom: 2px solid #e2e8f0;">Товар</th><th style="padding: 12px; text-align: center; border-bottom: 2px solid #e2e8f0;">Кількість</th><th style="padding: 12px; text-align: right; border-bottom: 2px solid #e2e8f0;">Ціна</th><th style="padding: 12px; text-align: right; border-bottom: 2px solid #e2e8f0;">Сума</th></tr>'
        
        for item in items:
            html += f'''
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 12px;">{item.product.name}</td>
                    <td style="padding: 12px; text-align: center;">{item.quantity} шт</td>
                    <td style="padding: 12px; text-align: right;">{float(item.price):.2f} ₴</td>
                    <td style="padding: 12px; text-align: right;"><strong>{float(item.get_cost()):.2f} ₴</strong></td>
                </tr>
            '''
        
        html += f'''
            <tr style="background: #ebf8ff; font-weight: 600;">
                <td colspan="3" style="padding: 12px; text-align: right;">Разом:</td>
                <td style="padding: 12px; text-align: right; color: #4299e1;">{float(obj.subtotal):.2f} ₴</td>
            </tr>
        '''
        
        html += '</table>'
        return mark_safe(html)
    get_items_table.short_description = "Товари в замовленні"
    
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


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Адміністрування підписників розсилки"""
    
    list_display = ['email', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', ('created_at', admin.DateFieldListFilter)]
    search_fields = ['email', 'name']
    ordering = ['-created_at']
    list_per_page = 50
    readonly_fields = ['created_at']
    actions = ['activate_subscribers', 'deactivate_subscribers']
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('email', 'name', 'is_active')
        }),
        ('Дата підписки', {
            'fields': ('created_at',),
            'classes': ('collapse',)
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
                'fields': ('send_type', 'scheduled_at')
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
        """Зберігаємо та відправляємо розсилку"""
        if not change:
            obj.created_by = request.user
        
        super().save_model(request, obj, form, change)
        
        send_type = request.POST.get('send_type', 'now')
        scheduled_at = obj.scheduled_at
        
        if send_type == 'now' and not scheduled_at and obj.status == 'draft':
            success = obj.send_campaign()
            if success:
                messages.success(request, f'Розсилку "{obj.name}" успішно відправлено! Відправлено: {obj.sent_count}, помилок: {obj.failed_count}')
            else:
                messages.error(request, 'Помилка при відправці розсилки')
        elif send_type == 'scheduled' and scheduled_at:
            obj.status = 'scheduled'
            obj.save(update_fields=['status'])
            messages.info(request, f'Розсилку заплановано на {scheduled_at.strftime("%d.%m.%Y %H:%M")}')
    
    def has_delete_permission(self, request, obj=None):
        """Дозволити видалення всім адміністраторам"""
        return request.user.is_superuser or request.user.is_staff
    
    class Media:
        css = {
            'all': ('admin/css/email_campaign.css',)
        }
        js = ('admin/js/email_campaign.js',)


# Налаштування відображення в адмінці
Order._meta.verbose_name = "Замовлення"
Order._meta.verbose_name_plural = "📦 Замовлення"

RetailClient._meta.verbose_name = 'Роздрібний клієнт'
RetailClient._meta.verbose_name_plural = '🛒 Роздрібні клієнти'
RetailClient._meta.app_label = 'users'

Newsletter._meta.verbose_name = 'Підписка на розсилку'
Newsletter._meta.verbose_name_plural = '📧 Підписка на розсилку'
Newsletter._meta.app_label = 'users'

EmailCampaign._meta.verbose_name = 'Email розсилка'
EmailCampaign._meta.verbose_name_plural = '✉️ Email розсилки'
