"""
Кошик покупок без реєстрації (session-based)
"""
from decimal import Decimal
from django.conf import settings
from apps.products.models import Product


class Cart:
    """Кошик покупок"""
    
    def __init__(self, request):
        """Ініціалізація кошика"""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        
        # Конвертуємо всі ціни у float (для сумісності зі старими сесіями)
        for item in cart.values():
            if 'price' in item and not isinstance(item['price'], float):
                item['price'] = float(item['price'])
        
        self.cart = cart
        # Адміністратори НЕ є оптовими клієнтами
        if request.user.is_authenticated and not request.user.is_staff and not request.user.is_superuser:
            self.user = request.user
        else:
            self.user = None
    
    def add(self, product, quantity=1, override_quantity=False):
        """Додавання товару в кошик"""
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': float(product.get_price_for_user(self.user))
            }
        if override_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        
        # Оновлюємо ціну (може змінитися залежно від кількості)
        self.cart[product_id]['price'] = float(
            product.get_price_for_user(self.user, self.cart[product_id]['quantity'])
        )
        self.save()
    
    def save(self):
        """Зберігання кошика в сесії"""
        # Гарантуємо що всі ціни float
        for item in self.cart.values():
            if 'price' in item:
                item['price'] = float(item['price'])
        self.session.modified = True
    
    def remove(self, product):
        """Видалення товару з кошика"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
    
    def __iter__(self):
        """Ітерація по товарах в кошику"""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        products_dict = {str(p.id): p for p in products}
        
        for product_id, item in self.cart.items():
            if product_id in products_dict:
                # Створюємо новий словник для кожного item
                yield {
                    'product': products_dict[product_id],
                    'quantity': item['quantity'],
                    'price': Decimal(str(item['price'])),
                    'total_price': Decimal(str(item['price'])) * item['quantity']
                }
    
    def __len__(self):
        """Кількість товарів в кошику"""
        return sum(item['quantity'] for item in self.cart.values())
    
    def get_total_price(self):
        """Загальна вартість кошика"""
        return sum(
            Decimal(str(item['price'])) * item['quantity'] 
            for item in self.cart.values()
        )
    
    def get_original_total_price(self):
        """Повна вартість без знижок"""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        products_dict = {str(p.id): p for p in products}
        
        total = Decimal('0')
        for product_id, item in self.cart.items():
            if product_id in products_dict:
                product = products_dict[product_id]
                if self.user and hasattr(self.user, 'is_wholesale') and self.user.is_wholesale:
                    original_price = product.wholesale_price or product.retail_price
                else:
                    original_price = product.retail_price
                total += Decimal(str(original_price)) * item['quantity']
        return total
    
    def get_savings_amount(self):
        """Сума економії (різниця між оригінальною ціною та поточною)"""
        return self.get_original_total_price() - self.get_total_price()
    
    def clear(self):
        """Очищення кошика"""
        del self.session[settings.CART_SESSION_ID]
        self.save()
    
    def get_item_count(self):
        """Кількість позицій в кошику"""
        return len(self.cart)
    
    def update_quantities(self, product_quantities):
        """Оновлення кількості товарів"""
        product_ids = [pid for pid in product_quantities.keys() if pid in self.cart]
        products = Product.objects.filter(id__in=product_ids)
        products_dict = {str(p.id): p for p in products}
        
        for product_id, quantity in product_quantities.items():
            if product_id in self.cart:
                if quantity <= 0:
                    del self.cart[product_id]
                else:
                    self.cart[product_id]['quantity'] = quantity
                    if product_id in products_dict:
                        product = products_dict[product_id]
                        self.cart[product_id]['price'] = float(
                            product.get_price_for_user(self.user, quantity)
                        )
        self.save()
