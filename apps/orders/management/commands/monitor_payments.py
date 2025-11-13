"""
Management команда для моніторингу невдалих оплат
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.orders.models import PendingPayment
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Моніторинг та очищення старих pending платежів'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Час у годинах для видалення необроблених платежів (за замовчуванням 24)'
        )
        parser.add_argument(
            '--report-only',
            action='store_true',
            help='Тільки звіт без очищення'
        )
    
    def handle(self, *args, **options):
        hours = options['hours']
        report_only = options['report_only']
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        pending_count = PendingPayment.objects.filter(
            is_processed=False,
            created_at__lt=cutoff_time
        ).count()
        
        failed_count = PendingPayment.objects.filter(
            is_processed=True,
            created_order__isnull=True,
            created_at__gte=cutoff_time
        ).count()
        
        self.stdout.write(self.style.WARNING(
            f'\n=== Звіт про оплати (останні {hours} годин) ==='
        ))
        self.stdout.write(f'Невдалих оплат: {failed_count}')
        self.stdout.write(f'Незавершених транзакцій (старіші {hours}h): {pending_count}')
        
        if failed_count > 0:
            logger.warning(f'Виявлено {failed_count} невдалих оплат за останні {hours} годин')
        
        if not report_only and pending_count > 0:
            deleted = PendingPayment.objects.filter(
                is_processed=False,
                created_at__lt=cutoff_time
            ).delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'Видалено {deleted[0]} старих незавершених транзакцій'
            ))
            logger.info(f'Cleanup: видалено {deleted[0]} pending платежів старіших {hours} годин')
        elif report_only:
            self.stdout.write(self.style.NOTICE('Режим звіту - дані не видалено'))

