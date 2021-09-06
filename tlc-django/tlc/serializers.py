from django.core.validators import ProhibitNullCharactersValidator
from django.db.models import fields
from django.utils.functional import empty
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

from .models import *


class AuthorizationSerializer(serializers.Serializer):
    """ Сериализация авторизации """

    token = serializers.CharField(max_length=255, read_only=True)
    username = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=50, required=False)
    password = serializers.CharField(max_length=50, write_only=True)
    # password = serializers.CharField(max_length=50, validators=(validate_password,), write_only=True)
    photo = serializers.ImageField(required=False, use_url=True)

    def create(self, validated_data):
        is_signup = self.context['signup']
        user, created = User.objects.get_or_create(username=validated_data.get('username'))
        if created:
            if not is_signup:
                user.delete()
                raise serializers.ValidationError({'info': 'Bad username/password'})
            # user.name = validated_data['name'] # Так почему то он сохраняет в виде кортежа из одного элемента
            setattr(user, 'name', validated_data['name']) # А вот так как строку
            user.set_password(validated_data.get('password'))
            user.photo = validated_data.get('photo')
            user.save()
        else:
            if is_signup:
                raise serializers.ValidationError({'info': f'User with phone/email {validated_data.get("username")} already exists'})
            if not user.check_password(validated_data.get('password')):
                raise serializers.ValidationError({'info': 'Bad username/password'})
        return user

    class Meta:
        model = User
        fields = "__all__"


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Сериализатор для детального отображения пользователя
    """

    class Meta:
        model = User
        fields = ['username', 'name', 'photo']


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для обновления пользователя
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.photo = validated_data.get('photo')
        old_pass = validated_data.get('old_password')
        new_pass = validated_data.get('new_password')
        if old_pass is not None and new_pass is not None:
            if instance.check_password(old_pass):
                # try:
                #     validate_password(new_pass)
                # except Exception as e:
                #     raise ValidationError(e)
                instance.set_password(new_pass)
            else:
                raise ValidationError({'info': 'Wrong password'})
        instance.save()
        return instance

    class Meta:
        model = User
        fields = ['username', 'name', 'photo', 'old_password', 'new_password']


class ArticleSerializer(serializers.ModelSerializer):
    """
    Сериализатор новостей
    """

    class Meta:
        model = Article
        fields = "__all__"


class DocumentSerializer(serializers.ModelSerializer):
    """
    Сериализатор документов
    """

    class Meta:
        model = Document
        fields = ["id", "title", "file"]


class VideoSerializer(serializers.ModelSerializer):
    """
    Сериализатор видео
    """

    class Meta:
        model = Video
        fields = ["id", "title", "file"]


class FAQSerializer(serializers.ModelSerializer):
    """
    Сериализатор FAQ
    """

    class Meta:
        model = FAQ
        fields = "__all__"


class ChatSerializer(serializers.ModelSerializer):
    """
    Сериализатор чатов
    """

    class Meta:
        model = Chat
        fields = "__all__"


class SocialSerializer(serializers.ModelSerializer):
    """
    Сериализатор соц сетей
    """

    class Meta:
        model = Social
        fields = "__all__"

    
class AttachesSerializer(serializers.ModelSerializer):
    """
    Сериализатор фото
    """

    class Meta:
        model = AttachmentPhoto
        fields = "__all__"


class AboutSerializer(serializers.ModelSerializer):
    """
    Сериализатор "О компании"
    """
    attaches = serializers.SerializerMethodField()

    def get_attaches(self, object):
        services = AttachmentPhoto.objects.all()
        return AttachesSerializer(instance=services, many=True, context=self.context).data

    class Meta:
        model = About
        fields = ["video", "text", "attaches"]


class ProductCategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор категорий продуктов
    """

    class Meta:
        model = ProductCategory
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор продуктов
    """
    category = ProductCategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = "__all__"


class ProductResultSerializer(serializers.ModelSerializer):
    """
    Сериализатор пезультатов по продуктам
    """

    class Meta:
        model = ProductResults
        fields = ['name', 'photo_before', 'photo_after', 'text', 'links']
