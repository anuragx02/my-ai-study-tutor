from django.urls import path

from backend.apps.core.views import ProgressView

urlpatterns = [
    path("progress", ProgressView.as_view(), name="progress"),
]
