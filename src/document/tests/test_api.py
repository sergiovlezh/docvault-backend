from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from document.models import Document, Tag

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


class DocumentViewSetTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.tag = Tag.objects.create(name="finance")
        self.document = Document.objects.create(
            title="Invoice 2025", description="Tax related", owner=self.user
        )
        self.document.add_tag(self.tag, added_by=self.user)

    def test_list_documents(self):
        # --- Arrange
        url = self.url("document-list")

        # --- Act
        response = self.client.get(url)
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.document.title, [document["title"] for document in data])

    def test_create_document(self):
        # --- Arrange
        url = self.url("document-list")

        title = "New Document"
        description = "My first doc"

        # --- Act
        response = self.client.post(url, {"title": title, "description": description})
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data["title"], title)
        self.assertTrue(Document.objects.filter(title=title, owner=self.user).exists())

    def test_document_visibility_limited_to_owner(self):
        # --- Arrange
        other_document = Document.objects.create(title="Hidden", owner=self.other_user)

        url = self.url("document-list")

        # --- Act
        response = self.client.get(url)
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [document["title"] for document in data]
        self.assertNotIn(other_document.title, titles)

    def test_update_document(self):
        # --- Arrange
        url = self.url("document-detail", pk=self.document.pk)

        new_title = "Updated Title"

        # --- Act
        response = self.client.patch(url, {"title": new_title})
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["title"], new_title)

        self.document.refresh_from_db()
        self.assertEqual(self.document.title, new_title)

    def test_delete_document(self):
        # --- Arrange
        url = self.url("document-detail", pk=self.document.pk)

        # --- Act
        response = self.client.delete(url)

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(pk=self.document.pk).exists())
