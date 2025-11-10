#!/usr/bin/env python3
"""
Скрипт для виправлення таблиці blog_article на Render
"""
import os
import sys
import django

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beautyshop.settings')
django.setup()

from django.db import connection

def fix_blog_table():
    print("=" * 50)
    print("ВИПРАВЛЕННЯ ТАБЛИЦІ BLOG")
    print("=" * 50)
    
    try:
        with connection.cursor() as cursor:
            # Видаляємо записи про blog міграції
            cursor.execute("DELETE FROM django_migrations WHERE app = 'blog'")
            deleted = cursor.rowcount
            print(f"✓ Видалено записів про blog міграції: {deleted}")
            
            # Перевіряємо чи існує таблиця
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'blog_article'
                );
            """)
            exists = cursor.fetchone()[0]
            
            if not exists:
                print("✓ Створюємо таблицю blog_article...")
                cursor.execute("""
                    CREATE TABLE blog_article (
                        id BIGSERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        slug VARCHAR(200) NOT NULL UNIQUE,
                        content TEXT NOT NULL,
                        excerpt TEXT,
                        image VARCHAR(100),
                        is_published BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                        meta_title VARCHAR(200),
                        meta_description TEXT
                    );
                """)
                print("✓ Таблиця blog_article створена успішно!")
            else:
                print("✓ Таблиця blog_article вже існує")
            
            # Додаємо запис про міграцію
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied)
                VALUES ('blog', '0001_initial', NOW())
                ON CONFLICT DO NOTHING;
            """)
            print("✓ Зареєстровано міграцію 0001_initial")
            
        print("=" * 50)
        print("✅ ВИПРАВЛЕННЯ ЗАВЕРШЕНО УСПІШНО")
        print("=" * 50)
        return 0
        
    except Exception as e:
        print("=" * 50)
        print(f"❌ ПОМИЛКА: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(fix_blog_table())

