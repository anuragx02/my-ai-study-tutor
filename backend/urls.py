from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({"status": "ok"})


def service_root(request):
    return JsonResponse(
        {
            "service": "ai-study-tutor",
            "status": "ok",
            "health": "/api/health/",
            "api": "/api/",
        }
    )


urlpatterns = [
    path("", service_root, name="service-root"),
    path("admin/", admin.site.urls),
    path("api/health/", health_check),
    path("api/", include("backend.apps.core.urls")),
]