from django.urls import path

from backend.apps.core.views import ProgressView, HistoryDeleteView

urlpatterns = [
    path("progress", ProgressView.as_view(), name="progress"),
    path("history", HistoryDeleteView.as_view(), name="history-delete"),
]
