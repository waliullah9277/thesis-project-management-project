from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.models import User
from accounts.permissions import IsSuperAdmin, IsStudent, IsSupervisor, IsExaminer
from projects.models import Project
from reports.models import ProgressReport
from viva.models import VivaSchedule
from evaluation.models import Evaluation
from training.models import IndustrialTraining
from notifications.models import Notice, Notification


class AdminDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        return Response({
            "success": True,
            "dashboard": "SUPER_ADMIN",
            "data": {
                "total_users": User.objects.count(),
                "total_students": User.objects.filter(role="STUDENT").count(),
                "total_supervisors": User.objects.filter(role="SUPERVISOR").count(),
                "total_examiners": User.objects.filter(role="EXAMINER").count(),
                "total_projects": Project.objects.count(),
                "pending_projects": Project.objects.filter(status="PENDING").count(),
                "approved_projects": Project.objects.filter(status="APPROVED").count(),
                "total_viva": VivaSchedule.objects.count(),
                "total_evaluations": Evaluation.objects.count(),
                "total_training": IndustrialTraining.objects.count(),
                "total_notices": Notice.objects.count(),
            }
        })


class StudentDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        return Response({
            "success": True,
            "dashboard": "STUDENT",
            "data": {
                "my_projects": Project.objects.filter(team__members=request.user).distinct().count(),
                "my_reports": ProgressReport.objects.filter(submitted_by=request.user).count(),
                "my_viva": VivaSchedule.objects.filter(project__team__members=request.user).distinct().count(),
                "my_results": Evaluation.objects.filter(
                    project__team__members=request.user,
                    published=True
                ).distinct().count(),
                "my_training": IndustrialTraining.objects.filter(student=request.user).count(),
                "unread_notifications": Notification.objects.filter(
                    user=request.user,
                    is_read=False
                ).count(),
            }
        })


class SupervisorDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def get(self, request):
        return Response({
            "success": True,
            "dashboard": "SUPERVISOR",
            "data": {
                "assigned_projects": Project.objects.filter(supervisor=request.user).count(),
                "pending_reports": ProgressReport.objects.filter(
                    project__supervisor=request.user,
                    status="SUBMITTED"
                ).count(),
                "reviewed_reports": ProgressReport.objects.filter(
                    project__supervisor=request.user,
                    status="REVIEWED"
                ).count(),
                "assigned_training": IndustrialTraining.objects.filter(supervisor=request.user).count(),
                "unread_notifications": Notification.objects.filter(
                    user=request.user,
                    is_read=False
                ).count(),
            }
        })


class ExaminerDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsExaminer]

    def get(self, request):
        return Response({
            "success": True,
            "dashboard": "EXAMINER",
            "data": {
                "assigned_viva": VivaSchedule.objects.filter(examiner=request.user).count(),
                "completed_viva": VivaSchedule.objects.filter(
                    examiner=request.user,
                    status="COMPLETED"
                ).count(),
                "my_evaluations": Evaluation.objects.filter(examiner=request.user).count(),
                "unread_notifications": Notification.objects.filter(
                    user=request.user,
                    is_read=False
                ).count(),
            }
        })