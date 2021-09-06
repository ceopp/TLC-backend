import re
from django.db.models.deletion import SET_NULL
from django.shortcuts import render

# Create your views here.
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from fcm_django.models import FCMDevice
from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.password_validation import validate_password

from tlc.models import ConfirmCode, User
from tlc.serializers import *

from tlc import utils

import os
import json


class AuthView(viewsets.ViewSet):
    """
    Авторизация пользователей + генерация токена
    """
    permission_classes = (AllowAny,)
    serializer_class = AuthorizationSerializer

    @action(methods=['POST'], detail=False, url_path='signup', url_name='Sign Up User', permission_classes=permission_classes)
    def signup(self, request):
        data = request.data
        serializer = self.serializer_class(data=data, context={"signup": True, "request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['POST'], detail=False, url_path='signin', url_name='Sign In User', permission_classes=permission_classes)
    def signin(self, request):
        data = request.data
        serializer = self.serializer_class(data=data, context={"signup": False, "request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=False, url_path='send', url_name='Send reset code', permission_classes=permission_classes)
    def send_reset_code(self, request):
        """
        Создание кода сброса
        """
        username=request.data.get('username')
        try:
            user = User.objects.get(username=username)
        except Exception:
            return Response({"info": f"there is no user with username {username}"}, status=status.HTTP_400_BAD_REQUEST)
        confirm_code, _ = ConfirmCode.objects.get_or_create(user=user)
        confirm_code.save()

        if re.match(r'^\+7[0-9]{10}$', username):
            # is phone
            return Response({"info": f"confirm code is send to your phone {confirm_code.code}"}, status=status.HTTP_200_OK)
        elif re.match(r'^[\w\.-]+@[\w\.-]+(\.[\w]+)+$', username):
            # is email
            message = f'Ваш код для сброса пароля: {confirm_code.code}'
            utils.send_email(message, username, 'TLC Сброс пароля')
            return Response({"info": f"confirm code is send to your email {username}"}, status=status.HTTP_200_OK)
        else:
            # error
            return Response({"info": f"invalid username"}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=False, url_path='reset', url_name='Reset password', permission_classes=permission_classes)
    def reset_password(self, request):
        """
        Сброс пароля пользователя
        """
        username=request.data.get('username')
        user = User.objects.get(username=username)
        confirm_code_data = int(request.data.get('code'))
        confirm_code = ConfirmCode.objects.filter(user=user).first()
        new_pass = request.data.get('password')
        # try:
        #     validate_password(new_pass)
        # except Exception as e:
        #     return Response({"info": e})
        if confirm_code is None:
            return Response({"info": f"Reset code was not send"}, status=status.HTTP_400_BAD_REQUEST)
        if confirm_code_data != confirm_code.code:
            return Response({"info": f"Wrong code"}, status=status.HTTP_400_BAD_REQUEST)
        confirm_code.delete()
        user.set_password(new_pass)
        user.save()
        return Response({"info": f"Password was reset successfully"}, status=status.HTTP_200_OK)


class UserView(viewsets.ViewSet):
    """
    Обновление профиля пользователя. Вывод информации о пользователе
    Использую экшны только для того, чтобы сохранить исходные роутинги
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = UserUpdateSerializer

    @action(methods=['PATCH'], detail=False, url_path='edit', url_name='Edit User', permission_classes=[IsAuthenticated])
    def edit_user(self, request, *args, **kwargs):
        data = request.data
        serializer = self.serializer_class(instance=request.user, data=data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserDetailSerializer(instance=user, context={"request": request}).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='me', url_name='About User', permission_classes=[IsAuthenticated])
    def about_user(self, request, *args, **kwargs):
        return Response(UserDetailSerializer(instance=request.user, context={"request": request}).data, status=status.HTTP_200_OK)


class NewsView(viewsets.ViewSet):
    """
    Получение новостей
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = ArticleSerializer

    @action(methods=['GET'], detail=False, url_path='all', url_name='Get all news', permission_classes=[IsAuthenticated])
    def all_news(self, request, *args, **kwargs):
        articles = Article.objects.all()
        return Response(ArticleSerializer(instance=articles, many=True, context={"request": request}).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='(?P<id>[^/]+)', url_name='Get article by id', permission_classes=[IsAuthenticated])
    def get_article(self, request, id, *args, **kwargs):
        article = Article.objects.get(id=id)
        return Response(ArticleSerializer(instance=article, context={"request": request}).data, status=status.HTTP_200_OK)


class DocumentsView(viewsets.ViewSet):
    """
    Получение документов
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = DocumentSerializer

    @action(methods=['GET'], detail=False, url_path='all', url_name='Get all documents', permission_classes=permission_classes)
    def all_docs(self, request, *args, **kwargs):
        docs = Document.objects.filter(is_educate=False)
        return Response(self.serializer_class(instance=docs, many=True, context={"request": request}).data, status=status.HTTP_200_OK)


class VideoView(viewsets.ViewSet):
    """
    Получение видео
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = VideoSerializer

    @action(methods=['GET'], detail=False, url_path='all', url_name='Get all videos', permission_classes=permission_classes)
    def all_videos(self, request, *args, **kwargs):
        videos = Video.objects.filter(is_educate=False)
        return Response(self.serializer_class(instance=videos, many=True, context={"request": request}).data, status=status.HTTP_200_OK)


class ChatView(viewsets.ViewSet):
    """
    Получение чатов
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = ChatSerializer

    @action(methods=['GET'], detail=False, url_path='all', url_name='Get all chats', permission_classes=permission_classes)
    def all_chats(self, request, *args, **kwargs):
        chats = Chat.objects.all()
        return Response(self.serializer_class(instance=chats, many=True, context={"request": request}).data, status=status.HTTP_200_OK)


class SocialView(viewsets.ViewSet):
    """
    Получение соц сетей
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = SocialSerializer

    @action(methods=['GET'], detail=False, url_path='all', url_name='Get all socials', permission_classes=permission_classes)
    def all_socials(self, request, *args, **kwargs):
        socials = Social.objects.all()
        return Response(self.serializer_class(instance=socials, many=True, context={"request": request}).data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_about(request):
    """
    Получение информации о компании
    """
    about = About.objects.first()
    return Response(AboutSerializer(instance=about, context={"request": request}).data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def support(request):
    """
    Отправка сообщения в техническую поддержку
    """
    user = request.user
    text = f"Отправлено: {user.username}"
    text += '\n\n' + request.data['text']

    utils.send_email(text, os.environ.get('EMAIL_SUPPORT'), 'Сообщение в поддержку')
    return Response({"info": "sended successfully"}, status=status.HTTP_200_OK)


class ProductView(viewsets.ViewSet):
    """
    Получение соц сетей
    """
    permission_classes = (IsAuthenticated, )

    @action(methods=['GET'], detail=False, url_path='categories', url_name='Get all product categories', permission_classes=permission_classes)
    def get_categories(self, request, *args, **kwargs):
        product_categories = ProductCategory.objects.all()
        return Response(ProductCategorySerializer(instance=product_categories, many=True, context={"request": request}).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='categories/(?P<id>[^/]+)', url_name='Get all products in category', permission_classes=permission_classes)
    def get_products_cat(self, request, id, *args, **kwargs):
        products = Product.objects.filter(category = ProductCategory.objects.get(id=id))
        return Response(ProductSerializer(instance=products, many=True, context={"request": request}).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='results/(?P<id>[^/]+)', url_name='Get results for product', permission_classes=permission_classes)
    def get_results(self, request, id, *args, **kwargs):
        product_results = ProductResults.objects.filter(product = Product.objects.get(id=id))
        return Response(ProductResultSerializer(instance=product_results, many=True, context={"request": request}).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='top', url_name='Get top product', permission_classes=permission_classes)
    def get_top(self, request, *args, **kwargs):
        products = Product.objects.filter(top__isnull=False).order_by('top')[0:5]
        return Response(ProductSerializer(instance=products, many=True, context={"request": request}).data, status=status.HTTP_200_OK)


class EducationView(viewsets.ViewSet):
    """
    Получение объектов для обучения
    """
    permission_classes = (IsAuthenticated, )

    @action(methods=['GET'], detail=False, url_path='docs', url_name='Get all edu documents', permission_classes=permission_classes)
    def all_edu_docs(self, request, *args, **kwargs):
        docs = Document.objects.filter(is_educate=True)
        return Response(DocumentSerializer(instance=docs, many=True, context={"request": request}).data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=False, url_path='video', url_name='Get all edu videos', permission_classes=permission_classes)
    def all_edu_videos(self, request, *args, **kwargs):
        videos = Video.objects.filter(is_educate=True)
        return Response(VideoSerializer(instance=videos, many=True, context={"request": request}).data, status=status.HTTP_200_OK)
    
    @action(methods=['GET'], detail=False, url_path='faq', url_name='Get all FAQ', permission_classes=permission_classes)
    def all_edu_faq(self, request, *args, **kwargs):
        faqs = FAQ.objects.all()
        return Response(FAQSerializer(instance=faqs, many=True, context={"request": request}).data, status=status.HTTP_200_OK)


