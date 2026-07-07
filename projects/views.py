from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.permissions import IsStudent, IsSuperAdmin, IsSupervisor
from .serializers import ProjectFeedbackSerializer, TeamSerializer, ProjectSerializer

from accounts.permissions import IsStudent, IsSuperAdmin, IsSupervisor
from accounts.models import User

from .models import Team, Project, ProjectFeedback

from .serializers import (
    TeamSerializer,
    ProjectSerializer,
    AssignSupervisorSerializer,
    ProjectStatusUpdateSerializer,
)


class TeamListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        teams = Team.objects.filter(members=request.user).order_by("-id")
        serializer = TeamSerializer(teams, many=True)

        return Response({
            "success": True,
            "count": teams.count(),
            "data": serializer.data
        })

    def post(self, request):
        serializer = TeamSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Team created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class ProjectListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        projects = Project.objects.filter(
            team__members=request.user
        ).distinct().order_by("-id")

        serializer = ProjectSerializer(projects, many=True)

        return Response({
            "success": True,
            "count": projects.count(),
            "data": serializer.data
        })

    def post(self, request):
        serializer = ProjectSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Project submitted successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class ProjectDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({
                "success": False,
                "message": "Project not found."
            }, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        if user.role == "STUDENT" and not project.team.members.filter(id=user.id).exists():
            return Response({
                "success": False,
                "message": "You are not allowed to view this project."
            }, status=status.HTTP_403_FORBIDDEN)

        if user.role == "SUPERVISOR" and project.supervisor != user:
            return Response({
                "success": False,
                "message": "You are not assigned to this project."
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = ProjectSerializer(project)

        return Response({
            "success": True,
            "data": serializer.data
        })
    
class AdminProjectListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        projects = Project.objects.all().order_by("-id")
        serializer = ProjectSerializer(projects, many=True)

        return Response({
            "success": True,
            "count": projects.count(),
            "data": serializer.data
        })


class AssignSupervisorAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({
                "success": False,
                "message": "Project not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = AssignSupervisorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        supervisor = User.objects.get(
            id=serializer.validated_data["supervisor_id"],
            role="SUPERVISOR"
        )

        project.supervisor = supervisor
        project.status = "IN_PROGRESS"
        project.save()

        return Response({
            "success": True,
            "message": "Supervisor assigned successfully.",
            "data": ProjectSerializer(project).data
        })


class ProjectStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({
                "success": False,
                "message": "Project not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project.status = serializer.validated_data["status"]
        project.save()

        return Response({
            "success": True,
            "message": "Project status updated successfully.",
            "data": ProjectSerializer(project).data
        })
    

class SupervisorAssignedProjectListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def get(self, request):
        projects = Project.objects.filter(
            supervisor=request.user
        ).order_by("-id")

        serializer = ProjectSerializer(projects, many=True)

        return Response({
            "success": True,
            "count": projects.count(),
            "data": serializer.data
        })


class ProjectFeedbackCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def post(self, request, project_id):
        try:
            project = Project.objects.get(
                id=project_id,
                supervisor=request.user
            )
        except Project.DoesNotExist:
            return Response({
                "success": False,
                "message": "Project not found or not assigned to you."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ProjectFeedbackSerializer(
            data={
                "project": project.id,
                "comment": request.data.get("comment")
            },
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Feedback submitted successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class ProjectFeedbackListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, project_id):
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({
                "success": False,
                "message": "Project not found."
            }, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        allowed = False

        if user.role == "SUPER_ADMIN":
            allowed = True

        elif user.role == "SUPERVISOR" and project.supervisor == user:
            allowed = True

        elif user.role == "STUDENT" and project.team.members.filter(id=user.id).exists():
            allowed = True

        if not allowed:
            return Response({
                "success": False,
                "message": "You are not allowed to view feedback."
            }, status=status.HTTP_403_FORBIDDEN)

        feedbacks = project.feedbacks.all().order_by("-id")
        serializer = ProjectFeedbackSerializer(feedbacks, many=True)

        return Response({
            "success": True,
            "count": feedbacks.count(),
            "data": serializer.data
        })
    
