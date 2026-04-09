from django.urls import path

from backend.apps.core.views import (
    KnowledgeDocumentDetailView,
    KnowledgeDocumentListCreateView,
    KnowledgeDocumentPurgeView,
)

urlpatterns = [
    path("documents", KnowledgeDocumentListCreateView.as_view(), name="knowledge-documents"),
    path("documents/<int:document_id>", KnowledgeDocumentDetailView.as_view(), name="knowledge-document-detail"),
    path("documents/purge", KnowledgeDocumentPurgeView.as_view(), name="knowledge-documents-purge"),
]
