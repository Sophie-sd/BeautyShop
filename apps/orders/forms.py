from django import forms
from .models import EmailCampaign
from .widgets import RecipientsCheckboxWidget
from ckeditor.widgets import CKEditorWidget


class EmailCampaignForm(forms.ModelForm):
    """Форма для створення email розсилки"""
    
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
    
    class Meta:
        model = EmailCampaign
        fields = ['name', 'subject', 'content', 'image', 'recipients', 'scheduled_at']
        widgets = {
            'scheduled_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.recipients:
            self.initial['recipients'] = self.instance.recipients
    
    def clean_recipients(self):
        """Конвертуємо вибрані значення в список"""
        recipients = self.cleaned_data.get('recipients')
        return list(recipients) if recipients else []

