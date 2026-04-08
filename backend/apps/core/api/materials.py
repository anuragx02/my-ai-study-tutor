from django.urls import path

from backend.apps.core.views import StudyMaterialListCreateView

urlpatterns = [
    path("", StudyMaterialListCreateView.as_view(), name="study-material-list-create"),
]
