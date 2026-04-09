from django.urls import include, path

urlpatterns = [
    path("auth/", include("backend.apps.core.api.auth")),
    path("knowledge/", include("backend.apps.core.api.knowledge")),
    path("courses/", include("backend.apps.core.api.courses")),
    path("materials/", include("backend.apps.core.api.materials")),
    path("quiz/", include("backend.apps.core.api.quiz")),
    path("ai/", include("backend.apps.core.api.ai")),
    path("analytics/", include("backend.apps.core.api.analytics")),
    path("recommendations/", include("backend.apps.core.api.recommendations")),
]
