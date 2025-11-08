from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from document.models import Tag

User = get_user_model()


class BaseAPITestCase(APITestCase):
    """Common setup for all document-related API tests."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pass1234")
        self.other_user = User.objects.create_user(username="bob", password="pass1234")
        self.client = APIClient()
        self.client.login(username="alice", password="pass1234")

    def url(self, name, **kwargs):
        """Shortcut for reversing URLs with kwargs."""
        return reverse(name, kwargs=kwargs)


class TagViewSetTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        self.tag = Tag.objects.create(name="finance")

    def test_list_tags(self):
        # --- Arrange
        url = self.url("tag-list")

        # --- Act
        response = self.client.get(url)
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.tag.name, [tag["name"] for tag in data])

    def test_create_tag(self):
        # --- Arrange
        url = self.url("tag-list")
        tag_name = "bill"

        # --- Act
        response = self.client.post(url, {"name": tag_name})
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data["name"], tag_name)
        self.assertTrue(Tag.objects.filter(name=tag_name).exists())

    def test_unique_tag_constraint(self):
        # --- Arrange
        url = self.url("tag-list")

        # --- Act
        response = self.client.post(url, {"name": self.tag.name})

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_tag(self):
        # --- Arrange
        url = self.url("tag-detail", pk=self.tag.pk)
        new_name = "updated"

        # --- Act
        response = self.client.patch(url, {"name": new_name})
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["name"], new_name)

        self.tag.refresh_from_db()
        self.assertEqual(self.tag.name, new_name)

    def test_delete_tag(self):
        # --- Arrange
        url = self.url("tag-detail", pk=self.tag.pk)

        # --- Act
        response = self.client.delete(url)

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(pk=self.tag.pk).exists())
