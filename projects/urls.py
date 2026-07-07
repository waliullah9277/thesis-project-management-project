from django.urls import path

from .views import (
    TeamListCreateAPIView,
    ProjectListCreateAPIView,
    ProjectDetailAPIView,
)


urlpatterns = [
    path("teams/", TeamListCreateAPIView.as_view(), name="team-list-create"),
    path("", ProjectListCreateAPIView.as_view(), name="project-list-create"),
    path("<int:project_id>/", ProjectDetailAPIView.as_view(), name="project-detail"),
]