from django.urls import include, path

urlpatterns = [
    path("auth/", include("apps.core.api.auth")),
    path("courses/", include("apps.core.api.courses")),
    path("materials/", include("apps.core.api.materials")),
    path("quiz/", include("apps.core.api.quiz")),
    path("ai/", include("apps.core.api.ai")),
    path("analytics/", include("apps.core.api.analytics")),
    path("recommendations/", include("apps.core.api.recommendations")),
]
