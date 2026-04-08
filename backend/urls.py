from django.contrib import admin
from django.urls import include, path, re_path
from django.http import JsonResponse
from django.views.generic import TemplateView


def health_check(request):
    return JsonResponse({"status": "ok"})


spa_index = TemplateView.as_view(template_name="index.html")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check),
    path("api/", include("backend.apps.core.urls")),
    path("", spa_index, name="spa-root"),
    re_path(r"^(?!api/|admin/|static/).*$", spa_index, name="spa-fallback"),
]