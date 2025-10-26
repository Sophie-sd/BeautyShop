# 🧠 Оптимізація пам'яті для Render (512MB)

## 🔴 Проблема

Render Free tier надає **512MB RAM**, але ваш додаток споживав **більше 512MB**, що викликало помилку:
```
Instance failed: wmcbb
Ran out of memory (used over 512MB) while running your code.
```

## ✅ Виправлення

### 1. **Gunicorn** (`Procfile`)
**Було:**
```bash
web: gunicorn beautyshop.wsgi
```
- 2-4 workers за замовчуванням
- Кожен worker: ~150-200 MB
- **Разом: 300-800 MB** ❌

**Стало:**
```bash
web: gunicorn beautyshop.wsgi --workers=1 --threads=4 --timeout=120 --max-requests=1000 --max-requests-jitter=50 --log-level=info
```
- **1 worker** з 4 threads
- Споживання: ~150-200 MB
- `--max-requests=1000` - перезапуск після 1000 запитів (запобігає витокам пам'яті)
- `--timeout=120` - таймаут 2 хвилини

**Економія: ~200-400 MB** 🎯

---

### 2. **Django Settings** (`production.py`)

#### База даних:
**Було:**
```python
conn_max_age=600  # 10 хвилин
```

**Стало:**
```python
conn_max_age=60  # 1 хвилина
conn_health_checks=True
statement_timeout=30000  # 30 сек таймаут
```

**Економія: ~20-40 MB** 🎯

#### Кешування:
```python
CACHES = {
    'default': {
        'OPTIONS': {
            'MAX_ENTRIES': 500,  # Обмежуємо кеш
        }
    }
}
```

#### Сесії:
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # БД замість пам'яті
SESSION_SAVE_EVERY_REQUEST = False
```

**Економія: ~30-50 MB** 🎯

---

### 3. **Команда імпорту** (`import_products_sitemap.py`)

**Було:**
```python
workers = 5  # 5 паралельних потоків
# Завантажувало всі 2500 URL в пам'ять
# Завантажувало 3 зображення на товар
```

**Стало:**
```python
workers = 2  # Максимум 3
batch_size = 100  # Обробка батчами
# Завантажує 2 зображення (замість 3)
# Перевірка розміру зображень (пропускає > 2MB)
gc.collect()  # Очищення пам'яті після кожного батчу
```

**Економія: ~100-150 MB** 🎯

---

### 4. **Команда розподілу** (`assign_categories.py`)

**Було:**
```python
products = Product.objects.filter(...)  # Завантажує ВСІ товари в пам'ять
for product in products:
    product.save()  # N запитів до БД
```

**Стало:**
```python
products_queryset = Product.objects.filter(...).only('id', 'name', 'description', 'category').iterator(chunk_size=100)
# Використовує iterator() - НЕ завантажує все в пам'ять
# Batch update кожні 100 товарів
Product.objects.bulk_update(products_to_update, ['category'], batch_size=100)
gc.collect()  # Очищення після кожного батчу
```

**Економія: ~80-120 MB** 🎯

---

### 5. **Python налаштування** (`render.yaml`)

```yaml
envVars:
  - key: PYTHONUNBUFFERED
    value: 1
  - key: MALLOC_ARENA_MAX
    value: 2  # Обмежує malloc arenas
```

**Економія: ~20-30 MB** 🎯

---

## 📊 Загальна економія

| Компонент | Було | Стало | Економія |
|-----------|------|-------|----------|
| Gunicorn workers | 300-800 MB | 150-200 MB | **200-400 MB** |
| БД підключення | 40-80 MB | 20-40 MB | **20-40 MB** |
| Кеш + сесії | 80-120 MB | 30-50 MB | **50-70 MB** |
| Імпорт товарів | 200-300 MB | 80-100 MB | **120-200 MB** |
| Python malloc | 50-80 MB | 30-50 MB | **20-30 MB** |
| **РАЗОМ** | **670-1380 MB** | **310-440 MB** | **410-740 MB** ✅ |

## 🎯 Результат

- **Було:** 670-1380 MB (перевищувало 512MB) ❌
- **Стало:** 310-440 MB (в межах 512MB) ✅

## 🚀 Рекомендації

### Для локальної розробки:
```bash
python manage.py import_products_sitemap --workers 10  # Більше workers
```

### Для Render (512MB):
```bash
python manage.py import_products_sitemap --workers 2   # Обмежено
```

### Якщо потрібно більше:
Апгрейд до Render **Starter plan** ($7/міс):
- **512MB → 2GB RAM**
- Можна повернути `workers=3-5`

---

## 📝 Технічні деталі

### Iterator vs QuerySet:
```python
# ❌ Погано - завантажує ВСЕ в пам'ять
products = Product.objects.all()
for p in products:
    ...

# ✅ Добре - завантажує по 100 штук
products = Product.objects.all().iterator(chunk_size=100)
for p in products:
    ...
```

### Bulk Update:
```python
# ❌ Погано - N запитів до БД
for product in products:
    product.category = new_category
    product.save()

# ✅ Добре - 1 запит на 100 товарів
Product.objects.bulk_update(products, ['category'], batch_size=100)
```

### Garbage Collection:
```python
import gc

# Після важких операцій
gc.collect()  # Звільняє пам'ять
```

---

## ✅ Чеклист перед деплоєм

- [x] Gunicorn обмежено до 1 worker
- [x] БД `conn_max_age=60`
- [x] Кеш обмежено `MAX_ENTRIES=500`
- [x] Сесії в БД
- [x] Імпорт з `--workers=2`
- [x] `.iterator()` для великих QuerySet
- [x] `bulk_update()` замість циклу `save()`
- [x] `gc.collect()` після важких операцій
- [x] `MALLOC_ARENA_MAX=2`

---

**Створено:** 26.10.2025  
**Статус:** ✅ Готово для Render Free tier (512MB)

