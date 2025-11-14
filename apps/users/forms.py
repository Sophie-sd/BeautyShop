"""
Форми для користувачів
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from .models import CustomUser, UserProfile
import re


class WholesaleRegistrationForm(UserCreationForm):
    """Форма реєстрації для оптових клієнтів"""
    
    first_name = forms.CharField(
        max_length=100, 
        required=True, 
        label="Ім'я",
        widget=forms.TextInput(attrs={
            'placeholder': "Ваше ім'я",
            'autocomplete': 'given-name'
        })
    )
    last_name = forms.CharField(
        max_length=100, 
        required=True, 
        label="Прізвище",
        widget=forms.TextInput(attrs={
            'placeholder': "Ваше прізвище",
            'autocomplete': 'family-name'
        })
    )
    middle_name = forms.CharField(
        max_length=100, 
        required=True, 
        label="По-батькові",
        widget=forms.TextInput(attrs={
            'placeholder': "По-батькові",
            'autocomplete': 'additional-name'
        })
    )
    email = forms.EmailField(
        required=True, 
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'example@email.com',
            'autocomplete': 'email'
        })
    )
    phone = forms.CharField(
        max_length=10, 
        required=True, 
        label='Телефон',
        widget=forms.TextInput(attrs={
            'placeholder': '0XX XXX XX XX',
            'pattern': '[0-9]{10}',
            'maxlength': '10',
            'autocomplete': 'tel',
            'inputmode': 'numeric'
        }),
        help_text='Введіть 10 цифр (префікс +38 додається автоматично)'
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'middle_name', 'email', 'phone', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Додаємо CSS класи для стилізації
        for field_name, field in self.fields.items():
            if field_name in ['password1', 'password2']:
                field.widget.attrs.update({
                    'class': 'form-control password-field',
                })
            else:
                field.widget.attrs.update({
                    'class': 'form-control',
                })
    
    def clean_phone(self):
        """Валідація телефону"""
        phone = self.cleaned_data.get('phone')
        
        if not phone:
            raise ValidationError('Телефон є обов\'язковим полем')
        
        # Видаляємо всі пробіли та нецифрові символи
        phone = re.sub(r'\D', '', phone)
        
        # Перевірка формату: має бути 10 цифр, що починаються з 0
        if not re.match(r'^0\d{9}$', phone):
            raise ValidationError(
                'Невірний формат телефону. Введіть 10 цифр, починаючи з 0 (наприклад: 0991234567)'
            )
        
        # Додаємо префікс +38
        phone_with_prefix = '+38' + phone
        
        # Перевірка унікальності
        if CustomUser.objects.filter(phone=phone_with_prefix).exists():
            raise ValidationError('Цей номер телефону вже зареєстрований')
        
        return phone_with_prefix
    
    def clean_email(self):
        """Валідація email"""
        email = self.cleaned_data.get('email')
        
        # Перевірка унікальності
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Ця email адреса вже зареєстрована')
        
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.middle_name = self.cleaned_data['middle_name']
        user.phone = self.cleaned_data['phone']
        
        # Генеруємо унікальний username з email
        if not user.username:
            base_username = self.cleaned_data['email'].split('@')[0]
            username = base_username
            counter = 1
            
            # Перевіряємо унікальність username
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user.username = username
        
        # Користувач неактивний до підтвердження email
        user.is_active = False
        # Оптовий статус False - буде встановлено True після підтвердження email
        user.is_wholesale = False
        
        if commit:
            user.save()
            
            # Створюємо профіль користувача
            UserProfile.objects.get_or_create(user=user)
        
        return user


class CustomLoginForm(AuthenticationForm):
    """Покращена форма входу з валідацією - ТІЛЬКИ через email"""
    
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com',
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control password-field',
            'placeholder': '••••••••',
            'autocomplete': 'current-password'
        })
    )


class CustomPasswordResetForm(PasswordResetForm):
    """Покращена форма відновлення паролю"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'example@email.com',
            'autocomplete': 'email'
        })
    
    def get_users(self, email):
        """Повертає користувачів з вказаним email"""
        active_users = CustomUser._default_manager.filter(
            email__iexact=email,
            is_active=True
        )
        return (
            user for user in active_users
            if user.has_usable_password()
        )


class EmailVerificationCodeForm(forms.Form):
    """Форма для введення коду підтвердження email"""
    
    code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        label='Код підтвердження',
        widget=forms.TextInput(attrs={
            'class': 'form-control code-input',
            'placeholder': '123456',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'maxlength': '6',
            'autocomplete': 'one-time-code'
        }),
        help_text='Введіть 6-значний код з email'
    )
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        
        if not code.isdigit():
            raise ValidationError('Код повинен містити тільки цифри')
        
        if len(code) != 6:
            raise ValidationError('Код повинен містити 6 цифр')
        
        return code


class PasswordResetCodeForm(forms.Form):
    """Форма для введення коду відновлення паролю"""
    
    code = forms.CharField(
        max_length=6,
        min_length=6,
        required=True,
        label='Код відновлення',
        widget=forms.TextInput(attrs={
            'class': 'form-control code-input',
            'placeholder': '123456',
            'pattern': '[0-9]{6}',
            'inputmode': 'numeric',
            'maxlength': '6',
            'autocomplete': 'one-time-code'
        }),
        help_text='Введіть 6-значний код з email'
    )
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        
        if not code.isdigit():
            raise ValidationError('Код повинен містити тільки цифри')
        
        if len(code) != 6:
            raise ValidationError('Код повинен містити 6 цифр')
        
        return code


class CustomSetPasswordForm(SetPasswordForm):
    """Форма для встановлення нового паролю після підтвердження коду"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control password-field',
            'placeholder': 'Новий пароль',
            'autocomplete': 'new-password'
        })
        
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control password-field',
            'placeholder': 'Підтвердіть новий пароль',
            'autocomplete': 'new-password'
        })


class ProfileEditForm(forms.ModelForm):
    """Форма редагування профілю користувача"""
    
    first_name = forms.CharField(
        max_length=100,
        required=True,
        label="Ім'я",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Ваше ім'я",
            'autocomplete': 'given-name'
        })
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        label="Прізвище",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "Ваше прізвище",
            'autocomplete': 'family-name'
        })
    )
    
    middle_name = forms.CharField(
        max_length=100,
        required=True,
        label="По-батькові",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': "По-батькові",
            'autocomplete': 'additional-name'
        })
    )
    
    phone = forms.CharField(
        max_length=10,
        required=True,
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0XX XXX XX XX',
            'pattern': '[0-9]{10}',
            'maxlength': '10',
            'autocomplete': 'tel',
            'inputmode': 'numeric'
        }),
        help_text='Введіть 10 цифр (префікс +38 додається автоматично)'
    )
    
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@email.com',
            'autocomplete': 'email',
            'readonly': 'readonly'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'middle_name', 'phone', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['readonly'] = True
        
        # Якщо у користувача вже є телефон, показуємо його без префікса +38
        if self.instance and self.instance.phone:
            phone_value = self.instance.phone
            if phone_value.startswith('+38'):
                # Видаляємо +38 для відображення
                self.initial['phone'] = phone_value[3:]
            else:
                self.initial['phone'] = phone_value
    
    def clean_phone(self):
        """Валідація телефону"""
        phone = self.cleaned_data.get('phone')
        
        if not phone:
            raise ValidationError('Телефон є обов\'язковим полем')
        
        # Видаляємо всі пробіли та нецифрові символи
        phone = re.sub(r'\D', '', phone)
        
        # Перевірка формату: має бути 10 цифр, що починаються з 0
        if not re.match(r'^0\d{9}$', phone):
            raise ValidationError(
                'Невірний формат телефону. Введіть 10 цифр, починаючи з 0 (наприклад: 0991234567)'
            )
        
        # Додаємо префікс +38
        phone_with_prefix = '+38' + phone
        
        # Перевірка унікальності (виключаючи поточного користувача)
        if CustomUser.objects.filter(phone=phone_with_prefix).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Цей номер телефону вже зареєстрований')
        
        return phone_with_prefix
