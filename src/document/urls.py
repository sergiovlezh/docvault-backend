from django.urls import include, path
from rest_framework.routers import DefaultRouter

from document.views import (
    DocumentFileViewSet,
    DocumentNoteViewSet,
    DocumentViewSet,
    TagViewSet,
)

# Main router for documents and tags
router = DefaultRouter()
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"tags", TagViewSet, basename="tag")

# Direct URL patterns for nested resources
urlpatterns = [
    path("", include(router.urls)),
    # Document files endpoints
    path(
        "documents/<int:document_pk>/files/",
        DocumentFileViewSet.as_view({"get": "list", "post": "create"}),
        name="document-files-list",
    ),
    path(
        "documents/<int:document_pk>/files/<uuid:pk>/",
        DocumentFileViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="document-files-detail",
    ),
    # Document notes endpoints
    path(
        "documents/<int:document_pk>/notes/",
        DocumentNoteViewSet.as_view({"get": "list", "post": "create"}),
        name="document-notes-list",
    ),
    path(
        "documents/<int:document_pk>/notes/<int:pk>/",
        DocumentNoteViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="document-notes-detail",
    ),
]
