from django.urls import path

from .views import (
    ProgressReportListCreateAPIView,
    SupervisorProgressReportListAPIView,
    ProgressReportReviewAPIView,
)


urlpatterns = [
    path("", ProgressReportListCreateAPIView.as_view(), name="progress-report-list-create"),
    path("supervisor/", SupervisorProgressReportListAPIView.as_view(), name="supervisor-progress-reports"),
    path("<int:report_id>/review/", ProgressReportReviewAPIView.as_view(), name="progress-report-review"),
]