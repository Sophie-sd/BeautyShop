"""
Розподіл товарів по категоріях на основі ключових слів
"""
from django.core.management.base import BaseCommand
from apps.products.models import Product, Category
import re


class Command(BaseCommand):
    help = 'Розподіл товарів з "Імпорт з Webosova" по правильних категоріях'

    CATEGORY_KEYWORDS = {
        'nigti': ['гель-лак', 'база', 'топ', 'primer', 'base', 'top', 'нігт', 'манікюр', 
                  'акрил', 'гель для нарощування', 'nail', 'лак для нігтів', 'покриття',
                  'кутикул', 'масло для нігтів', 'олія для нігтів', 'зміцнення нігтів'],
        
        'volossia': ['шампунь', 'бальзам', 'маска для волосся', 'кондиціонер', 'фарба для волосся',
                     'хна для волосся', 'воск для волосся', 'лак для волосся', 'перукар'],
        
        'brovy-ta-vii': ['фарба для брів', 'хна для брів', 'гель для брів', 'фіксатор для брів',
                         'шампунь для брів', 'ламінування', 'вії', 'туш', 'пінцет для брів'],
        
        'depilyatsiya': ['віск', 'шугаринг', 'паста для шугарінгу', 'цукрова паста', 'депіляція',
                        'воскоплав', 'шпател', 'смужки для депіляції', 'картридж'],
        
        'kosmetyka': ['крем', 'сироватка', 'пілінг', 'тонік', 'міцелярна вода', 'молочко',
                      'скраб', 'гель для обличчя', 'догляд за шкірою', 'очищення'],
        
        'makiyazh': ['тональний', 'пудра', 'рум\'яна', 'тіні', 'помада', 'блиск для губ',
                     'олівець', 'консилер', 'хайлайтер', 'бронзатор'],
        
        'odnorazova-produktsia': ['бахіли', 'рукавички', 'маска одноразова', 'серветки',
                                  'простирадло одноразове', 'шапочка', 'фартух одноразовий',
                                  'одноразов'],
        
        'dezinfektsiya-ta-sterylizatsiya': ['дезінфекція', 'стерилізація', 'антисептик',
                                            'дезінфікуючий засіб', 'ахд', 'крафт-пакет',
                                            'сухожар', 'автоклав', 'бактерицидна лампа'],
        
        'mebli-dlya-saloniv': ['крісло', 'лампа', 'стіл', 'тележка', 'стілець', 'манікюрна витяжка',
                               'світильник', 'меблі', 'обладнання', 'фрезер', 'воскоплав', 'витяжка'],
    }

    def handle(self, *args, **options):
        self.stdout.write('🔄 Розподіл товарів по категоріях...\n')
        
        import_category = Category.objects.filter(slug='import-webosova').first()
        if not import_category:
            self.stdout.write(self.style.ERROR('❌ Категорія "Імпорт з Webosova" не знайдена'))
            return
        
        products = Product.objects.filter(category=import_category)
        total = products.count()
        self.stdout.write(f'📦 Знайдено товарів для розподілу: {total}\n')
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Всі товари вже розподілені!'))
            return
        
        stats = {}
        unassigned = 0
        
        for product in products:
            category_slug = self.detect_category(product)
            
            if category_slug:
                category = Category.objects.filter(slug=category_slug).first()
                if category:
                    product.category = category
                    product.save(update_fields=['category'])
                    stats[category.name] = stats.get(category.name, 0) + 1
                else:
                    unassigned += 1
            else:
                unassigned += 1
        
        self.stdout.write(self.style.SUCCESS('\n✅ Розподіл завершено!\n'))
        self.stdout.write('📊 Статистика:\n')
        
        for cat_name, count in sorted(stats.items(), key=lambda x: -x[1]):
            self.stdout.write(f'  • {cat_name}: {count} товарів')
        
        if unassigned > 0:
            self.stdout.write(self.style.WARNING(f'\n  ⚠ Не розподілено: {unassigned} товарів'))
            self.stdout.write('    (залишились в "Імпорт з Webosova")')

    def detect_category(self, product):
        """Визначає категорію товару за ключовими словами"""
        text = f"{product.name} {product.description}".lower()
        
        scores = {}
        for slug, keywords in self.CATEGORY_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text:
                    score += 1
            if score > 0:
                scores[slug] = score
        
        if not scores:
            return None
        
        return max(scores.items(), key=lambda x: x[1])[0]

