from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Виправляє міграції блогу на продакшені'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Виправлення міграцій блогу...'))
        
        with connection.cursor() as cursor:
            try:
                # Видаляємо всі записи про blog міграції
                cursor.execute("DELETE FROM django_migrations WHERE app = 'blog'")
                deleted = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f'Видалено {deleted} записів про blog міграції'))
                
                # Перевіряємо чи існує таблиця
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'blog_article'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                
                if table_exists:
                    self.stdout.write(self.style.SUCCESS('Таблиця blog_article вже існує'))
                else:
                    self.stdout.write(self.style.WARNING('Таблиця blog_article не існує, створюємо...'))
                    
                    # Створюємо таблицю
                    cursor.execute("""
                        CREATE TABLE blog_article (
                            id BIGSERIAL PRIMARY KEY,
                            title VARCHAR(200) NOT NULL,
                            slug VARCHAR(200) NOT NULL UNIQUE,
                            content TEXT NOT NULL,
                            excerpt TEXT,
                            image VARCHAR(100),
                            is_published BOOLEAN NOT NULL DEFAULT TRUE,
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            meta_title VARCHAR(200),
                            meta_description TEXT
                        );
                    """)
                    self.stdout.write(self.style.SUCCESS('Таблиця blog_article створена'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Помилка: {e}'))
                raise
        
        self.stdout.write(self.style.SUCCESS('Виправлення завершено! Тепер запустіть: python manage.py migrate blog --fake'))

