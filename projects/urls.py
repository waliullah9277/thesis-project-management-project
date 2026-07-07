from django.urls import path

from .views import (
    TeamListCreateAPIView,
    ProjectListCreateAPIView,
    ProjectDetailAPIView,
    AdminProjectListAPIView,
    AssignSupervisorAPIView,
    ProjectStatusUpdateAPIView,
    SupervisorAssignedProjectListAPIView,
    ProjectFeedbackCreateAPIView,
    ProjectFeedbackListAPIView,
)


urlpatterns = [
    
    path("teams/", TeamListCreateAPIView.as_view(), name="team-list-create"),
    path("", ProjectListCreateAPIView.as_view(), name="project-list-create"),
    path("<int:project_id>/", ProjectDetailAPIView.as_view(), name="project-detail"),
    path("admin/list/", AdminProjectListAPIView.as_view(), name="admin-project-list"),
    path("<int:project_id>/assign-supervisor/", AssignSupervisorAPIView.as_view(), name="assign-supervisor"),
    path("<int:project_id>/status/", ProjectStatusUpdateAPIView.as_view(), name="project-status-update"),
    path("supervisor/assigned/", SupervisorAssignedProjectListAPIView.as_view(), name="supervisor-assigned-projects"),
    path("<int:project_id>/feedback/", ProjectFeedbackCreateAPIView.as_view(), name="project-feedback-create"),
    path("<int:project_id>/feedbacks/", ProjectFeedbackListAPIView.as_view(), name="project-feedback-list"),


]