from django.urls import path

from backend.apps.core.views import AskView, ChatSessionDetailView, ChatSessionListView

urlpatterns = [
    path("ask", AskView.as_view(), name="ai-ask"),
    path("sessions", ChatSessionListView.as_view(), name="ai-session-list"),
    path("sessions/<int:session_id>", ChatSessionDetailView.as_view(), name="ai-session-detail"),
]
