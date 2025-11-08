import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from document.models import Document, DocumentFile, DocumentNote, Tag

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


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


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class DocumentFileViewSetTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        self.document = Document.objects.create(
            title="Sample Doc",
            owner=self.user,
        )

    def tearDown(self):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

        super().tearDown()

    def test_upload_file(self):
        # --- Arrange
        url = self.url("document-files-list", document_pk=self.document.pk)
        uploaded_file = SimpleUploadedFile(
            "test.pdf", b"%PDF-1.4 content", content_type="application/pdf"
        )

        # --- Act
        response = self.client.post(url, {"file": uploaded_file}, format="multipart")
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DocumentFile.objects.filter(document=self.document).exists())

        # self.assertTrue(self.document.files.filter(id=data["id"]).exists())
        self.assertTrue(
            DocumentFile.objects.filter(document=self.document, id=data["id"]).exists()
        )

    def test_list_files(self):
        # --- Arrange
        DocumentFile.objects.create(
            document=self.document, uploaded_by=self.user, file="dummy.pdf"
        )

        url = self.url("document-files-list", document_pk=self.document.pk)

        # --- Act
        response = self.client.get(url)
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)

    def test_upload_denied_for_foreign_document(self):
        # --- Arrange
        other_doc = Document.objects.create(title="Foreign", owner=self.other_user)

        url = self.url("document-files-list", document_pk=other_doc.pk)

        uploaded_file = SimpleUploadedFile("x.pdf", b"blocked")

        # --- Act
        response = self.client.post(url, {"file": uploaded_file}, format="multipart")

        # --- Assert
        self.assertIn(
            response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )
        self.assertFalse(DocumentFile.objects.filter(document=other_doc).exists())


class DocumentNoteViewSetTests(BaseAPITestCase):
    def setUp(self):
        super().setUp()

        self.document = Document.objects.create(
            title="Sample Note Doc",
            owner=self.user,
        )

    def test_create_note(self):
        # --- Arrange
        url = self.url("document-notes-list", document_pk=self.document.pk)
        content = "Remember to review this."

        # --- Act
        response = self.client.post(url, {"content": content})
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data["content"], content)
        self.assertTrue(DocumentNote.objects.filter(document=self.document).exists())

    def test_list_notes(self):
        # --- Arrange
        DocumentNote.objects.create(
            document=self.document, created_by=self.user, content="Note 1"
        )

        url = self.url("document-notes-list", document_pk=self.document.pk)

        # --- Act
        response = self.client.get(url)
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), 1)

    def test_update_note(self):
        # --- Arrange
        note = DocumentNote.objects.create(
            document=self.document, created_by=self.user, content="Old text"
        )

        url = self.url(
            "document-notes-detail", document_pk=self.document.pk, pk=note.pk
        )

        new_content = "Updated text"

        # --- Act
        response = self.client.patch(url, {"content": new_content})
        data = response.json()

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["content"], new_content)

        note.refresh_from_db()
        self.assertEqual(note.content, new_content)

    def test_delete_note(self):
        # --- Arrange
        note = DocumentNote.objects.create(
            document=self.document, created_by=self.user, content="To delete"
        )

        url = self.url(
            "document-notes-detail", document_pk=self.document.pk, pk=note.pk
        )

        # --- Act
        response = self.client.delete(url)

        # --- Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(DocumentNote.objects.filter(pk=note.pk).exists())

    def test_note_access_denied_for_foreign_document(self):
        # --- Arrange
        other_doc = Document.objects.create(title="Private", owner=self.other_user)

        url = self.url("document-notes-list", document_pk=other_doc.pk)

        content = "Unauthorized note"

        # --- Act
        response = self.client.post(url, {"content": content})

        # --- Assert
        self.assertIn(
            response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]
        )
        self.assertFalse(DocumentNote.objects.filter(document=other_doc).exists())
