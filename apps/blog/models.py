"""
Моделі блогу
"""
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from ckeditor.fields import RichTextField


class Article(models.Model):
    """Статті блогу"""
    
    title = models.CharField('Заголовок', max_length=200)
    slug = models.SlugField('URL', max_length=200, unique=True, blank=True)
    content = RichTextField('Контент')
    excerpt = models.TextField('Короткий опис', max_length=300, blank=True)
    image = models.ImageField('Зображення', upload_to='articles/', blank=True)
    
    is_published = models.BooleanField('Опубліковано', default=True)
    created_at = models.DateTimeField('Створено', auto_now_add=True)
    updated_at = models.DateTimeField('Оновлено', auto_now=True)
    
    # SEO поля
    meta_title = models.CharField('SEO заголовок', max_length=200, blank=True)
    meta_description = models.TextField('SEO опис', max_length=300, blank=True)
    
    class Meta:
        verbose_name = 'Стаття'
        verbose_name_plural = 'Статті'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'slug': self.slug})
    
    def __str__(self):
        return self.title
