"""
Views для користувачів
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, TemplateView, View, FormView, UpdateView
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView, PasswordResetView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from .models import CustomUser
from .forms import (
    WholesaleRegistrationForm, CustomLoginForm, CustomPasswordResetForm, 
    ProfileEditForm, EmailVerificationCodeForm, PasswordResetCodeForm, CustomSetPasswordForm
)
from .utils import send_verification_email, send_verification_code_email, send_password_reset_code_email
import logging

logger = logging.getLogger(__name__)


class WholesaleRegisterView(CreateView):
    """Реєстрація тільки для оптових клієнтів"""
    
    model = CustomUser
    form_class = WholesaleRegistrationForm
    template_name = 'users/register.html'
    
    def form_valid(self, form):
        try:
            # Зберігаємо користувача (is_active=False)
            user = form.save()
            logger.info(f"📝 New user registered: {user.email} (username: {user.username})")
            
            # Зберігаємо email в сесії для верифікації
            self.request.session['pending_verification_email'] = user.email
            
            # Надсилаємо лист з кодом підтвердження
            if send_verification_code_email(user, self.request):
                logger.info(f"✅ Verification code sent successfully to: {user.email}")
            else:
                logger.error(f"❌ Failed to send verification code to: {user.email}")
                messages.warning(
                    self.request,
                    'Реєстрація успішна, але виникла помилка при надсиланні коду. Зверніться до підтримки.'
                )
            
            return redirect('users:verify_email_code')
            
        except Exception as e:
            logger.error(f"❌ Registration error: {str(e)}", exc_info=True)
            messages.error(
                self.request,
                f'Виникла помилка при реєстрації: {str(e)}. Спробуйте ще раз або зверніться до підтримки.'
            )
            return super().form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Будь ласка, виправте помилки у формі.')
        return super().form_invalid(form)


class RegistrationPendingView(TemplateView):
    """Сторінка після реєстрації - перенаправлення на введення коду"""
    
    def get(self, request, *args, **kwargs):
        # Отримуємо email з сесії (якщо є)
        email = request.session.get('pending_verification_email')
        if not email:
            messages.error(request, 'Сесія верифікації закінчилась. Будь ласка, увійдіть або зареєструйтесь знову.')
            return redirect('users:register')
        
        return redirect('users:verify_email_code')


class EmailVerificationCodeView(FormView):
    """Введення коду підтвердження email"""
    
    template_name = 'users/verify_email_code.html'
    form_class = EmailVerificationCodeForm
    
    def dispatch(self, request, *args, **kwargs):
        # Перевіряємо чи є email в сесії
        if not request.session.get('pending_verification_email'):
            messages.error(request, 'Сесія верифікації закінчилась. Будь ласка, зареєструйтесь знову.')
            return redirect('users:register')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email'] = self.request.session.get('pending_verification_email')
        return context
    
    def form_valid(self, form):
        email = self.request.session.get('pending_verification_email')
        code = form.cleaned_data['code']
        
        try:
            user = CustomUser.objects.get(email=email)
            success, message = user.verify_email_code(code)
            
            if success:
                # Очищаємо сесію
                del self.request.session['pending_verification_email']
                
                # Логінимо користувача
                login(self.request, user, backend='apps.users.backends.WholesaleClientBackend')
                # Оновлюємо сесію для iOS Safari
                self.request.session.modified = True
                
                messages.success(self.request, message)
                return redirect('users:profile')
            else:
                messages.error(self.request, message)
                return self.form_invalid(form)
                
        except CustomUser.DoesNotExist:
            messages.error(self.request, 'Користувача не знайдено.')
            return redirect('users:register')


class ResendVerificationCodeView(View):
    """Повторна відправка коду верифікації"""
    
    def post(self, request):
        email = request.session.get('pending_verification_email')
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Сесія верифікації закінчилась.'
            })
        
        try:
            user = CustomUser.objects.get(email=email)
            
            if send_verification_code_email(user, request):
                logger.info(f"Verification code resent to {email}")
                return JsonResponse({
                    'success': True,
                    'message': 'Код відправлено повторно!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Помилка при відправці коду.'
                })
                
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Користувача не знайдено.'
            })


class EmailVerificationView(View):
    """Підтвердження email через токен (старий метод)"""
    
    def get(self, request, token):
        try:
            user = CustomUser.objects.get(email_verification_token=token)
            
            if user.verify_email(token):
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Email успішно підтверджено!')
                return redirect('users:profile')
            else:
                messages.error(request, 'Невірний токен верифікації.')
                return redirect('users:login')
                
        except CustomUser.DoesNotExist:
            messages.error(request, 'Невірний токен верифікації.')
            return redirect('users:login')


class ProfileView(LoginRequiredMixin, TemplateView):
    """Особистий кабінет користувача"""
    
    template_name = 'users/profile.html'
    
    def dispatch(self, request, *args, **kwargs):
        # БЕЗПЕКА: Адміністратори НЕ можуть заходити в особистий кабінет
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            messages.error(
                request,
                '🔒 Доступ заборонено. Адміністратори не мають доступу до особистого кабінету оптових клієнтів.'
            )
            return redirect('/admin/')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Отримуємо останні 3 замовлення для відображення в профілі
        from apps.orders.models import Order
        recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:3]
        
        context.update({
            'user': user,
            'is_wholesale': user.is_wholesale,
            'recent_orders': recent_orders,
        })
        return context


class UserOrdersView(LoginRequiredMixin, TemplateView):
    """Замовлення користувача"""
    
    template_name = 'users/orders.html'
    
    def dispatch(self, request, *args, **kwargs):
        # БЕЗПЕКА: Адміністратори НЕ можуть заходити в особистий кабінет
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            messages.error(
                request,
                '🔒 Доступ заборонено. Адміністратори не мають доступу до особистого кабінету оптових клієнтів.'
            )
            return redirect('/admin/')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.orders.models import Order
        
        context['orders'] = Order.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Редагування профілю користувача"""
    
    model = CustomUser
    form_class = ProfileEditForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')
    
    def dispatch(self, request, *args, **kwargs):
        # БЕЗПЕКА: Адміністратори НЕ можуть заходити в особистий кабінет
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser):
            messages.error(
                request,
                '🔒 Доступ заборонено. Адміністратори не мають доступу до особистого кабінету оптових клієнтів.'
            )
            return redirect('/admin/')
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Дані успішно оновлено!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Будь ласка, виправте помилки у формі.')
        return super().form_invalid(form)


class CustomLoginView(DjangoLoginView):
    """Custom login view з покращеною валідацією - ТІЛЬКИ для оптових клієнтів"""
    
    authentication_form = CustomLoginForm
    template_name = 'users/login.html'
    
    def form_valid(self, form):
        """
        БЕЗПЕКА: Використовуємо ТІЛЬКИ WholesaleClientBackend
        Забороняємо вхід адміністраторам
        """
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        # Імпортуємо наш backend
        from apps.users.backends import WholesaleClientBackend
        
        # Аутентифікуємо ТІЛЬКИ через WholesaleClientBackend
        backend = WholesaleClientBackend()
        user = backend.authenticate(self.request, username=username, password=password)
        
        if user is None:
            # Перевіряємо чому не вдалося ввійти
            try:
                found_user = CustomUser.objects.filter(email=username).first()
                
                if not found_user:
                    messages.error(
                        self.request,
                        'Користувача з таким email не зареєстровано. Будь ласка, зареєструйтеся.'
                    )
                elif found_user.is_staff or found_user.is_superuser:
                    messages.error(
                        self.request,
                        '🔒 Доступ заборонено. Адміністратори можуть входити тільки через /admin/'
                    )
                elif not found_user.is_active:
                    messages.error(
                        self.request,
                        'Ваш акаунт ще не активовано. Будь ласка, перевірте вашу пошту та підтвердіть email.'
                    )
                else:
                    messages.error(
                        self.request,
                        'Невірний пароль. Перевірте правильність введення паролю.'
                    )
            except Exception:
                messages.error(
                    self.request,
                    'Користувача не знайдено. Особистий кабінет доступний тільки зареєстрованим оптовим клієнтам.'
                )
            
            return self.form_invalid(form)
        
        # Якщо аутентифікація успішна - логінимо користувача
        login(self.request, user, backend='apps.users.backends.WholesaleClientBackend')
        
        # Оновлюємо сесію для iOS Safari
        self.request.session.modified = True
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Якщо форма невалідна (не заповнені поля)
        if not form.data.get('username'):
            messages.error(self.request, 'Будь ласка, введіть email.')
        elif not form.data.get('password'):
            messages.error(self.request, 'Будь ласка, введіть пароль.')
        
        return super().form_invalid(form)


class CustomPasswordResetView(FormView):
    """Кастомний view для відновлення паролю через код"""
    
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset.html'
    
    def form_valid(self, form):
        email = form.cleaned_data['email']
        logger.info(f"🔐 Password reset requested for email: {email}")
        
        # Перевіряємо чи існує користувач
        users = CustomUser.objects.filter(email__iexact=email, is_active=True)
        if users.exists():
            user = users.first()
            logger.info(f"✅ User found: {user.username}")
            
            # Зберігаємо email в сесії
            self.request.session['password_reset_email'] = email
            
            # Відправляємо код
            if send_password_reset_code_email(user):
                messages.success(
                    self.request,
                    'Код для відновлення паролю відправлено на вашу пошту.'
                )
                return redirect('users:password_reset_code')
            else:
                messages.error(
                    self.request,
                    'Виникла помилка при відправці коду. Спробуйте ще раз.'
                )
                return self.form_invalid(form)
        else:
            logger.warning(f"⚠️ No active user found with email: {email}")
            messages.error(
                self.request,
                'Користувача з таким email не зареєстровано. Будь ласка, зареєструйтеся.'
            )
            return self.form_invalid(form)


class PasswordResetCodeView(FormView):
    """Введення коду відновлення паролю"""
    
    template_name = 'users/password_reset_code.html'
    form_class = PasswordResetCodeForm
    
    def dispatch(self, request, *args, **kwargs):
        # Перевіряємо чи є email в сесії
        if not request.session.get('password_reset_email'):
            messages.error(request, 'Сесія відновлення паролю закінчилась. Спробуйте ще раз.')
            return redirect('users:password_reset')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['email'] = self.request.session.get('password_reset_email')
        return context
    
    def form_valid(self, form):
        email = self.request.session.get('password_reset_email')
        code = form.cleaned_data['code']
        
        try:
            user = CustomUser.objects.get(email=email, is_active=True)
            success, message = user.verify_password_reset_code(code)
            
            if success:
                # Зберігаємо user_id для наступного кроку
                self.request.session['password_reset_user_id'] = user.id
                messages.success(self.request, message)
                return redirect('users:password_reset_new_password')
            else:
                messages.error(self.request, message)
                return self.form_invalid(form)
                
        except CustomUser.DoesNotExist:
            messages.error(self.request, 'Користувача не знайдено.')
            return redirect('users:password_reset')


class PasswordResetNewPasswordView(FormView):
    """Встановлення нового паролю після підтвердження коду"""
    
    template_name = 'users/password_reset_new_password.html'
    form_class = CustomSetPasswordForm
    
    def dispatch(self, request, *args, **kwargs):
        # Перевіряємо чи є user_id в сесії
        if not request.session.get('password_reset_user_id'):
            messages.error(request, 'Сесія відновлення паролю закінчилась. Спробуйте ще раз.')
            return redirect('users:password_reset')
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user_id = self.request.session.get('password_reset_user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            kwargs['user'] = user
        except CustomUser.DoesNotExist:
            pass
        return kwargs
    
    def form_valid(self, form):
        user = form.save()
        
        # Очищаємо код відновлення
        user.clear_password_reset_code()
        
        # Очищаємо сесію
        if 'password_reset_email' in self.request.session:
            del self.request.session['password_reset_email']
        if 'password_reset_user_id' in self.request.session:
            del self.request.session['password_reset_user_id']
        
        messages.success(self.request, 'Пароль успішно змінено! Тепер ви можете увійти.')
        return redirect('users:login')


class ResendPasswordResetCodeView(View):
    """Повторна відправка коду відновлення паролю"""
    
    def post(self, request):
        email = request.session.get('password_reset_email')
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Сесія відновлення паролю закінчилась.'
            })
        
        try:
            user = CustomUser.objects.get(email=email, is_active=True)
            
            if send_password_reset_code_email(user):
                logger.info(f"Password reset code resent to {email}")
                return JsonResponse({
                    'success': True,
                    'message': 'Код відправлено повторно!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Помилка при відправці коду.'
                })
                
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Користувача не знайдено.'
            })
