from django.urls import path

from .views import (
    VivaScheduleListCreateAPIView,
    AssignExaminerAPIView,
    ExaminerAssignedVivaAPIView,
    VivaStatusUpdateAPIView,
)


urlpatterns = [
    path("", VivaScheduleListCreateAPIView.as_view(), name="viva-list-create"),
    path("<int:viva_id>/assign-examiner/", AssignExaminerAPIView.as_view(), name="assign-examiner"),
    path("examiner/assigned/", ExaminerAssignedVivaAPIView.as_view(), name="examiner-assigned-viva"),
    path("<int:viva_id>/status/", VivaStatusUpdateAPIView.as_view(), name="viva-status-update"),
]