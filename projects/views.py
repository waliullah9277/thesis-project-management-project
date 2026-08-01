from django.db import transaction
from django.db.models import F
from django.http import FileResponse

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import (
    IsStudent,
    IsSuperAdmin,
    IsSupervisor,
)
from notifications.models import Notification

from .models import (
    Project,
    ProjectDocument,
    ProjectFeedback,
    Team,
    TeamMemberInfo,
)
from .serializers import (
    AssignSupervisorSerializer,
    ProjectDocumentReviewSerializer,
    ProjectDocumentSerializer,
    ProjectFeedbackSerializer,
    ProjectSerializer,
    ProjectStatusUpdateSerializer,
    SupervisorProjectReviewSerializer,
    TeamMemberInfoSerializer,
    TeamSerializer,
)


# =========================================================
# COMMON HELPERS
# =========================================================


def create_notification(user, title, message):
    """
    Create a notification for a user.
    """

    if not user:
        return

    Notification.objects.create(
        user=user,
        title=title,
        message=message,
    )


def notify_project_students(
    project,
    title,
    message,
):
    """
    Notify all active registered students connected to a project.

    The team leader is included even if the leader is missing from
    team.members.
    """

    student_ids = set(
        project.team.members.values_list(
            "id",
            flat=True,
        )
    )

    if project.team.leader_id:
        student_ids.add(
            project.team.leader_id
        )

    students = User.objects.filter(
        id__in=student_ids,
        role="STUDENT",
        is_active=True,
    )

    for student in students:
        create_notification(
            student,
            title,
            message,
        )


def get_project_or_none(project_id):
    """
    Return a project with its related data or None.
    """

    try:
        return (
            Project.objects.select_related(
                "team",
                "team__leader",
                "supervisor",
                "submitted_by",
            )
            .prefetch_related(
                "team__members",
                "team__member_infos",
                "documents",
            )
            .get(id=project_id)
        )

    except Project.DoesNotExist:
        return None


def get_document_or_none(document_id):
    """
    Return a project document with related project information.
    """

    try:
        return (
            ProjectDocument.objects.select_related(
                "project",
                "project__team",
                "project__team__leader",
                "project__supervisor",
                "project__submitted_by",
                "uploaded_by",
                "reviewed_by",
                "previous_version",
            )
            .prefetch_related(
                "project__team__members",
            )
            .get(id=document_id)
        )

    except ProjectDocument.DoesNotExist:
        return None


def examiner_has_project_access(
    user,
    project,
):
    """
    Return True when an active Examiner is assigned to the project's
    viva schedule.

    The import stays inside this helper to avoid a circular import
    between the projects and viva applications.
    """

    if (
        not user
        or not user.is_authenticated
        or user.role != "EXAMINER"
        or not user.is_active
    ):
        return False

    from viva.models import VivaSchedule

    return VivaSchedule.objects.filter(
        project_id=project.id,
        examiner_id=user.id,
    ).exists()


def user_can_view_project(user, project):
    """
    Determine whether a user can view a project and its documents.

    Access rules:
    - Super Admin: every project.
    - Supervisor: only projects assigned to that supervisor.
    - Student: only projects belonging to their own team.
    - Examiner: only projects whose viva is assigned to that examiner.
    """

    if user.role == "SUPER_ADMIN":
        return True

    if user.role == "SUPERVISOR":
        return (
            project.supervisor_id
            == user.id
        )

    if user.role == "STUDENT":
        is_leader = (
            project.team.leader_id
            == user.id
        )

        is_member = (
            project.team.members.filter(
                id=user.id,
            ).exists()
        )

        return is_leader or is_member

    if user.role == "EXAMINER":
        return examiner_has_project_access(
            user,
            project,
        )

    return False


def user_can_upload_project_document(
    user,
    project,
):
    """
    Determine whether a user can upload a project document.
    """

    if user.role == "SUPER_ADMIN":
        return True

    if user.role == "SUPERVISOR":
        return (
            project.supervisor_id
            == user.id
        )

    if user.role == "STUDENT":
        is_leader = (
            project.team.leader_id
            == user.id
        )

        is_member = (
            project.team.members.filter(
                id=user.id,
            ).exists()
        )

        return is_leader or is_member

    return False


def user_can_delete_project_document(
    user,
    document,
):
    """
    Super Admin can delete any document.

    A student can delete only their own latest version when its status
    is Pending, Revision Required or Rejected.
    """

    if user.role == "SUPER_ADMIN":
        return True

    if user.role == "STUDENT":
        return (
            document.uploaded_by_id
            == user.id
            and document.is_latest
            and document.status
            in {
                "PENDING",
                "REVISION_REQUIRED",
                "REJECTED",
            }
        )

    return False


def serialize_document_list(
    documents,
    request,
):
    """
    Serialize a document queryset consistently.
    """

    return ProjectDocumentSerializer(
        documents,
        many=True,
        context={
            "request": request,
        },
    ).data


# =========================================================
# TEAM LIST AND CREATE
# =========================================================


class TeamListCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def get(self, request):
        teams = (
            Team.objects.filter(
                members=request.user,
            )
            .select_related(
                "leader",
            )
            .prefetch_related(
                "members",
                "member_infos",
            )
            .distinct()
            .order_by("-id")
        )

        serializer = TeamSerializer(
            teams,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": teams.count(),
            "data": serializer.data,
        })

    def post(self, request):
        serializer = TeamSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        team = serializer.save()

        response_serializer = TeamSerializer(
            team,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Team created successfully."
                ),
                "data": (
                    response_serializer.data
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# TEAM UPDATE AND DELETE
# =========================================================


class TeamUpdateDeleteAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def put(self, request, team_id):
        try:
            team = Team.objects.get(
                id=team_id,
                leader=request.user,
            )

        except Team.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Team not found or you are not "
                        "the team leader."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        serializer = TeamSerializer(
            team,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        updated_team = serializer.save()

        response_serializer = TeamSerializer(
            updated_team,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "message": (
                "Team updated successfully."
            ),
            "data": response_serializer.data,
        })

    def delete(self, request, team_id):
        try:
            team = Team.objects.get(
                id=team_id,
                leader=request.user,
            )

        except Team.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Team not found or you are not "
                        "the team leader."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if hasattr(team, "project"):
            return Response(
                {
                    "success": False,
                    "message": (
                        "This team already has a project. "
                        "The project must be removed before "
                        "the team can be deleted."
                    ),
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        team.delete()

        return Response({
            "success": True,
            "message": (
                "Team deleted successfully."
            ),
        })


# =========================================================
# REGISTERED TEAM MEMBER UPDATE
# =========================================================


class TeamMemberUpdateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def patch(self, request, team_id):
        try:
            team = Team.objects.get(
                id=team_id,
                leader=request.user,
            )

        except Team.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Team not found or you are not "
                        "the team leader."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        member_ids = request.data.get(
            "members",
            [],
        )

        if not isinstance(member_ids, list):
            return Response(
                {
                    "success": False,
                    "message": (
                        "Members must be provided "
                        "as a list."
                    ),
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        try:
            normalized_member_ids = [
                int(member_id)
                for member_id
                in member_ids
            ]

        except (
            TypeError,
            ValueError,
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "One or more member IDs "
                        "are invalid."
                    ),
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        if (
            request.user.id
            not in normalized_member_ids
        ):
            normalized_member_ids.insert(
                0,
                request.user.id,
            )

        normalized_member_ids = list(
            dict.fromkeys(
                normalized_member_ids
            )
        )

        if (
            len(normalized_member_ids)
            > team.member_count
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        f"This team allows maximum "
                        f"{team.member_count} member(s)."
                    ),
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        if len(normalized_member_ids) > 3:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Maximum 3 members are allowed."
                    ),
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        members = User.objects.filter(
            id__in=normalized_member_ids,
            role="STUDENT",
            is_active=True,
        )

        if (
            members.count()
            != len(normalized_member_ids)
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "An invalid or inactive "
                        "student was selected."
                    ),
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        team.members.set(members)

        serializer = TeamSerializer(
            team,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "message": (
                "Team members updated successfully."
            ),
            "data": serializer.data,
        })


# =========================================================
# TEAM MEMBER INFORMATION CREATE
# =========================================================


class TeamMemberInfoCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def post(self, request, team_id):
        try:
            team = Team.objects.get(
                id=team_id,
                leader=request.user,
            )

        except Team.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Team not found or you are not "
                        "the team leader."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if (
            team.member_infos.count()
            >= team.member_count
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        f"Maximum {team.member_count} "
                        f"member(s) are allowed."
                    ),
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        serializer = TeamMemberInfoSerializer(
            data=request.data,
            context={
                "request": request,
                "team": team,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        member = serializer.save(
            team=team,
        )

        response_serializer = (
            TeamMemberInfoSerializer(
                member,
                context={
                    "request": request,
                    "team": team,
                },
            )
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Member added successfully."
                ),
                "data": (
                    response_serializer.data
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# TEAM MEMBER INFORMATION UPDATE AND DELETE
# =========================================================


class TeamMemberInfoUpdateDeleteAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def put(self, request, member_id):
        try:
            member = (
                TeamMemberInfo.objects
                .select_related(
                    "team",
                )
                .get(
                    id=member_id,
                    team__leader=request.user,
                )
            )

        except TeamMemberInfo.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Member not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        serializer = TeamMemberInfoSerializer(
            member,
            data=request.data,
            partial=True,
            context={
                "request": request,
                "team": member.team,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        updated_member = serializer.save()

        response_serializer = (
            TeamMemberInfoSerializer(
                updated_member,
                context={
                    "request": request,
                    "team": member.team,
                },
            )
        )

        return Response({
            "success": True,
            "message": (
                "Member updated successfully."
            ),
            "data": response_serializer.data,
        })

    def delete(self, request, member_id):
        try:
            member = (
                TeamMemberInfo.objects.get(
                    id=member_id,
                    team__leader=request.user,
                )
            )

        except TeamMemberInfo.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Member not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        member.delete()

        return Response({
            "success": True,
            "message": (
                "Member deleted successfully."
            ),
        })


# =========================================================
# PROJECT LIST AND CREATE
# =========================================================


class ProjectListCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def get(self, request):
        projects = (
            Project.objects.filter(
                team__members=request.user,
            )
            .select_related(
                "team",
                "team__leader",
                "supervisor",
                "submitted_by",
            )
            .prefetch_related(
                "team__members",
                "team__member_infos",
                "documents",
            )
            .distinct()
            .order_by("-id")
        )

        serializer = ProjectSerializer(
            projects,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": projects.count(),
            "data": serializer.data,
        })

    def post(self, request):
        serializer = ProjectSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        project = serializer.save()

        admins = User.objects.filter(
            role="SUPER_ADMIN",
            is_active=True,
        )

        for admin in admins:
            create_notification(
                admin,
                "New Project Submitted",
                (
                    f"{request.user.first_name} "
                    f"submitted a new project: "
                    f'"{project.title}".'
                ),
            )

        response_serializer = ProjectSerializer(
            project,
            context={
                "request": request,
            },
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Project submitted successfully."
                ),
                "data": (
                    response_serializer.data
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# PROJECT DETAILS
# =========================================================


class ProjectDetailAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, project_id):
        project = get_project_or_none(
            project_id,
        )

        if not project:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Project not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if not user_can_view_project(
            request.user,
            project,
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not allowed to "
                        "view this project."
                    ),
                },
                status=(
                    status.HTTP_403_FORBIDDEN
                ),
            )

        serializer = ProjectSerializer(
            project,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "data": serializer.data,
        })


# =========================================================
# ADMIN PROJECT LIST
# =========================================================


class AdminProjectListAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    def get(self, request):
        projects = (
            Project.objects.select_related(
                "team",
                "team__leader",
                "supervisor",
                "submitted_by",
            )
            .prefetch_related(
                "team__members",
                "team__member_infos",
                "documents",
            )
            .all()
            .order_by("-id")
        )

        serializer = ProjectSerializer(
            projects,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": projects.count(),
            "data": serializer.data,
        })


# =========================================================
# ASSIGN SUPERVISOR
# =========================================================


class AssignSupervisorAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    def patch(self, request, project_id):
        project = get_project_or_none(
            project_id,
        )

        if not project:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Project not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        serializer = AssignSupervisorSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        supervisor = User.objects.get(
            id=serializer.validated_data[
                "supervisor_id"
            ],
            role="SUPERVISOR",
            is_active=True,
        )

        project.supervisor = supervisor
        project.status = (
            "SUPERVISOR_ASSIGNED"
        )

        project.save(
            update_fields=[
                "supervisor",
                "status",
                "updated_at",
            ]
        )

        create_notification(
            supervisor,
            "New Project Assigned",
            (
                f'Project "{project.title}" '
                f"has been assigned to you."
            ),
        )

        supervisor_name = (
            f"{supervisor.first_name or ''} "
            f"{supervisor.last_name or ''}"
        ).strip()

        notify_project_students(
            project,
            "Supervisor Assigned",
            (
                f"{supervisor_name or 'A supervisor'} "
                f"has been assigned to your project "
                f'"{project.title}".'
            ),
        )

        response_serializer = ProjectSerializer(
            project,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "message": (
                "Supervisor assigned successfully."
            ),
            "data": response_serializer.data,
        })


# =========================================================
# ADMIN PROJECT STATUS UPDATE
# =========================================================


class ProjectStatusUpdateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    def patch(self, request, project_id):
        project = get_project_or_none(
            project_id,
        )

        if not project:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Project not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        serializer = (
            ProjectStatusUpdateSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        project.status = (
            serializer.validated_data[
                "status"
            ]
        )

        project.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        notify_project_students(
            project,
            "Project Status Updated",
            (
                f'Your project "{project.title}" '
                f"status is now "
                f"{project.get_status_display()}."
            ),
        )

        response_serializer = ProjectSerializer(
            project,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "message": (
                "Project status updated successfully."
            ),
            "data": response_serializer.data,
        })


# =========================================================
# SUPERVISOR ASSIGNED PROJECT LIST
# =========================================================


class SupervisorAssignedProjectListAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
        IsSupervisor,
    ]

    def get(self, request):
        projects = (
            Project.objects.filter(
                supervisor=request.user,
            )
            .select_related(
                "team",
                "team__leader",
                "supervisor",
                "submitted_by",
            )
            .prefetch_related(
                "team__members",
                "team__member_infos",
                "documents",
            )
            .order_by("-id")
        )

        serializer = ProjectSerializer(
            projects,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": projects.count(),
            "data": serializer.data,
        })


# =========================================================
# SUPERVISOR PROJECT REVIEW
# =========================================================


class SupervisorProjectReviewAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
        IsSupervisor,
    ]

    def patch(self, request, project_id):
        try:
            project = (
                Project.objects
                .select_related(
                    "team",
                    "supervisor",
                )
                .prefetch_related(
                    "team__members",
                )
                .get(
                    id=project_id,
                    supervisor=request.user,
                )
            )

        except Project.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Project not found or it "
                        "is not assigned to you."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        serializer = (
            SupervisorProjectReviewSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        new_status = (
            serializer.validated_data[
                "status"
            ]
        )

        comment = (
            serializer.validated_data.get(
                "comment",
                "",
            )
        )

        project.status = new_status

        project.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        if comment:
            ProjectFeedback.objects.create(
                project=project,
                supervisor=request.user,
                comment=comment,
            )

        notify_project_students(
            project,
            "Project Status Updated",
            (
                f'Your project "{project.title}" '
                f"status is now "
                f"{project.get_status_display()}."
            ),
        )

        response_serializer = ProjectSerializer(
            project,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "message": (
                "Project status updated successfully."
            ),
            "data": response_serializer.data,
        })


# =========================================================
# PROJECT FEEDBACK CREATE
# =========================================================


class ProjectFeedbackCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSupervisor,
    ]

    def post(self, request, project_id):
        try:
            project = Project.objects.get(
                id=project_id,
                supervisor=request.user,
            )

        except Project.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Project not found or it "
                        "is not assigned to you."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        serializer = ProjectFeedbackSerializer(
            data={
                "project": project.id,
                "comment": request.data.get(
                    "comment"
                ),
            },
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        feedback = serializer.save()

        notify_project_students(
            project,
            "New Project Feedback",
            (
                f"Supervisor added feedback "
                f"on your project "
                f'"{project.title}".'
            ),
        )

        response_serializer = (
            ProjectFeedbackSerializer(
                feedback,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Feedback submitted successfully."
                ),
                "data": (
                    response_serializer.data
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# PROJECT FEEDBACK LIST
# =========================================================


class ProjectFeedbackListAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, project_id):
        project = get_project_or_none(
            project_id,
        )

        if not project:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Project not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if not user_can_view_project(
            request.user,
            project,
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not allowed to "
                        "view this project's feedback."
                    ),
                },
                status=(
                    status.HTTP_403_FORBIDDEN
                ),
            )

        feedbacks = (
            project.feedbacks
            .select_related(
                "supervisor",
            )
            .all()
            .order_by("-id")
        )

        serializer = ProjectFeedbackSerializer(
            feedbacks,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": feedbacks.count(),
            "data": serializer.data,
        })


# =========================================================
# PROJECT DOCUMENT LIST AND UPLOAD
# =========================================================


class ProjectDocumentListCreateAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def get(self, request, project_id):
        """
        Return every document version belonging to the project.

        The response includes latest and previous versions.
        """

        project = get_project_or_none(
            project_id,
        )

        if not project:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Project not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if not user_can_view_project(
            request.user,
            project,
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not allowed to view "
                        "this project's documents."
                    ),
                },
                status=(
                    status.HTTP_403_FORBIDDEN
                ),
            )

        documents = (
            project.documents
            .select_related(
                "project",
                "project__team",
                "uploaded_by",
                "reviewed_by",
                "previous_version",
            )
            .all()
            .order_by(
                "-uploaded_at",
                "-id",
            )
        )

        latest_count = documents.filter(
            is_latest=True,
        ).count()

        previous_version_count = (
            documents.filter(
                is_latest=False,
            ).count()
        )

        return Response({
            "success": True,
            "project_id": project.id,
            "project_title": project.title,
            "count": documents.count(),
            "latest_count": latest_count,
            "previous_version_count": (
                previous_version_count
            ),
            "data": serialize_document_list(
                documents,
                request,
            ),
        })

    def post(self, request, project_id):
        """
        Upload a new submission or revised version.

        For a new document:
            title
            description
            document_type
            file

        For a revised version, also send:
            previous_document_id
        """

        project = get_project_or_none(
            project_id,
        )

        if not project:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Project not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if not user_can_upload_project_document(
            request.user,
            project,
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not allowed to upload "
                        "documents for this project."
                    ),
                },
                status=(
                    status.HTTP_403_FORBIDDEN
                ),
            )

        serializer = ProjectDocumentSerializer(
            data=request.data,
            context={
                "request": request,
                "project": project,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        document = serializer.save()

        is_revision = (
            document.previous_version_id
            is not None
        )

        if (
            project.supervisor
            and project.supervisor_id
            != request.user.id
        ):
            if is_revision:
                notification_title = (
                    "Revised Project Document"
                )

                notification_message = (
                    f'Version {document.version} of '
                    f'"{document.title}" was uploaded '
                    f'for project "{project.title}".'
                )

            else:
                notification_title = (
                    "New Project Document"
                )

                notification_message = (
                    f"A new "
                    f"{document.get_document_type_display()} "
                    f'document was uploaded for project '
                    f'"{project.title}".'
                )

            create_notification(
                project.supervisor,
                notification_title,
                notification_message,
            )

        response_serializer = (
            ProjectDocumentSerializer(
                document,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Revised document uploaded successfully."
                    if is_revision
                    else "Document uploaded successfully."
                ),
                "is_revision": is_revision,
                "version": document.version,
                "data": (
                    response_serializer.data
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# =========================================================
# PROJECT LATEST DOCUMENT LIST
# =========================================================


class ProjectLatestDocumentListAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, project_id):
        """
        Return only the current/latest version of each submission.
        """

        project = get_project_or_none(
            project_id,
        )

        if not project:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Project not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if not user_can_view_project(
            request.user,
            project,
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not allowed to view "
                        "this project's documents."
                    ),
                },
                status=(
                    status.HTTP_403_FORBIDDEN
                ),
            )

        documents = (
            project.documents
            .filter(
                is_latest=True,
            )
            .select_related(
                "project",
                "project__team",
                "uploaded_by",
                "reviewed_by",
                "previous_version",
            )
            .order_by(
                "-uploaded_at",
                "-id",
            )
        )

        status_summary = {
            "pending": documents.filter(
                status="PENDING",
            ).count(),
            "approved": documents.filter(
                status="APPROVED",
            ).count(),
            "revision_required": (
                documents.filter(
                    status="REVISION_REQUIRED",
                ).count()
            ),
            "rejected": documents.filter(
                status="REJECTED",
            ).count(),
        }

        return Response({
            "success": True,
            "project_id": project.id,
            "project_title": project.title,
            "count": documents.count(),
            "status_summary": status_summary,
            "data": serialize_document_list(
                documents,
                request,
            ),
        })


# =========================================================
# DOCUMENT VERSION HISTORY
# =========================================================


class ProjectDocumentVersionHistoryAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, document_id):
        """
        Return all versions from the same submission group.

        Versions are returned from newest to oldest.
        """

        document = get_document_or_none(
            document_id,
        )

        if not document:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Document not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if not user_can_view_project(
            request.user,
            document.project,
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not allowed to view "
                        "this document's version history."
                    ),
                },
                status=(
                    status.HTTP_403_FORBIDDEN
                ),
            )

        versions = (
            ProjectDocument.objects.filter(
                submission_group=(
                    document.submission_group
                ),
                project=document.project,
            )
            .select_related(
                "project",
                "project__team",
                "uploaded_by",
                "reviewed_by",
                "previous_version",
            )
            .order_by(
                "-version",
                "-id",
            )
        )

        latest_version = versions.filter(
            is_latest=True,
        ).first()

        return Response({
            "success": True,
            "project_id": document.project_id,
            "project_title": (
                document.project.title
            ),
            "submission_group": str(
                document.submission_group
            ),
            "document_type": (
                document.document_type
            ),
            "document_type_display": (
                document
                .get_document_type_display()
            ),
            "title": document.title,
            "version_count": versions.count(),
            "latest_document_id": (
                latest_version.id
                if latest_version
                else None
            ),
            "latest_version": (
                latest_version.version
                if latest_version
                else None
            ),
            "data": serialize_document_list(
                versions,
                request,
            ),
        })


# =========================================================
# PROJECT DOCUMENT DELETE
# =========================================================


class ProjectDocumentDeleteAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def delete(self, request, document_id):
        document = get_document_or_none(
            document_id,
        )

        if not document:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Document not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if not user_can_delete_project_document(
            request.user,
            document,
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not allowed to delete "
                        "this document."
                    ),
                },
                status=(
                    status.HTTP_403_FORBIDDEN
                ),
            )

        was_latest = document.is_latest

        submission_group = (
            document.submission_group
        )

        project_id = document.project_id

        document_title = document.title

        stored_file = document.file

        document.delete()

        promoted_document = None

        if was_latest:
            promoted_document = (
                ProjectDocument.objects.filter(
                    submission_group=(
                        submission_group
                    ),
                    project_id=project_id,
                )
                .order_by(
                    "-version",
                    "-id",
                )
                .first()
            )

            if promoted_document:
                promoted_document.is_latest = True

                promoted_document.save(
                    update_fields=[
                        "is_latest",
                        "updated_at",
                    ]
                )

        if stored_file:
            try:
                stored_file.delete(
                    save=False,
                )

            except (
                FileNotFoundError,
                OSError,
            ):
                pass

        return Response({
            "success": True,
            "message": (
                "Document deleted successfully."
            ),
            "deleted_title": document_title,
            "previous_version_promoted": (
                promoted_document is not None
            ),
            "promoted_document_id": (
                promoted_document.id
                if promoted_document
                else None
            ),
            "promoted_version": (
                promoted_document.version
                if promoted_document
                else None
            ),
        })


# =========================================================
# PROJECT DOCUMENT REVIEW
# =========================================================


class ProjectDocumentReviewAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSupervisor,
    ]

    def patch(self, request, document_id):
        try:
            document = (
                ProjectDocument.objects
                .select_related(
                    "project",
                    "project__team",
                    "project__supervisor",
                    "uploaded_by",
                    "previous_version",
                )
                .prefetch_related(
                    "project__team__members",
                )
                .get(
                    id=document_id,
                    project__supervisor=(
                        request.user
                    ),
                )
            )

        except ProjectDocument.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Document not found or its "
                        "project is not assigned to you."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if not document.is_latest:
            return Response(
                {
                    "success": False,
                    "message": (
                        "A previous document version "
                        "cannot be reviewed. Review the "
                        "latest version instead."
                    ),
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        serializer = (
            ProjectDocumentReviewSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        document.status = (
            serializer.validated_data[
                "status"
            ]
        )

        document.supervisor_remarks = (
            serializer.validated_data.get(
                "supervisor_remarks",
                "",
            )
        )

        document.reviewed_by = request.user

        document.save()

        notify_project_students(
            document.project,
            "Project Document Reviewed",
            (
                f'"{document.title}" '
                f"Version {document.version} "
                f"was reviewed. Status: "
                f"{document.get_status_display()}."
            ),
        )

        response_serializer = (
            ProjectDocumentSerializer(
                document,
                context={
                    "request": request,
                },
            )
        )

        return Response({
            "success": True,
            "message": (
                "Document reviewed successfully."
            ),
            "data": response_serializer.data,
        })


# =========================================================
# PROJECT DOCUMENT DOWNLOAD
# =========================================================


class ProjectDocumentDownloadAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request, document_id):
        document = get_document_or_none(
            document_id,
        )

        if not document:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Document not found."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        if not user_can_view_project(
            request.user,
            document.project,
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You are not allowed to "
                        "download this document."
                    ),
                },
                status=(
                    status.HTTP_403_FORBIDDEN
                ),
            )

        if not document.file:
            return Response(
                {
                    "success": False,
                    "message": (
                        "The uploaded file is unavailable."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        try:
            file_handle = (
                document.file.open("rb")
            )

        except (
            FileNotFoundError,
            OSError,
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "The uploaded file could not "
                        "be found on the server."
                    ),
                },
                status=(
                    status.HTTP_404_NOT_FOUND
                ),
            )

        ProjectDocument.objects.filter(
            id=document.id,
        ).update(
            download_count=(
                F("download_count") + 1
            )
        )

        return FileResponse(
            file_handle,
            as_attachment=True,
            filename=(
                document.file_name
                or "project-document"
            ),
        )


# =========================================================
# ADMIN ALL PROJECT DOCUMENTS
# =========================================================


class AdminProjectDocumentListAPIView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    def get(self, request):
        """
        Admin can request all versions or only latest versions.

        Examples:
            /api/projects/admin/documents/
            /api/projects/admin/documents/?latest_only=true
        """

        latest_only = (
            str(
                request.query_params.get(
                    "latest_only",
                    "",
                )
            )
            .strip()
            .lower()
            in {
                "1",
                "true",
                "yes",
            }
        )

        documents = (
            ProjectDocument.objects
            .select_related(
                "project",
                "project__team",
                "project__supervisor",
                "uploaded_by",
                "reviewed_by",
                "previous_version",
            )
            .all()
        )

        if latest_only:
            documents = documents.filter(
                is_latest=True,
            )

        documents = documents.order_by(
            "-uploaded_at",
            "-id",
        )

        return Response({
            "success": True,
            "latest_only": latest_only,
            "count": documents.count(),
            "data": serialize_document_list(
                documents,
                request,
            ),
        })