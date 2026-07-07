from django.urls import path

from .views import (
    StudentDashboardAPIView,
    SupervisorDashboardAPIView,
    ExaminerDashboardAPIView,
    AdminDashboardAPIView,
)


urlpatterns = [
    path("student/", StudentDashboardAPIView.as_view(), name="student-dashboard"),
    path("supervisor/", SupervisorDashboardAPIView.as_view(), name="supervisor-dashboard"),
    path("examiner/", ExaminerDashboardAPIView.as_view(), name="examiner-dashboard"),
    path("admin/", AdminDashboardAPIView.as_view(), name="admin-dashboard"),
]