from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from django.shortcuts import redirect


def health_check(request):
    return JsonResponse({"status": "ok"})


def service_root(request):
    return redirect('/static/index.html')


urlpatterns = [
    path("", service_root, name="service-root"),
    path("admin/", admin.site.urls),
    path("api/health/", health_check),
    path("api/", include("backend.apps.core.urls")),
]