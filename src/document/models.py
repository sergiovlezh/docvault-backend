import uuid
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models

User = get_user_model()


def document_file_path(instance: "DocumentFile", filename: str) -> str:
    """Return a storage-relative path for the uploaded file.

    Format: documents/<user_id>/<uuid><ext>
    Keep it relative so Django storage backends handle the absolute path/URL.
    If the filename has no extension, an empty string is used for <ext>.

    Args:
        instance (DocumentFile): The DocumentFile instance.
        filename (str): The original filename.

    Returns:
        str: The constructed file path.
    """
    user_id: int = instance.owner.pk
    file_id: uuid.UUID = instance.id or uuid.uuid4()
    ext: str = Path(filename).suffix.lower() or ""

    return f"documents/{user_id}/{file_id}{ext}"


class Tag(models.Model):
    """Simple tag model to categorize documents.

    Tags are canonical (global) and can be used by many users in many documents.
    The "property" of a tag is handled in DocumentTag through a ManyToManyField.
    """

    name = models.CharField(max_length=250, unique=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Document(models.Model):
    """A single logical document."""

    title = models.CharField(max_length=500, db_index=True)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    tags = models.ManyToManyField(Tag, through="DocumentTag", related_name="documents")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title

    def add_tag(self, tag: Tag, added_by: AbstractUser) -> None:
        DocumentTag.objects.create(document=self, tag=tag, added_by=added_by)


class DocumentFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="files"
    )
    file = models.FileField(upload_to=document_file_path, max_length=1024)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="uploaded_files"
    )

    @property
    def owner(self) -> AbstractUser:
        return self.document.owner

    def __str__(self):
        return self.document.title


class DocumentTag(models.Model):
    """Through model for Document and Tag ManyToMany relationship."""

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="document_tags"
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="document_tags")
    added_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="added_tags"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "tag"], name="unique_document_tag"
            )
        ]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.document.title} - {self.tag.name}"


class DocumentNote(models.Model):
    """Simple note model for user-generated content."""

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="notes"
    )
    content = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        content_preview = (
            f"{self.content[:30]}..." if len(self.content) > 30 else self.content
        )

        return content_preview
