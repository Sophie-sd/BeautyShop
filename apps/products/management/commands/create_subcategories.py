"""
Команда для створення підкатегорій для кожної головної категорії
"""
from django.core.management.base import BaseCommand
from apps.products.models import Category


class Command(BaseCommand):
    help = 'Створює підкатегорії для головних категорій'

    def handle(self, *args, **options):
        self.stdout.write('Створення підкатегорій...\n')
        
        # Підкатегорії для кожної категорії
        subcategories_data = {
            'nigti': [
                ('Гель-лаки', 'gel-laky'),
                ('Бази і топи', 'bazy-i-topy'),
                ('Гелі', 'geli'),
                ('Акрили', 'akryly'),
                ('Пензлики', 'penzlyky'),
                ('Пилки та бафи', 'pylky-ta-bafy'),
                ('Декор', 'dekor'),
                ('Засоби для нігтів', 'zasoby-dlya-nigtiv'),
            ],
            'volossia': [
                ('Шампуні', 'shampuni'),
                ('Маски', 'masky'),
                ('Бальзами', 'balzamy'),
                ('Фарби для волосся', 'farby-dlya-volossya'),
                ('Стайлінг', 'stayling'),
                ('Догляд за волоссям', 'doglyad-za-voloссyam'),
            ],
            'brovy-ta-vii': [
                ('Хна для брів', 'khna-dlya-briv'),
                ('Фарби для брів', 'farby-dlya-briv'),
                ('Туш для вій', 'tush-dlya-viy'),
                ('Пінцети', 'pintsety'),
                ('Засоби для брів', 'zasoby-dlya-briv'),
            ],
            'depilyatsiya': [
                ('Віск', 'visk'),
                ('Шугарінг', 'shugaring'),
                ('Засоби після депіляції', 'zasoby-pislya-depilyatsii'),
                ('Інструменти', 'instrumenty'),
            ],
            'kosmetyka': [
                ('Креми', 'kremy'),
                ('Сироватки', 'syrovatky'),
                ('Тоніки', 'toniky'),
                ('Маски для обличчя', 'masky-dlya-oblychya'),
                ('Очищення', 'ochyshchennya'),
            ],
            'makiyazh': [
                ('Тональні засоби', 'tonalni-zasoby'),
                ('Пудри', 'pudry'),
                ('Помади', 'pomady'),
                ('Тіні', 'tini'),
                ('Олівці', 'olivtsi'),
            ],
            'odnorazova-produktsia': [
                ('Рушники', 'rushnyky'),
                ('Простирадла', 'prostyradla'),
                ('Серветки', 'servetky'),
                ('Захист', 'zakhyst'),
            ],
            'dezinfektsiya-ta-sterylizatsiya': [
                ('Дезінфектори', 'dezinfektory'),
                ('Стерилізатори', 'sterylizatory'),
                ('Засоби дезінфекції', 'zasoby-dezinfektsii'),
            ],
            'mebli-dlya-saloniv': [
                ('Крісла', 'krisla'),
                ('Столи', 'stoly'),
                ('Стелажі', 'stelazhi'),
                ('Лампи', 'lampy'),
            ],
        }
        
        created_count = 0
        
        for parent_slug, subcats in subcategories_data.items():
            try:
                parent = Category.objects.get(slug=parent_slug)
                self.stdout.write(f'\n📁 {parent.name}:')
                
                for name, slug in subcats:
                    subcat, created = Category.objects.get_or_create(
                        slug=slug,
                        defaults={
                            'name': name,
                            'parent': parent,
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'  ✅ {name}')
                    else:
                        subcat.parent = parent
                        subcat.is_active = True
                        subcat.save()
                        self.stdout.write(f'  🔄 {name} (оновлено)')
                        
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Категорія {parent_slug} не знайдена')
                )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Створено {created_count} підкатегорій')
        )
        
        total_subcats = Category.objects.filter(parent__isnull=False).count()
        self.stdout.write(f'📊 Всього підкатегорій: {total_subcats}\n')

