"""
Налаштування для продакшну (Render)
"""
from .base import *
import dj_database_url
import os

DEBUG = False

# Override SECRET_KEY for production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# ALLOWED_HOSTS для Render
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALLOWED_HOSTS.append('.onrender.com')
ALLOWED_HOSTS.append('beautyshop-django.onrender.com')

# CSRF trusted origins для Render
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'https://beautyshop-django.onrender.com').split(',')
if 'https://beautyshop-django.onrender.com' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://beautyshop-django.onrender.com')
if 'https://*.onrender.com' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://*.onrender.com')

# Database для продакшну (оптимізовано для обмеженої пам'яті)
if os.getenv('DATABASE_URL'):
    # Production database (PostgreSQL on Render)
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=60,  # Зменшено з 600 до 60 сек для економії пам'яті
            conn_health_checks=True,
        )
    }
    # Додаткові налаштування для оптимізації PostgreSQL
    DATABASES['default']['ATOMIC_REQUESTS'] = False  # Вимикаємо автоматичні транзакції
    DATABASES['default']['AUTOCOMMIT'] = True
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
        'options': '-c statement_timeout=30000'  # 30 секунд таймаут для запитів
    }
else:
    # Development database (SQLite)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Static and Media files для продакшну
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Cloudinary configuration для зберігання media файлів
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', 'dahkrj6ye'),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
}

MEDIA_URL = '/media/'

# Django 4.2+ STORAGES система
STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Whitenoise також обслуговує media файли на production
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = False  # Вимкнено на production для продуктивності
WHITENOISE_MAX_AGE = 31536000  # 1 рік кешування для статичних файлів з хешами
WHITENOISE_IMMUTABLE_FILE_TEST = lambda path, url: True  # Всі файли з immutable cache

# Додаємо Whitenoise middleware після SecurityMiddleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Додаємо діагностичний middleware для адмінки (ПЕРЕД authentication middleware)
# Це допомагає діагностувати проблеми з входом
MIDDLEWARE.insert(6, 'apps.users.admin_login_middleware.AdminLoginDebugMiddleware')

# Додаємо security headers middleware
MIDDLEWARE.append('apps.core.middleware.SecurityHeadersMiddleware')
MIDDLEWARE.append('apps.core.middleware.PrivatePagesCacheMiddleware')

# Security settings для продакшну
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Session і CSRF cookies для production - посилена безпека та сумісність
SESSION_COOKIE_SECURE = True  # Тільки HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'  # Захист від CSRF, сумісно з iOS Safari та платіжними редіректами
SESSION_COOKIE_HTTPONLY = True  # Захист від XSS
SESSION_SAVE_EVERY_REQUEST = True  # Продовжує сесію при кожному запиті (sliding expiration)
SESSION_COOKIE_DOMAIN = None  # Автоматично визначається з ALLOWED_HOSTS
SESSION_COOKIE_PATH = '/'  # Доступна для всього сайту

CSRF_COOKIE_SECURE = True  # Тільки HTTPS
CSRF_COOKIE_SAMESITE = 'Lax'  # Захист від CSRF
CSRF_COOKIE_HTTPONLY = False  # JS має доступ для AJAX
CSRF_COOKIE_DOMAIN = None  # Автоматично визначається з ALLOWED_HOSTS
CSRF_COOKIE_PATH = '/'  # Доступна для всього сайту

X_FRAME_OPTIONS = 'DENY'

# Content Security Policy (CSP)
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Додаткові security headers
# CSP буде налаштовано через middleware нижче для гнучкості

# Email settings для продакшну
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
# Використовуємо той самий email що і EMAIL_HOST_USER для FROM_EMAIL
DEFAULT_FROM_EMAIL = f"Beauty Shop <{os.getenv('EMAIL_HOST_USER', 'noreply@beautyshop.com')}>"
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Додаткові налаштування для Gmail
EMAIL_TIMEOUT = 30  # 30 секунд таймаут

# LiqPay налаштування
LIQPAY_PUBLIC_KEY = os.getenv('LIQPAY_PUBLIC_KEY', '')
LIQPAY_PRIVATE_KEY = os.getenv('LIQPAY_PRIVATE_KEY', '')

# Логування для продакшну
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Email логування (тільки помилки)
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Authentication логування (тільки попередження)
        'django.contrib.auth': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.users': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Кешування (обмежено для економії пам'яті)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 500,  # Обмежуємо кількість кешованих записів
        }
    }
}

# Оптимізація пам'яті для Django
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB замість 2.5MB за замовчуванням
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Обмеження для QuerySet
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Session налаштування для production (не перезаписуємо base.py)
# SESSION_ENGINE вже налаштовано в base.py
# SESSION_SAVE_EVERY_REQUEST = True в base.py - важливо для iOS Safari

# Налаштування для Django 4.2+ 
USE_TZ = True
TIME_ZONE = 'Europe/Kiev'
