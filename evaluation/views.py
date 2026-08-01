from django.db import transaction
from django.db.models import Avg, Max, Min

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import (
    IsExaminer,
    IsStudent,
    IsSuperAdmin,
)
from notifications.models import Notification
from projects.models import Project

from .models import (
    Evaluation,
    EvaluationAuditLog,
)
from .serializers import (
    EvaluationSerializer,
    PublishResultSerializer,
)


def create_notification(
    user,
    title,
    message,
):
    if not user:
        return

    Notification.objects.create(
        user=user,
        title=title,
        message=message,
    )


def notify_project_students(
    evaluation,
    title,
    message,
):
    project = evaluation.project

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

    for student in project.team.members.model.objects.filter(
        id__in=student_ids,
        role="STUDENT",
        is_active=True,
    ):
        create_notification(
            student,
            title,
            message,
        )


def evaluation_snapshot(evaluation):
    return {
        "proposal_marks": float(
            evaluation.proposal_marks
        ),
        "progress_marks": float(
            evaluation.progress_marks
        ),
        "viva_marks": float(
            evaluation.viva_marks
        ),
        "total_marks": float(
            evaluation.total_marks
        ),
        "grade": evaluation.grade,
        "grade_point": float(
            evaluation.grade_point
        ),
        "grade_definition": (
            evaluation.grade_definition
        ),
        "remarks": evaluation.remarks,
        "published": evaluation.published,
        "rubric_enabled": (
            evaluation.rubric_enabled
        ),
    }


def get_evaluation_queryset():
    return (
        Evaluation.objects.select_related(
            "project",
            "project__team",
            "project__team__leader",
            "project__supervisor",
            "examiner",
            "published_by",
        )
        .prefetch_related(
            "project__team__members",
            "audit_logs",
            "audit_logs__changed_by",
        )
    )


class EvaluationCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsExaminer,
    ]

    @transaction.atomic
    def post(self, request):
        project_id = request.data.get(
            "project"
        )

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
                    viva_schedule__examiner=(
                        request.user
                    ),
                )
            )

        except Project.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Project not found or viva "
                        "is not assigned to you."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if hasattr(project, "evaluation"):
            return Response(
                {
                    "success": False,
                    "message": (
                        "Evaluation already exists "
                        "for this project."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = EvaluationSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        evaluation = serializer.save(
            examiner=request.user,
        )

        EvaluationAuditLog.objects.create(
            evaluation=evaluation,
            action="CREATED",
            changed_by=request.user,
            old_data={},
            new_data=evaluation_snapshot(
                evaluation
            ),
        )

        response_serializer = (
            EvaluationSerializer(
                evaluation,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Evaluation submitted successfully."
                ),
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class EvaluationUpdateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsExaminer,
    ]

    @transaction.atomic
    def patch(
        self,
        request,
        evaluation_id,
    ):
        try:
            evaluation = (
                get_evaluation_queryset()
                .get(
                    id=evaluation_id,
                    examiner=request.user,
                )
            )

        except Evaluation.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Evaluation not found or "
                        "it does not belong to you."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if evaluation.is_locked:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Published evaluations are "
                        "locked and cannot be edited."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_data = evaluation_snapshot(
            evaluation
        )

        serializer = EvaluationSerializer(
            evaluation,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        updated_evaluation = (
            serializer.save()
        )

        EvaluationAuditLog.objects.create(
            evaluation=updated_evaluation,
            action="UPDATED",
            changed_by=request.user,
            old_data=old_data,
            new_data=evaluation_snapshot(
                updated_evaluation
            ),
        )

        response_serializer = (
            EvaluationSerializer(
                updated_evaluation,
                context={
                    "request": request,
                },
            )
        )

        return Response({
            "success": True,
            "message": (
                "Evaluation updated successfully."
            ),
            "data": response_serializer.data,
        })


class ExaminerEvaluationListAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsExaminer,
    ]

    def get(self, request):
        evaluations = (
            get_evaluation_queryset()
            .filter(
                examiner=request.user,
            )
            .order_by("-id")
        )

        serializer = EvaluationSerializer(
            evaluations,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": evaluations.count(),
            "data": serializer.data,
        })


class AdminEvaluationListAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    def get(self, request):
        evaluations = (
            get_evaluation_queryset()
            .all()
            .order_by("-id")
        )

        serializer = EvaluationSerializer(
            evaluations,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": evaluations.count(),
            "data": serializer.data,
        })


class PublishResultAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    @transaction.atomic
    def patch(
        self,
        request,
        evaluation_id,
    ):
        try:
            evaluation = (
                get_evaluation_queryset()
                .get(id=evaluation_id)
            )

        except Evaluation.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Evaluation not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = PublishResultSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        old_data = evaluation_snapshot(
            evaluation
        )

        should_publish = (
            serializer.validated_data[
                "published"
            ]
        )

        if should_publish:
            evaluation.publish(
                request.user
            )

            audit_action = "PUBLISHED"
            message = (
                "Result published successfully."
            )

        else:
            evaluation.unpublish()

            audit_action = "UNPUBLISHED"
            message = (
                "Result unpublished successfully."
            )

        evaluation.save()

        EvaluationAuditLog.objects.create(
            evaluation=evaluation,
            action=audit_action,
            changed_by=request.user,
            old_data=old_data,
            new_data=evaluation_snapshot(
                evaluation
            ),
        )

        if should_publish:
            notify_project_students(
                evaluation,
                "Project Result Published",
                (
                    f'Result for project '
                    f'"{evaluation.project.title}" '
                    f"has been published."
                ),
            )

        response_serializer = (
            EvaluationSerializer(
                evaluation,
                context={
                    "request": request,
                },
            )
        )

        return Response({
            "success": True,
            "message": message,
            "data": response_serializer.data,
        })


class StudentResultAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    def get(self, request):
        evaluations = (
            get_evaluation_queryset()
            .filter(
                project__team__members=(
                    request.user
                ),
                published=True,
            )
            .distinct()
            .order_by("-id")
        )

        serializer = EvaluationSerializer(
            evaluations,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": evaluations.count(),
            "data": serializer.data,
        })


class EvaluationAnalyticsAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    def get(self, request):
        evaluations = Evaluation.objects.all()

        published = evaluations.filter(
            published=True
        )

        aggregate = published.aggregate(
            average_marks=Avg(
                "total_marks"
            ),
            highest_marks=Max(
                "total_marks"
            ),
            lowest_marks=Min(
                "total_marks"
            ),
        )

        grade_distribution = {
            grade: published.filter(
                grade=grade
            ).count()
            for grade in [
                "A+",
                "A",
                "A-",
                "B+",
                "B",
                "B-",
                "C+",
                "C",
                "D",
                "F",
            ]
        }

        total_published = published.count()

        passed_count = published.exclude(
            grade="F"
        ).count()

        pass_rate = (
            round(
                (
                    passed_count
                    / total_published
                )
                * 100,
                2,
            )
            if total_published
            else 0
        )

        return Response({
            "success": True,
            "data": {
                "total_evaluations": (
                    evaluations.count()
                ),
                "published_count": (
                    total_published
                ),
                "draft_count": (
                    evaluations.filter(
                        published=False
                    ).count()
                ),
                "average_marks": (
                    aggregate[
                        "average_marks"
                    ]
                    or 0
                ),
                "highest_marks": (
                    aggregate[
                        "highest_marks"
                    ]
                    or 0
                ),
                "lowest_marks": (
                    aggregate[
                        "lowest_marks"
                    ]
                    or 0
                ),
                "pass_rate": pass_rate,
                "grade_distribution": (
                    grade_distribution
                ),
            },
        })