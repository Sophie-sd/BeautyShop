"""
Адміністративна панель для core додатку - банери та статті
"""
from django.contrib import admin
from django.utils.html import format_html, strip_tags
from django.utils.safestring import mark_safe
from django.db import models
from ckeditor.widgets import CKEditorWidget
from .models import Banner
from apps.blog.models import Article


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """Адмін панель для банерів"""
    
    list_display = [
        'title', 
        'desktop_preview', 
        'mobile_preview', 
        'is_active', 
        'has_link',
        'order', 
        'created_at'
    ]
    
    list_filter = [
        'is_active', 
        'created_at'
    ]
    
    search_fields = [
        'title', 
        'alt_text', 
        'link_url'
    ]
    
    list_editable = [
        'is_active', 
        'order'
    ]
    
    readonly_fields = [
        'created_at', 
        'updated_at',
        'desktop_preview_large',
        'mobile_preview_large'
    ]
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('title', 'alt_text', 'is_active', 'order')
        }),
        ('Зображення', {
            'fields': (
                ('desktop_image', 'desktop_preview_large'),
                ('mobile_image', 'mobile_preview_large'),
            ),
            'description': mark_safe("""
                <div class="banner-image-info">
                    <h4>📐 Розміри зображень:</h4>
                    <ul>
                        <li><strong>Десктоп:</strong> 1200×400 пікселів (співвідношення 3:1)</li>
                        <li><strong>Мобільний:</strong> 375×280 пікселів (співвідношення 1.34:1)</li>
                    </ul>
                    <p class="image-formats-note">Підтримувані формати: JPG, PNG, WebP</p>
                </div>
            """)
        }),
        ('Посилання', {
            'fields': ('link_url',),
            'description': 'URL на який переходити при натисканні на банер (необов\'язково)'
        }),
        ('Системні дані', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def desktop_preview(self, obj):
        """Превью десктопного зображення в списку"""
        if obj.desktop_image:
            return format_html(
                '<img src="{}" alt="{}" class="admin-preview-desktop" />',
                obj.desktop_image.url,
                obj.alt_text
            )
        return "Немає"
    desktop_preview.short_description = "Превью десктоп"
    
    def mobile_preview(self, obj):
        """Превью мобільного зображення в списку"""
        if obj.mobile_image:
            return format_html(
                '<img src="{}" alt="{}" class="admin-preview-mobile" />',
                obj.mobile_image.url,
                obj.alt_text
            )
        return "Немає"
    mobile_preview.short_description = "Превью мобільний"
    
    def desktop_preview_large(self, obj):
        """Велике превью десктопного зображення"""
        if obj.desktop_image:
            return format_html(
                '''
                <div class="admin-preview-large">
                    <img src="{}" alt="{}" class="admin-preview-large-desktop" />
                    <p class="admin-preview-caption">Десктоп версія</p>
                </div>
                ''',
                obj.desktop_image.url,
                obj.alt_text
            )
        return "Зображення не завантажено"
    desktop_preview_large.short_description = "Превью десктоп"
    
    def mobile_preview_large(self, obj):
        """Велике превью мобільного зображення"""
        if obj.mobile_image:
            return format_html(
                '''
                <div class="admin-preview-large">
                    <img src="{}" alt="{}" class="admin-preview-large-mobile" />
                    <p class="admin-preview-caption">Мобільна версія</p>
                </div>
                ''',
                obj.mobile_image.url,
                obj.alt_text
            )
        return "Зображення не завантажено"
    mobile_preview_large.short_description = "Превью мобільний"
    
    def has_link(self, obj):
        """Чи є посилання"""
        if obj.link_url:
            return format_html(
                '<span class="admin-has-link">✓ Є</span>'
            )
        return format_html(
            '<span class="admin-no-link">Немає</span>'
        )
    has_link.short_description = "Посилання"
    
    def get_queryset(self, request):
        """Оптимізація запитів"""
        return super().get_queryset(request).select_related()
        
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Адміністрування статей"""
    
    list_display = [
        'title', 'get_image_preview', 'created_at', 'get_excerpt_preview'
    ]
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    save_on_top = True
    list_per_page = 50
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('title', 'slug', 'excerpt', 'image')
        }),
        ('Контент', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('Зв\'язані товари', {
            'fields': ('related_products',),
            'description': 'Оберіть до 5 товарів для відображення в кінці статті'
        }),
        ('Публікація', {
            'fields': ('is_published',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ['related_products']
    
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget()},
    }
    
    actions = ['publish_articles', 'unpublish_articles', 'duplicate_articles']
    
    def get_image_preview(self, obj):
        """Попередній перегляд зображення"""
        if obj.image:
            return format_html(
                '<img src="{}" class="admin-thumbnail-small" />',
                obj.image.url
            )
        return "📷 Немає"
    get_image_preview.short_description = "Зображення"
    
    def get_excerpt_preview(self, obj):
        """Попередній перегляд опису"""
        if obj.excerpt:
            clean_text = strip_tags(obj.excerpt)
            return clean_text[:50] + "..." if len(clean_text) > 50 else clean_text
        return "Немає опису"
    get_excerpt_preview.short_description = "Короткий опис"
    
    def publish_articles(self, request, queryset):
        """Опублікувати статті"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f"Опубліковано {updated} статей")
    publish_articles.short_description = "Опублікувати вибрані статті"
    
    def unpublish_articles(self, request, queryset):
        """Сховати статті"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f"Сховано {updated} статей")
    unpublish_articles.short_description = "Сховати вибрані статті"
    
    def duplicate_articles(self, request, queryset):
        """Дублювати статті"""
        duplicated = 0
        for article in queryset:
            article.pk = None
            article.title = f"{article.title} (копія)"
            article.slug = f"{article.slug}-copy"
            article.is_published = False
            article.save()
            duplicated += 1
        self.message_user(request, f"Продубльовано {duplicated} статей")
    duplicate_articles.short_description = "Дублювати вибрані статті"
    
    def get_queryset(self, request):
        """Оптимізація запитів"""
        return super().get_queryset(request).prefetch_related('related_products')
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)


# Налаштування відображення моделей в адмінці
Banner._meta.verbose_name = "Банер"
Banner._meta.verbose_name_plural = "📸 Банери"

Article._meta.verbose_name = "Стаття"
Article._meta.verbose_name_plural = "📝 Статті"
Article._meta.app_label = "core"

# Додаткові налаштування адмін панелі
admin.site.site_header = "Beauty Shop Адміністрування"
admin.site.site_title = "Beauty Shop Admin"
admin.site.index_title = "Панель управління"
