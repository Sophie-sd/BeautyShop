from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.orders.models import EmailCampaign


class Command(BaseCommand):
    help = 'Відправка запланованих email розсилок'
    
    def handle(self, *args, **options):
        now = timezone.now()
        
        scheduled_campaigns = EmailCampaign.objects.filter(
            status='scheduled',
            scheduled_at__lte=now
        )
        
        if not scheduled_campaigns.exists():
            self.stdout.write(self.style.WARNING('Немає запланованих розсилок для відправки'))
            return
        
        for campaign in scheduled_campaigns:
            self.stdout.write(f'Відправка розсилки: {campaign.name}')
            
            try:
                success = campaign.send_campaign()
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Розсилку "{campaign.name}" відправлено успішно! '
                            f'Відправлено: {campaign.sent_count}, Помилок: {campaign.failed_count}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Помилка при відправці розсилки "{campaign.name}"')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Виняток при відправці "{campaign.name}": {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nОброблено {scheduled_campaigns.count()} розсилок')
        )

