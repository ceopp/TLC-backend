from django.conf.urls import url
from django.urls import path
from rest_framework.routers import SimpleRouter

from tlc.views import *

router = SimpleRouter()
router.register(r'auth', AuthView, basename='auth')
router.register(r'user', UserView, basename='user')
router.register(r'news', NewsView, basename='news')
router.register(r'docs', DocumentsView, basename='docs')
router.register(r'chats', ChatView, basename='chats')
router.register(r'social', SocialView, basename='social')
router.register(r'product', ProductView, basename='product')
router.register(r'video', VideoView, basename='video')
router.register(r'education', EducationView, basename='education')

urlpatterns = [
    # path('auth/send/', reset_password),
    # url(r'^auth/registration/$', TokenViewSet.as_view()),
    path('about/', get_about),
    path('support/', support),
]

urlpatterns += router.urls
