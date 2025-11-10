# Generated migration
from django.db import migrations, models
import ckeditor.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок')),
                ('slug', models.SlugField(blank=True, max_length=200, unique=True, verbose_name='URL')),
                ('content', ckeditor.fields.RichTextField(verbose_name='Контент')),
                ('excerpt', models.TextField(blank=True, max_length=300, verbose_name='Короткий опис')),
                ('image', models.ImageField(blank=True, upload_to='articles/', verbose_name='Зображення')),
                ('is_published', models.BooleanField(default=True, verbose_name='Опубліковано')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
                ('meta_title', models.CharField(blank=True, max_length=200, verbose_name='SEO заголовок')),
                ('meta_description', models.TextField(blank=True, max_length=300, verbose_name='SEO опис')),
            ],
            options={
                'verbose_name': 'Стаття',
                'verbose_name_plural': 'Статті',
                'ordering': ['-created_at'],
            },
        ),
    ]

