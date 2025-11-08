from django import forms
from .models import EmailCampaign
from .widgets import RecipientsCheckboxWidget
from ckeditor.widgets import CKEditorWidget


class EmailCampaignForm(forms.ModelForm):
    """Форма для створення email розсилки"""
    
    SEND_TYPE_CHOICES = [
        ('now', 'Відправити зараз після збереження'),
        ('scheduled', 'Запланувати відправку'),
    ]
    
    send_type = forms.ChoiceField(
        label='Час відправки',
        choices=SEND_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='now',
        required=True
    )
    
    recipients = forms.MultipleChoiceField(
        label='Отримувачі',
        choices=EmailCampaign.RECIPIENT_CHOICES,
        widget=RecipientsCheckboxWidget,
        help_text='Виберіть одну або декілька груп отримувачів'
    )
    
    content = forms.CharField(
        label='Контент листа',
        widget=CKEditorWidget(),
        help_text='Використовуйте редактор для форматування тексту'
    )
    
    scheduled_at = forms.DateTimeField(
        label='Дата та час відправки',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False,
        help_text='Залиште порожнім для відправки зараз'
    )
    
    class Meta:
        model = EmailCampaign
        fields = ['name', 'subject', 'content', 'image', 'recipients', 'scheduled_at']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.recipients:
            self.initial['recipients'] = self.instance.recipients
        
        if self.instance and self.instance.pk and self.instance.scheduled_at:
            self.initial['send_type'] = 'scheduled'
    
    def clean(self):
        cleaned_data = super().clean()
        send_type = cleaned_data.get('send_type')
        scheduled_at = cleaned_data.get('scheduled_at')
        
        if send_type == 'scheduled' and not scheduled_at:
            raise forms.ValidationError('Вкажіть дату та час для запланованої відправки')
        
        if send_type == 'now':
            cleaned_data['scheduled_at'] = None
        
        return cleaned_data
    
    def clean_recipients(self):
        """Конвертуємо вибрані значення в список"""
        recipients = self.cleaned_data.get('recipients')
        return list(recipients) if recipients else []

