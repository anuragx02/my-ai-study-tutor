from django.urls import path

from backend.apps.core.views import CourseListCreateView, TopicListCreateView

urlpatterns = [
    path("", CourseListCreateView.as_view(), name="course-list-create"),
    path("topics", TopicListCreateView.as_view(), name="topic-list-create"),
]
