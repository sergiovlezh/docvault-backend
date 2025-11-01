from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from tempfile import NamedTemporaryFile
import os

User = get_user_model()


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
