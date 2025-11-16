from django.test import TestCase

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Link, ClickEvent

from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

class PublicShortenAPITests(APITestCase):
    def test_create_short_link_success(self):
        """
        Публичный эндпоинт /api/v1/shorten/ успешно создаёт короткую ссылку
        """
        url = reverse("v1:public-shorten")
        data = {
            "original_url": "https://ya.ru/",
            "title": "Моя первая короткая ссылка",
        }

        response = self.client.post(url, data, format="json")

        # 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # В ответе есть необходимые поля
        self.assertIn("short_code", response.data)
        self.assertIn("short_url", response.data)
        self.assertEqual(response.data["original_url"], data["original_url"])

        # Ссылка действительно создалась в базе
        short_code = response.data["short_code"]
        self.assertTrue(Link.objects.filter(short_code=short_code).exists())

        link = Link.objects.get(short_code=short_code)
        self.assertEqual(link.original_url, data["original_url"])
        self.assertEqual(link.title, data["title"])
        self.assertIsNone(link.owner)  # публичный, без владельца
        self.assertEqual(link.clicks_count, 0)

    def test_create_short_link_validation_error(self):
        """
        Если не передать original_url, должен вернуться 400 и ошибка валидации
        """
        url = reverse("v1:public-shorten")
        data = {
            # "original_url" специально не передаём
            "title": "Без URL",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("original_url", response.data)

class RedirectViewTests(APITestCase):
    def test_public_redirect_increases_clicks_and_returns_302(self):
        """
        Публичный редирект /r/<short_code>/:
        - возвращает 302 Redirect
        - увеличивает clicks_count
        - создаёт запись ClickEvent
        """
        link = Link.objects.create(
            owner=None,
            original_url="https://ya.ru/",
            short_code="test123",
            title="Тестовый редирект",
        )
        self.assertEqual(link.clicks_count, 0)

        # Имя маршрута в shortener_project/urls.py: "redirect_public"
        redirect_url = reverse("redirect_public", kwargs={"short_code": link.short_code})

        response = self.client.get(redirect_url, follow=False)

        # 302 Redirect
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response["Location"], link.original_url)

        # Перечитываем объект из базы и проверяем счётчик
        link.refresh_from_db()
        self.assertEqual(link.clicks_count, 1)

        # Проверяем, что создался ClickEvent
        self.assertEqual(ClickEvent.objects.filter(link=link).count(), 1)


class LinkViewSetTests(APITestCase):
    """
    Тесты для LinkViewSet:
    - авторизованное создание ссылки
    - список ссылок только владельца
    - поиск / фильтрация по параметру search
    - check_alive
    """

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="user1",
            password="pass12345",
        )
        self.other_user = User.objects.create_user(
            username="user2",
            password="pass12345",
        )

        # базовый URL для LinkViewSet
        # basename="links", namespace="v1" → "v1:links-list"
        self.links_list_url = reverse("v1:links-list")

    # 1) Авторизованное создание ссылок через LinkViewSet
    def test_create_link_authorized(self):
        self.client.force_authenticate(self.user)

        payload = {
            "original_url": "https://example.com",
            "title": "Моя тестовая ссылка",
        }

        response = self.client.post(self.links_list_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # из ответа берём id и проверяем в базе владельца
        link_id = response.data["id"]
        link = Link.objects.get(pk=link_id)
        self.assertEqual(link.owner, self.user)
        self.assertEqual(link.original_url, payload["original_url"])

    # 2) /api/v1/links/ — список только ссылок владельца
    def test_links_list_returns_only_owner_links(self):
        # ссылка пользователя 1
        link1 = Link.objects.create(
            owner=self.user,
            original_url="https://owner-link.com",
            short_code="own111",
        )
        # ссылка другого пользователя
        Link.objects.create(
            owner=self.other_user,
            original_url="https://other-link.com",
            short_code="oth222",
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(self.links_list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # пагинации нет → просто список
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], link1.id)
        self.assertEqual(response.data[0]["original_url"], link1.original_url)

    # 3) Тест фильтрации/поиска ?search=
    def test_search_filter_returns_only_matching_links(self):
        self.client.force_authenticate(self.user)

        # создаём несколько ссылок
        link_google = Link.objects.create(
            owner=self.user,
            original_url="https://google.com",
            title="Поиск",
            short_code="goo123",
        )
        Link.objects.create(
            owner=self.user,
            original_url="https://ya.ru",
            title="Яндекс",
            short_code="ya123",
        )

        # фильтруем по слову "google"
        response = self.client.get(self.links_list_url, {"search": "google"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], link_google.id)
        self.assertIn("google", response.data[0]["original_url"])

    # 4) Тест check_alive (detail-action)
    @patch("shortener.views.urlreq.urlopen")
    def test_check_alive_updates_link_status(self, mock_urlopen):
        """
        Эмулируем успешный HEAD-запрос (код 200) и проверяем,
        что is_alive / last_check_status / last_checked_at обновились
        """
        self.client.force_authenticate(self.user)

        link = Link.objects.create(
            owner=self.user,
            original_url="https://example.com",
            short_code="chk123",
        )

        # Подготавливаем mock под context manager:
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        url = reverse("v1:links-check-alive", args=[link.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Данные из ответа
        self.assertTrue(response.data["is_alive"])
        self.assertEqual(response.data["status"], 200)

        # Обновляем объект из БД и проверяем поля
        link.refresh_from_db()
        self.assertTrue(link.is_alive)
        self.assertEqual(link.last_check_status, 200)
        self.assertIsNotNone(link.last_checked_at)