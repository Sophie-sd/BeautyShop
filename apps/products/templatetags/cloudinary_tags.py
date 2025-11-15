"""
Кастомні теги для роботи з Cloudinary
"""
from django import template

register = template.Library()


@register.filter
def cloudinary_transform(image_url: str, transformations: str = 'w_300,h_300,c_fill,q_85,f_auto') -> str:
    """
    Трансформує URL зображення через Cloudinary
    
    Usage:
        {{ product.images.first.image.url|cloudinary_transform }}
        {{ product.images.first.image.url|cloudinary_transform:'w_500,h_500,c_fit,q_90' }}
    """
    if not image_url:
        return ''
    
    url_str = str(image_url)
    
    # Якщо це вже Cloudinary URL
    if 'res.cloudinary.com' in url_str or 'cloudinary.com' in url_str:
        # Перевіряємо чи вже є трансформації
        if '/image/upload/' in url_str:
            parts = url_str.split('/image/upload/')
            if len(parts) == 2:
                # Якщо вже є трансформації, замінюємо їх
                base_url = parts[0]
                path_parts = parts[1].split('/')
                # Перший елемент після upload/ може бути трансформацією або версією
                if path_parts[0].startswith('v') and path_parts[0][1:].isdigit():
                    # Це версія, залишаємо
                    return f"{base_url}/image/upload/{transformations}/{parts[1]}"
                else:
                    # Це трансформація або public_id, додаємо трансформації
                    return f"{base_url}/image/upload/{transformations}/{parts[1]}"
        elif '/raw/upload/' in url_str:
            # Для raw файлів не застосовуємо трансформації
            return url_str
    
    # Якщо це не Cloudinary URL або локальний файл, повертаємо як є
    return url_str


@register.simple_tag
def cloudinary_image(image, width: int = 300, height: int = 300, crop: str = 'fill', quality: int = 85) -> str:
    """
    Генерує URL для зображення з трансформаціями Cloudinary
    
    Usage:
        {% cloudinary_image product.images.first.image width=300 height=300 %}
    """
    if not image:
        return ''
    
    try:
        image_url = image.url if hasattr(image, 'url') else str(image)
    except (AttributeError, ValueError):
        return ''
    
    transformations = f'w_{width},h_{height},c_{crop},q_{quality},f_auto'
    return cloudinary_transform(image_url, transformations)

