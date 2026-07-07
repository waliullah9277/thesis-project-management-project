from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.permissions import IsStudent, IsSupervisor
from projects.models import Project
from .models import ProgressReport
from .serializers import (
    ProgressReportSerializer,
    ProgressReportReviewSerializer,
)


class ProgressReportListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        reports = ProgressReport.objects.filter(
            submitted_by=request.user
        ).order_by("-id")

        serializer = ProgressReportSerializer(reports, many=True)

        return Response({
            "success": True,
            "count": reports.count(),
            "data": serializer.data
        })

    def post(self, request):
        project_id = request.data.get("project")

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({
                "success": False,
                "message": "Project not found."
            }, status=status.HTTP_404_NOT_FOUND)

        if not project.team.members.filter(id=request.user.id).exists():
            return Response({
                "success": False,
                "message": "You are not allowed to submit report for this project."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ProgressReportSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Progress report submitted successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class SupervisorProgressReportListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def get(self, request):
        reports = ProgressReport.objects.filter(
            project__supervisor=request.user
        ).order_by("-id")

        serializer = ProgressReportSerializer(reports, many=True)

        return Response({
            "success": True,
            "count": reports.count(),
            "data": serializer.data
        })


class ProgressReportReviewAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def patch(self, request, report_id):
        try:
            report = ProgressReport.objects.get(
                id=report_id,
                project__supervisor=request.user
            )
        except ProgressReport.DoesNotExist:
            return Response({
                "success": False,
                "message": "Report not found or not assigned to you."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ProgressReportReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report.status = serializer.validated_data["status"]
        report.supervisor_comment = serializer.validated_data["supervisor_comment"]
        report.reviewed_at = timezone.now()
        report.save()

        return Response({
            "success": True,
            "message": "Progress report reviewed successfully.",
            "data": ProgressReportSerializer(report).data
        })