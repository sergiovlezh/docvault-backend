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


class DocumentAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="pass")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _json_or_results(self, resp):
        j = resp.json()
        return j.get("results", j)

    def test_documents_and_nested_endpoints(self):
        # documents list (empty)
        resp = self.client.get(reverse("document-list"))
        assert resp.status_code == 200

        data = resp.json()
        assert data == []

        # create document
        resp = self.client.post(
            reverse("document-list"), {"title": "Doc A"}, format="json"
        )
        assert resp.status_code == 201
        doc_id = resp.json()["id"]

        # files list (empty)
        files_url = reverse("document-files-list", kwargs={"document_pk": doc_id})
        resp = self.client.get(files_url)
        assert resp.status_code == 200
        data = resp.json()
        assert data == []

        # upload a file using a real temporary file on disk and remove it afterwards

        with NamedTemporaryFile(suffix=".txt", delete=True) as tmp:
            tmp.write(b"hello")
            tmp.flush()
            with open(tmp.name, "rb") as fh:
                f = SimpleUploadedFile(os.path.basename(tmp.name), fh.read(), content_type="text/plain")
                resp = self.client.post(files_url, {"file": f}, format="multipart")
            assert resp.status_code == 201
            file_id = resp.json()["id"]

        # retrieve the uploaded file
        resp = self.client.get(
            reverse(
                "document-files-detail", kwargs={"document_pk": doc_id, "pk": file_id}
            )
        )
        assert resp.status_code == 200

        # notes create + list
        notes_url = reverse("document-notes-list", kwargs={"document_pk": doc_id})
        resp = self.client.post(notes_url, {"content": "note1"}, format="json")
        assert resp.status_code == 201
        resp = self.client.get(notes_url)
        assert resp.status_code == 200

        # tags
        resp = self.client.post(reverse("tag-list"), {"name": "tag1"}, format="json")
        assert resp.status_code == 201
