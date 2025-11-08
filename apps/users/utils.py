"""
Утиліти для роботи з користувачами
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


def send_verification_code_email(user, request):
    """
    Надсилає лист з 6-значним кодом підтвердження email
    """
    # Генеруємо код
    code = user.generate_email_verification_code()
    
    # Контекст для шаблону
    context = {
        'user': user,
        'code': code,
    }
    
    # Рендеримо HTML версію
    html_message = render_to_string('emails/email_verification_code.html', context)
    plain_message = strip_tags(html_message)
    
    # Надсилаємо лист
    try:
        send_mail(
            subject='Підтвердження e-mail - BeautyShop',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Verification code sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification code to {user.email}: {str(e)}")
        return False


def send_verification_email(user, request):
    """
    Надсилає лист з підтвердженням email користувачу (старий метод з токеном)
    Залишаємо для зворотної сумісності
    """
    # Використовуємо новий метод з кодом
    return send_verification_code_email(user, request)


def send_password_reset_code_email(user):
    """
    Надсилає лист з 6-значним кодом відновлення паролю
    """
    # Генеруємо код
    code = user.generate_password_reset_code()
    
    # Контекст для шаблону
    context = {
        'user': user,
        'code': code,
    }
    
    # Рендеримо HTML версію
    html_message = render_to_string('emails/password_reset_code.html', context)
    plain_message = strip_tags(html_message)
    
    # Надсилаємо лист
    try:
        send_mail(
            subject='Відновлення паролю - BeautyShop',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset code sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset code to {user.email}: {str(e)}")
        return False


def send_password_reset_email(user, request, token, uidb64):
    """
    Надсилає лист з посиланням для відновлення паролю (старий метод)
    Залишаємо для зворотної сумісності
    """
    # Будуємо URL для відновлення
    reset_url = request.build_absolute_uri(
        reverse('users:password_reset_confirm', kwargs={
            'uidb64': uidb64,
            'token': token
        })
    )
    
    # Контекст для шаблону
    context = {
        'user': user,
        'reset_url': reset_url,
    }
    
    # Рендеримо HTML версію
    html_message = render_to_string('emails/password_reset.html', context)
    plain_message = strip_tags(html_message)
    
    # Надсилаємо лист
    try:
        send_mail(
            subject='Відновлення паролю - BeautyShop',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False

