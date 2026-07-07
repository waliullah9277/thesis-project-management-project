from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path("", include("common.urls")),

    path("admin/", admin.site.urls),

    path("api/auth/", include("accounts.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/projects/", include("projects.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/viva/", include("viva.urls")),
    path("api/evaluation/", include("evaluation.urls")),
    path("api/training/", include("training.urls")),

]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)