# Generated manually to restore Newsletter table

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0007_delete_newsletter_order_delivery_type_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Newsletter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='Email')),
                ('name', models.CharField(blank=True, max_length=200, verbose_name="Ім'я")),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна підписка')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата підписки')),
            ],
            options={
                'verbose_name': 'Підписка на розсилку',
                'verbose_name_plural': 'Підписки на розсилку',
                'ordering': ['-created_at'],
            },
        ),
    ]

