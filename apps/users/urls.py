"""
URLs для користувачів
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomPasswordResetForm

app_name = 'users'

urlpatterns = [
    # Реєстрація
    path('register/', views.WholesaleRegisterView.as_view(), name='register'),
    path('registration-pending/', views.RegistrationPendingView.as_view(), name='registration_pending'),
    
    # Верифікація email з кодом
    path('verify-email-code/', views.EmailVerificationCodeView.as_view(), name='verify_email_code'),
    path('resend-verification-code/', views.ResendVerificationCodeView.as_view(), name='resend_verification_code'),
    
    # Старий метод з токеном (для зворотної сумісності)
    path('verify-email/<str:token>/', views.EmailVerificationView.as_view(), name='verify_email'),
    
    # Вхід/вихід
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
    
    # Особистий кабінет
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('orders/', views.UserOrdersView.as_view(), name='orders'),
    
    # Відновлення паролю з кодом
    path('password/reset/', 
         views.CustomPasswordResetView.as_view(),
         name='password_reset'),
    path('password/reset/code/', 
         views.PasswordResetCodeView.as_view(),
         name='password_reset_code'),
    path('password/reset/new-password/', 
         views.PasswordResetNewPasswordView.as_view(),
         name='password_reset_new_password'),
    path('password/reset/resend-code/', 
         views.ResendPasswordResetCodeView.as_view(),
         name='resend_password_reset_code'),
    
    # Старі URL для зворотної сумісності (якщо потрібно)
    path('password/reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),
         name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url='/users/password/reset/complete/'
         ),
         name='password_reset_confirm'),
    path('password/reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]
