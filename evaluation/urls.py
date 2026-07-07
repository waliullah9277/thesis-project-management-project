from django.urls import path

from .views import (
    EvaluationCreateAPIView,
    ExaminerEvaluationListAPIView,
    AdminEvaluationListAPIView,
    PublishResultAPIView,
    StudentResultAPIView,
)


urlpatterns = [
    path("", EvaluationCreateAPIView.as_view(), name="evaluation-create"),
    path("examiner/", ExaminerEvaluationListAPIView.as_view(), name="examiner-evaluation-list"),
    path("admin/", AdminEvaluationListAPIView.as_view(), name="admin-evaluation-list"),
    path("<int:evaluation_id>/publish/", PublishResultAPIView.as_view(), name="publish-result"),
    path("student/result/", StudentResultAPIView.as_view(), name="student-result"),
]