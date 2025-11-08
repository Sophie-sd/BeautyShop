from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Order, EmailSubscriber


@receiver(post_save, sender=Order)
def collect_order_email(sender, instance, created, **kwargs):
    """Збирати email адреси з замовлень"""
    if created and instance.email:
        is_wholesale = instance.user and instance.user.is_wholesale
        source = 'registered' if instance.user else 'order'
        name = f"{instance.first_name} {instance.last_name}" if instance.first_name else ''
        
        EmailSubscriber.add_subscriber(
            email=instance.email,
            source=source,
            name=name,
            is_wholesale=is_wholesale
        )


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def collect_user_email(sender, instance, created, **kwargs):
    """Збирати email адреси зареєстрованих користувачів (тільки оптових, не адмінів)"""
    if instance.email and not instance.is_staff and not instance.is_superuser:
        is_wholesale = getattr(instance, 'is_wholesale', False)
        if is_wholesale:
            EmailSubscriber.add_subscriber(
                email=instance.email,
                source='registered',
                name=f"{instance.first_name} {instance.last_name}" if instance.first_name else instance.username,
                is_wholesale=True
            )

