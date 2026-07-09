from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.permissions import IsStudent, IsSuperAdmin, IsSupervisor
from .serializers import ProjectFeedbackSerializer, TeamSerializer, ProjectSerializer

from accounts.permissions import IsStudent, IsSuperAdmin, IsSupervisor
from accounts.models import User
from notifications.models import Notification

from .models import Team, Project, ProjectFeedback
from .models import Team, Project, ProjectFeedback, TeamMemberInfo
from .serializers import TeamSerializer, TeamMemberInfoSerializer, SupervisorProjectReviewSerializer

from .serializers import (
    TeamSerializer,
    ProjectSerializer,
    AssignSupervisorSerializer,
    ProjectStatusUpdateSerializer,
)

def create_notification(user, title, message):
    Notification.objects.create(
        user=user,
        title=title,
        message=message
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
        project = serializer.save()

        admins = User.objects.filter(role="SUPER_ADMIN")

        for admin in admins:
            create_notification(
                admin,
                "New Project Submitted",
                f'{request.user.first_name} submitted a new project: "{project.title}".'
            )
        

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
        project.status = "SUPERVISOR_ASSIGNED"
        project.save(update_fields=["supervisor", "status"])

        create_notification(
        supervisor,
        "New Project Assigned",
        f'Project "{project.title}" has been assigned to you.'
)

        for student in project.team.members.all():
            create_notification(
                student,
                "Supervisor Assigned",
                f'{supervisor.first_name} {supervisor.last_name} has been assigned to your project "{project.title}".'
            )

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

        for student in project.team.members.all():
            create_notification(
            student,
            "Project Status Updated",
            f'Your project "{project.title}" status is now {project.status}.'
        )

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
        feedback = serializer.save()

        for student in project.team.members.all():
            create_notification(
                student,
                "New Project Feedback",
                f'Supervisor added feedback on your project "{project.title}".'
            )

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
    

class TeamMemberUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def patch(self, request, team_id):
        try:
            team = Team.objects.get(id=team_id, leader=request.user)
        except Team.DoesNotExist:
            return Response({
                "success": False,
                "message": "Team not found or you are not the team leader."
            }, status=status.HTTP_404_NOT_FOUND)

        member_ids = request.data.get("members", [])

        if not isinstance(member_ids, list):
            return Response({
                "success": False,
                "message": "Members must be a list."
            }, status=status.HTTP_400_BAD_REQUEST)

        member_ids = [int(member_id) for member_id in member_ids]

        if request.user.id not in member_ids:
            member_ids.insert(0, request.user.id)

        if len(member_ids) < 1:
            return Response({
                "success": False,
                "message": "Minimum 1 member is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(member_ids) > team.member_count:
            return Response({
                "success": False,
                "message": f"This team allows maximum {team.member_count} member(s)."
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(member_ids) > 3:
            return Response({
                "success": False,
                "message": "Maximum 3 members are allowed."
            }, status=status.HTTP_400_BAD_REQUEST)

        members = User.objects.filter(
            id__in=member_ids,
            role="STUDENT",
            is_active=True
        )

        if members.count() != len(member_ids):
            return Response({
                "success": False,
                "message": "Invalid or inactive student selected."
            }, status=status.HTTP_400_BAD_REQUEST)

        team.members.set(members)

        return Response({
            "success": True,
            "message": "Team members updated successfully.",
            "data": TeamSerializer(team).data
        })
    


class TeamUpdateDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def put(self, request, team_id):
        try:
            team = Team.objects.get(id=team_id, leader=request.user)
        except Team.DoesNotExist:
            return Response({
                "success": False,
                "message": "Team not found or you are not the team leader."
            }, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name")
        member_count = request.data.get("member_count")

        if name:
            team.name = name

        if member_count:
            member_count = int(member_count)

            if member_count < 1 or member_count > 3:
                return Response({
                    "success": False,
                    "message": "Member count must be between 1 and 3."
                }, status=status.HTTP_400_BAD_REQUEST)

            if team.member_infos.count() > member_count:
                return Response({
                    "success": False,
                    "message": "Remove extra members before reducing member count."
                }, status=status.HTTP_400_BAD_REQUEST)

            team.member_count = member_count

        team.save()

        return Response({
            "success": True,
            "message": "Team updated successfully.",
            "data": TeamSerializer(team).data
        })

    def delete(self, request, team_id):
        try:
            team = Team.objects.get(id=team_id, leader=request.user)
        except Team.DoesNotExist:
            return Response({
                "success": False,
                "message": "Team not found or you are not the team leader."
            }, status=status.HTTP_404_NOT_FOUND)

        team.delete()

        return Response({
            "success": True,
            "message": "Team deleted successfully."
        })
    

class TeamMemberInfoCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def post(self, request, team_id):
        try:
            team = Team.objects.get(id=team_id, leader=request.user)
        except Team.DoesNotExist:
            return Response({
                "success": False,
                "message": "Team not found or you are not the team leader."
            }, status=status.HTTP_404_NOT_FOUND)

        if team.member_infos.count() >= team.member_count:
            return Response({
                "success": False,
                "message": f"Maximum {team.member_count} member(s) allowed."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = TeamMemberInfoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(team=team)

        return Response({
            "success": True,
            "message": "Member added successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    
class TeamMemberInfoUpdateDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def put(self, request, member_id):
        try:
            member = TeamMemberInfo.objects.get(
                id=member_id,
                team__leader=request.user
            )
        except TeamMemberInfo.DoesNotExist:
            return Response({
                "success": False,
                "message": "Member not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TeamMemberInfoSerializer(
            member,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Member updated successfully.",
            "data": serializer.data
        })

    def delete(self, request, member_id):
        try:
            member = TeamMemberInfo.objects.get(
                id=member_id,
                team__leader=request.user
            )
        except TeamMemberInfo.DoesNotExist:
            return Response({
                "success": False,
                "message": "Member not found."
            }, status=status.HTTP_404_NOT_FOUND)

        member.delete()

        return Response({
            "success": True,
            "message": "Member deleted successfully."
        })



class SupervisorProjectReviewAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def patch(self, request, project_id):
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

        serializer = SupervisorProjectReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        comment = serializer.validated_data.get("comment", "")

        project.status = new_status
        project.save(update_fields=["status"])

        if comment:
            ProjectFeedback.objects.create(
                project=project,
                supervisor=request.user,
                comment=comment
            )

        for student in project.team.members.all():
            create_notification(
                student,
                "Project Status Updated",
                f'Your project "{project.title}" status is now {new_status}.'
            )

        return Response({
            "success": True,
            "message": "Project status updated successfully.",
            "data": ProjectSerializer(project).data
        })





