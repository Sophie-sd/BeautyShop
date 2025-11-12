"""
Спільні utility функції для адміністративної панелі
Уникнення дублювання коду між різними admin.py
"""
from django.utils.html import format_html
from typing import Optional


def get_image_preview(image_url: Optional[str], alt_text: str = '', css_class: str = 'admin-thumbnail-small') -> str:
    """
    Генерує HTML для превью зображення в адмінці
    
    Args:
        image_url: URL зображення
        alt_text: Альтернативний текст
        css_class: CSS клас для зображення
    
    Returns:
        HTML рядок з превью зображення або placeholder
    """
    if image_url:
        return format_html(
            '<img src="{}" alt="{}" class="{}" />',
            image_url,
            alt_text,
            css_class
        )
    return format_html('<div class="admin-icon-placeholder">📦</div>')


def get_colored_badge(text: str, badge_type: str = 'info') -> str:
    """
    Генерує кольоровий бейдж для відображення статусу
    
    Args:
        text: Текст бейджа
        badge_type: Тип бейджа (success, warning, danger, info, secondary)
    
    Returns:
        HTML рядок з бейджем
    """
    return format_html(
        '<span class="badge badge-{}">{}</span>',
        badge_type,
        text
    )


def get_status_icon(is_active: bool, active_text: str = '✓ Активно', inactive_text: str = '✕ Неактивно') -> str:
    """
    Генерує іконку статусу активності
    
    Args:
        is_active: Чи активний елемент
        active_text: Текст для активного стану
        inactive_text: Текст для неактивного стану
    
    Returns:
        HTML рядок зі статусом
    """
    if is_active:
        return format_html(
            '<span class="status-active">{}</span>',
            active_text
        )
    return format_html(
        '<span class="status-inactive">{}</span>',
        inactive_text
    )


def get_yes_no_icon(value: bool) -> str:
    """
    Генерує іконку так/ні
    
    Args:
        value: Булеве значення
    
    Returns:
        HTML рядок з іконкою
    """
    if value:
        return format_html('<span class="admin-has-link">✓ Є</span>')
    return format_html('<span class="admin-no-link">Немає</span>')


def format_price(price: float, currency: str = '₴') -> str:
    """
    Форматує ціну для відображення
    
    Args:
        price: Сума
        currency: Валюта
    
    Returns:
        Відформатована ціна
    """
    return f'{price:.2f} {currency}'


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Обрізає текст до вказаної довжини з додаванням трикрапки
    
    Args:
        text: Текст для обрізання
        max_length: Максимальна довжина
    
    Returns:
        Обрізаний текст
    """
    if not text:
        return ''
    return text[:max_length] + '...' if len(text) > max_length else text


class AdminMediaMixin:
    """Mixin для додавання кастомних CSS/JS до адмінки"""
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)


def optimize_queryset_for_admin(queryset, select_related_fields=None, prefetch_related_fields=None):
    """
    Оптимізує queryset для адміністративної панелі
    
    Args:
        queryset: Django QuerySet
        select_related_fields: Список полів для select_related
        prefetch_related_fields: Список полів для prefetch_related
    
    Returns:
        Оптимізований QuerySet
    """
    if select_related_fields:
        queryset = queryset.select_related(*select_related_fields)
    
    if prefetch_related_fields:
        queryset = queryset.prefetch_related(*prefetch_related_fields)
    
    return queryset

