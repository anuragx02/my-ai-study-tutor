from django.urls import path

from apps.core.views import RecommendationView

urlpatterns = [
    path("", RecommendationView.as_view(), name="recommendations"),
]
