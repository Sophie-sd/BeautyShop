"""
Форми для адмін-панелі товарів з валідацією
"""
from django import forms
from django.core.exceptions import ValidationError
from ckeditor.widgets import CKEditorWidget
from .models import Product


class ProductAdminForm(forms.ModelForm):
    """Форма додавання/редагування товару з валідацією"""
    
    description = forms.CharField(
        label='Опис товару',
        widget=CKEditorWidget(),
        required=False,
        help_text='Детальний опис товару. Буде відображатися у вкладці "Опис" на сторінці товару'
    )
    
    characteristics = forms.CharField(
        label='Характеристики товару',
        widget=CKEditorWidget(),
        required=False,
        help_text='Характеристики товару (виробник, об\'єм, склад тощо). Буде відображатися у вкладці "Характеристики"'
    )
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def clean(self):
        """Загальна валідація форми"""
        cleaned_data = super().clean()
        
        retail_price = cleaned_data.get('retail_price')
        wholesale_price = cleaned_data.get('wholesale_price')
        sale_price = cleaned_data.get('sale_price')
        price_3_qty = cleaned_data.get('price_3_qty')
        price_5_qty = cleaned_data.get('price_5_qty')
        is_sale = cleaned_data.get('is_sale')
        sale_start_date = cleaned_data.get('sale_start_date')
        sale_end_date = cleaned_data.get('sale_end_date')
        stock = cleaned_data.get('stock')
        is_active = cleaned_data.get('is_active')
        
        # Перевірка оптової ціни
        if wholesale_price and retail_price:
            if wholesale_price >= retail_price:
                raise ValidationError({
                    'wholesale_price': 'Оптова ціна повинна бути меншою за роздрібну ціну'
                })
        
        # Перевірка акційної ціни
        if is_sale:
            if not sale_price:
                raise ValidationError({
                    'sale_price': 'Вкажіть акційну ціну, якщо товар позначено як акційний'
                })
            if sale_price >= retail_price:
                raise ValidationError({
                    'sale_price': 'Акційна ціна повинна бути меншою за роздрібну ціну'
                })
        
        # Перевірка дат акції
        if sale_start_date and sale_end_date:
            if sale_end_date <= sale_start_date:
                raise ValidationError({
                    'sale_end_date': 'Дата закінчення акції повинна бути пізніше дати початку'
                })
        
        # Перевірка градації цін (правило: 5+ <= 3+ <= базова)
        if price_3_qty and retail_price:
            if price_3_qty >= retail_price:
                raise ValidationError({
                    'price_3_qty': 'Ціна "від 3 шт" повинна бути меншою за роздрібну ціну'
                })
        
        if price_5_qty and retail_price:
            if price_5_qty >= retail_price:
                raise ValidationError({
                    'price_5_qty': 'Ціна "від 5 шт" повинна бути меншою за роздрібну ціну'
                })
        
        if price_3_qty and price_5_qty:
            if price_5_qty >= price_3_qty:
                raise ValidationError({
                    'price_5_qty': 'Ціна "від 5 шт" повинна бути меншою або дорівнювати ціні "від 3 шт"'
                })
        
        # Перевірка оптової ціни відносно інших
        if wholesale_price and retail_price:
            if wholesale_price > retail_price:
                raise ValidationError({
                    'wholesale_price': 'Оптова ціна не може бути більшою за роздрібну'
                })
        
        # Попередження про активний товар без наявності
        if is_active and stock == 0:
            self.add_error('stock', 'Увага: товар активний, але кількість на складі = 0. Клієнти не зможуть його замовити.')
        
        return cleaned_data
    
    def clean_retail_price(self):
        """Валідація роздрібної ціни"""
        price = self.cleaned_data.get('retail_price')
        if price and price <= 0:
            raise ValidationError('Роздрібна ціна повинна бути більшою за 0')
        return price
    
    def clean_sku(self):
        """Валідація артикулу"""
        sku = self.cleaned_data.get('sku')
        if sku:
            sku = sku.strip().upper()
            # Перевірка унікальності SKU
            if self.instance.pk:
                # Редагування існуючого товару
                if Product.objects.exclude(pk=self.instance.pk).filter(sku=sku).exists():
                    raise ValidationError(f'Товар з артикулом "{sku}" вже існує')
            else:
                # Додавання нового товару
                if Product.objects.filter(sku=sku).exists():
                    raise ValidationError(f'Товар з артикулом "{sku}" вже існує')
        return sku

