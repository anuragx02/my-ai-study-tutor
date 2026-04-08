from django.urls import path

from backend.apps.core.views import QuizGenerateView, QuizListView, QuizSubmitView

urlpatterns = [
    path("generate", QuizGenerateView.as_view(), name="quiz-generate"),
    path("submit", QuizSubmitView.as_view(), name="quiz-submit"),
    path("", QuizListView.as_view(), name="quiz-list"),
]
