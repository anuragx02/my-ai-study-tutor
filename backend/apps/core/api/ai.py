from django.urls import path

from apps.core.views import AskView

urlpatterns = [
    path("ask", AskView.as_view(), name="ai-ask"),
]
