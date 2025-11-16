from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LinkViewSet, CategoryViewSet, TagViewSet, PublicShorten, redirect_view

router = DefaultRouter()
router.register(prefix="links", viewset=LinkViewSet, basename="links")
router.register(prefix="categories", viewset=CategoryViewSet, basename="categories")
router.register(prefix="tags", viewset=TagViewSet, basename="tags")

urlpatterns = [
    # публичный эндпоинт для создания короткой ссылки
    path("shorten/", PublicShorten.as_view(), name="public-shorten"),

    # REST API для авторизованных пользователей
    path("", include(router.urls)),

    # РЕДИРЕКТ ВНУТРИ /api/v1/
    path("r/<str:short_code>/", redirect_view, name="redirect"),
]