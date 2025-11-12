from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    
    def ready(self):
        """Імпортуємо admin для Newsletter"""
        import apps.users.newsletter_admin
    verbose_name = '👥 Клієнти'
