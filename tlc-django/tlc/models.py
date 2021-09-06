from datetime import datetime, timedelta
from email.policy import default
import random
from typing import List
from django.db.models.deletion import CASCADE
import jwt as jwt
from django.contrib.auth.models import AbstractUser
from django.db import models
from configs import settings

from .validators import *


class User(AbstractUser):
    """
    [User]
    Переопределенный класс пользователя. Использует кастомный менеджер.
    """

    name = models.CharField(max_length=30, blank=True, null=True, verbose_name="имя пользователя")
    username = models.CharField(max_length=50, unique=True, verbose_name='номер телефона/email')
    photo = models.ImageField(upload_to='user_images', blank=True, null=True)

    USERNAME_FIELD = 'username'

    def __str__(self) -> str:
        return f"{self.username}"

    @property
    def token(self) -> str:
        return self._generate_jwt_token()

    def _generate_jwt_token(self) -> str:
        """
        Генерирует веб-токен JSON, в котором хранится идентификатор этого
        пользователя, срок действия токена составляет 30 дней от создания
        """
        dt = datetime.now() + timedelta(days=30)

        token = jwt.encode({
            'id': self.pk,
            'expire': str(dt)
        }, settings.SECRET_KEY, algorithm='HS256')

        return token.decode('utf-8')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class ConfirmCode(models.Model):
    """
    [ConfirmCode]
    Модель кода подтверждения для регистрации
    """
    user = models.ForeignKey(User, on_delete=CASCADE)
    code = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        self.code = random.randint(1000, 9999)
        super(ConfirmCode, self).save(*args, **{})


class Article(models.Model):
    """
    [Article]
    Модель записи в новостях
    """

    title = models.CharField(max_length=50, default="Без заголовка", verbose_name="Заголовок")
    summary = models.TextField(max_length=150, blank=True, null=True, verbose_name='Аннотация')
    photo = models.ImageField(upload_to='news_photos', blank=True, null=True)
    text = models.TextField(blank=True, null=True, verbose_name="Текст")

    def __str__(self) -> str:
        return f"{self.title}"

    class Meta:
        verbose_name = 'Новостная запись'
        verbose_name_plural = 'Новостные записи'


class Document(models.Model):
    """
    [Document]
    Модель документа
    """

    title = models.CharField(max_length=50, default="Без названия", verbose_name="Название")
    file = models.FileField(upload_to='documents', validators=(validate_file_extension,))
    is_educate = models.BooleanField(default=False, verbose_name="Документ для раздела Обучение?")

    def __str__(self) -> str:
        return f"{self.title}"

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'


class Chat(models.Model):
    """
    [Chat]
    Модель чата
    """

    title = models.CharField(max_length=50, default="Без названия", verbose_name="Название")
    link = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.link})"

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'


class Social(models.Model):
    """
    [Social]
    Модель соц сети
    """

    link = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.link}"

    class Meta:
        verbose_name = 'Социальная сеть'
        verbose_name_plural = 'Социальные сети'


class AttachmentPhoto(models.Model):
    """
    [AttachmentPhoto]
    Модель прикрепляемого фото
    """
    photo = models.ImageField(upload_to='images', blank=False, verbose_name="Файл")

    def __str__(self) -> str:
        return str(self.id)

    class Meta:
        verbose_name = 'Фото'
        verbose_name_plural = 'Фото'


class About(models.Model):
    """
    [About]
    Модель страницы "О компании"
    """

    video = models.FileField(upload_to='video', blank=False, verbose_name="Видео")
    text = models.TextField(null=True, blank=True)
    attaches = models.ManyToManyField(AttachmentPhoto)

    def __str__(self) -> str:
        return f"О компании"

    class Meta:
        verbose_name = 'О компании'
        verbose_name_plural = 'О компании'


class ProductCategory(models.Model):
    """
    [ProductCategory]
    Модель категории товара
    """

    title = models.CharField(max_length=70, blank=True, null=True, verbose_name="название категории")

    def __str__(self) -> str:
        return f"{self.title}"

    class Meta:
        verbose_name = 'Категория продуктов'
        verbose_name_plural = 'Категории продуктов'


class Product(models.Model):
    """
    [Product]
    Модель товара
    """

    title = models.CharField(max_length=70, blank=True, null=True, verbose_name="название товара")
    photo = models.ImageField(upload_to='products', null=True, blank=True)
    summary = models.TextField(blank=True, null=True, verbose_name="краткое описание")
    text = models.TextField(blank=True, null=True, verbose_name="описание")
    category = models.ForeignKey(ProductCategory, on_delete=CASCADE)
    top = models.IntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.title}"

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'


class ProductResults(models.Model):
    """
    [ProductResults]
    Модель результатов по товару
    """

    product = models.ForeignKey(Product, on_delete=CASCADE)
    name = models.CharField(max_length=50, blank=True, null=True, verbose_name="Имя")
    photo_before = models.ImageField(upload_to='products_res_before', null=True, blank=True, verbose_name="Фото до")
    photo_after = models.ImageField(upload_to='products_res_after', null=True, blank=True, verbose_name="Фото после")
    text = models.TextField(blank=True, null=True, verbose_name="описание отзыва")
    links = models.JSONField(default=dict, blank=True)

    def __str__(self) -> str:
        return f"{self.product.title} ({self.name})"

    class Meta:
        verbose_name = 'Результат по продукту'
        verbose_name_plural = 'Результаты по продукту'


class Video(models.Model):
    """
    [Video]
    Модель видео
    """

    title = models.CharField(max_length=50, default="Без названия", verbose_name="Название")
    file = models.FileField(upload_to='video', validators=(validate_video_extension,))
    is_educate = models.BooleanField(default=False, verbose_name="Видео для раздела Обучение?")

    def __str__(self) -> str:
        return f"{self.title}"

    class Meta:
        verbose_name = 'Видео'
        verbose_name_plural = 'Видео'


class FAQ(models.Model):
    """
    [FAQ]
    Модель FAQ
    """

    question = models.TextField(verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")

    def __str__(self) -> str:
        return f"{self.question}"

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQ'
