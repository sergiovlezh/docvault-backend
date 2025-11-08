from django.db.models.query import QuerySet
from django.shortcuts import get_object_or_404
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
        return (
            Document.objects.filter(owner=self.request.user)
            .prefetch_related("tags", "files")
            .select_related("owner")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DocumentFileViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self) -> QuerySet[DocumentFile]:
        return DocumentFile.objects.filter(document__owner=self.request.user)

    def perform_create(self, serializer):
        document = get_object_or_404(
            Document, pk=self.kwargs["document_pk"], owner=self.request.user
        )
        serializer.save(uploaded_by=self.request.user, document=document)


class DocumentNoteViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[DocumentNote]:
        return DocumentNote.objects.filter(document__owner=self.request.user)

    def perform_create(self, serializer):
        document = get_object_or_404(
            Document, pk=self.kwargs["document_pk"], owner=self.request.user
        )
        serializer.save(created_by=self.request.user, document=document)
