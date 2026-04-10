from django.urls import path

from backend.apps.core.views import (
    KnowledgeBaseDetailView,
    KnowledgeBaseListCreateView,
    KnowledgeBasePurgeView,
)

urlpatterns = [
    path("documents", KnowledgeBaseListCreateView.as_view(), name="knowledge-documents"),
    path("documents/<int:document_id>", KnowledgeBaseDetailView.as_view(), name="knowledge-document-detail"),
    path("documents/purge", KnowledgeBasePurgeView.as_view(), name="knowledge-documents-purge"),
]
