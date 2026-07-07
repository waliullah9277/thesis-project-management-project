from django.urls import path

from .views import (
    CompanyListCreateAPIView,
    StudentTrainingListCreateAPIView,
    AdminTrainingListAPIView,
    AssignTrainingSupervisorAPIView,
    TrainingStatusUpdateAPIView,
    SupervisorTrainingListAPIView,
    TrainingFeedbackAPIView,
)


urlpatterns = [
    path("companies/", CompanyListCreateAPIView.as_view(), name="company-list-create"),

    path("student/", StudentTrainingListCreateAPIView.as_view(), name="student-training-list-create"),
    path("admin/", AdminTrainingListAPIView.as_view(), name="admin-training-list"),

    path("<int:training_id>/assign-supervisor/", AssignTrainingSupervisorAPIView.as_view(), name="assign-training-supervisor"),
    path("<int:training_id>/status/", TrainingStatusUpdateAPIView.as_view(), name="training-status-update"),

    path("supervisor/", SupervisorTrainingListAPIView.as_view(), name="supervisor-training-list"),
    path("<int:training_id>/feedback/", TrainingFeedbackAPIView.as_view(), name="training-feedback"),
]