"""
Management команда для додавання товару в блок новинок
"""
from django.core.management.base import BaseCommand, CommandError
from apps.products.models import Product, NewProduct


class Command(BaseCommand):
    help = 'Додає товар в блок "Новинки" на головній сторінці'

    def add_arguments(self, parser):
        parser.add_argument(
            'product_id',
            type=int,
            help='ID товару для додавання в новинки'
        )
        parser.add_argument(
            '--sort-order',
            type=int,
            default=0,
            help='Порядок сортування (за замовчуванням: 0)'
        )

    def handle(self, *args, **options):
        product_id = options['product_id']
        sort_order = options['sort_order']

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise CommandError(f'Товар з ID {product_id} не знайдено')

        # Перевіряємо чи товар вже в новинках
        if NewProduct.objects.filter(product=product).exists():
            self.stdout.write(
                self.style.WARNING(f'Товар "{product.name}" вже в блоці новинок')
            )
            return

        # Додаємо товар в новинки
        new_product = NewProduct.objects.create(
            product=product,
            sort_order=sort_order,
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Товар "{product.name}" додано в новинки (позиція {sort_order})'
            )
        )

