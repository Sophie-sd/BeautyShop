from django import forms
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class RecipientsCheckboxWidget(forms.CheckboxSelectMultiple):
    """Віджет для вибору отримувачів розсилки з покращеним UI"""
    
    template_name = 'admin/widgets/recipients_checkbox.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs)
        output = []
        
        output.append('<div class="email-campaign-recipients">')
        
        for i, (option_value, option_label) in enumerate(self.choices):
            if has_id:
                final_attrs['id'] = f"{attrs['id']}_{i}"
            
            label_for = format_html(' for="{}"', final_attrs['id']) if has_id else ''
            
            checked = ''
            if str(option_value) in [str(v) for v in value]:
                checked = ' checked'
            
            output.append(format_html(
                '<div class="recipient-option">'
                '<input type="checkbox" name="{}" value="{}" id="{}"{}/>'
                '<label{}>{}</label>'
                '</div>',
                name, option_value, final_attrs['id'], mark_safe(checked),
                mark_safe(label_for), option_label
            ))
        
        output.append('</div>')
        
        return mark_safe('\n'.join(output))

