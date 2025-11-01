from django.db.models.query import QuerySet
from rest_framework import permissions, viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from document.models import Document, DocumentFile, DocumentNote, Tag
from document.serializers import (
    DocumentFileSerializer,
    DocumentNoteSerializer,
    DocumentSerializer,
    TagSerializer,
)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Document]:
        return Document.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DocumentFileViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self) -> QuerySet[DocumentFile]:
        return DocumentFile.objects.filter(document__owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            uploaded_by=self.request.user, document_id=self.kwargs["document_pk"]
        )


class DocumentNoteViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[DocumentNote]:
        return DocumentNote.objects.filter(document__owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user, document_id=self.kwargs["document_pk"]
        )
