from django.urls import path

from .views import (
    SupervisorProjectReviewAPIView,
    TeamListCreateAPIView,
    ProjectListCreateAPIView,
    ProjectDetailAPIView,
    AdminProjectListAPIView,
    AssignSupervisorAPIView,
    SupervisorAssignedProjectListAPIView,
    ProjectFeedbackCreateAPIView,
    ProjectFeedbackListAPIView,
    TeamUpdateDeleteAPIView,
    TeamMemberInfoCreateAPIView,
    TeamMemberInfoUpdateDeleteAPIView,
)

urlpatterns = [
    path("teams/", TeamListCreateAPIView.as_view(), name="team-list-create"),
    path("", ProjectListCreateAPIView.as_view(), name="project-list-create"),
    path("<int:project_id>/", ProjectDetailAPIView.as_view(), name="project-detail"),

    path("admin/list/", AdminProjectListAPIView.as_view(), name="admin-project-list"),
    path("<int:project_id>/assign-supervisor/", AssignSupervisorAPIView.as_view(), name="assign-supervisor"),

    path("supervisor/assigned/", SupervisorAssignedProjectListAPIView.as_view(), name="supervisor-assigned-projects"),
    path("supervisor/review/<int:project_id>/", SupervisorProjectReviewAPIView.as_view(), name="supervisor-project-review"),

    path("<int:project_id>/feedback/", ProjectFeedbackCreateAPIView.as_view(), name="project-feedback-create"),
    path("<int:project_id>/feedbacks/", ProjectFeedbackListAPIView.as_view(), name="project-feedback-list"),

    path("teams/<int:team_id>/update-delete/", TeamUpdateDeleteAPIView.as_view()),
    path("teams/<int:team_id>/members/add/", TeamMemberInfoCreateAPIView.as_view()),
    path("teams/members/<int:member_id>/update-delete/", TeamMemberInfoUpdateDeleteAPIView.as_view()),
]