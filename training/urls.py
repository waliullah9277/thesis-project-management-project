from django.urls import path

from .views import (
    AdminTrainingListAPIView,
    AssignTrainingSupervisorAPIView,
    CompanyDetailAPIView,
    CompanyListCreateAPIView,
    StudentTrainingDetailAPIView,
    StudentTrainingListCreateAPIView,
    SupervisorTrainingListAPIView,
    TrainingFeedbackAPIView,
    TrainingStatusUpdateAPIView,
)


urlpatterns = [
    path(
        "companies/",
        CompanyListCreateAPIView.as_view(),
        name="company-list-create",
    ),

    path(
        "companies/<int:company_id>/",
        CompanyDetailAPIView.as_view(),
        name="company-detail",
    ),

    path(
        "student/",
        StudentTrainingListCreateAPIView.as_view(),
        name="student-training-list-create",
    ),

    path(
        "student/<int:training_id>/",
        StudentTrainingDetailAPIView.as_view(),
        name="student-training-detail",
    ),

    path(
        "admin/",
        AdminTrainingListAPIView.as_view(),
        name="admin-training-list",
    ),

    path(
        "<int:training_id>/assign-supervisor/",
        AssignTrainingSupervisorAPIView.as_view(),
        name="assign-training-supervisor",
    ),

    path(
        "<int:training_id>/status/",
        TrainingStatusUpdateAPIView.as_view(),
        name="training-status-update",
    ),

    path(
        "supervisor/",
        SupervisorTrainingListAPIView.as_view(),
        name="supervisor-training-list",
    ),

    path(
        "<int:training_id>/feedback/",
        TrainingFeedbackAPIView.as_view(),
        name="training-feedback",
    ),
]