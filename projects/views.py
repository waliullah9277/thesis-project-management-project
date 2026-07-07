from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.permissions import IsStudent, IsSuperAdmin, IsSupervisor
from .models import Team, Project
from .serializers import TeamSerializer, ProjectSerializer


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