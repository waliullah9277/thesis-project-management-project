from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import (
    IsExaminer,
    IsSuperAdmin,
)
from notifications.models import Notification

from .models import VivaSchedule
from .serializers import (
    AssignExaminerSerializer,
    VivaScheduleSerializer,
)


def get_viva_queryset():
    """
    Return Viva schedules with the related project data required by
    the serializer and examiner frontend.
    """

    return (
        VivaSchedule.objects.select_related(
            "project",
            "project__team",
            "project__team__leader",
            "project__supervisor",
            "project__submitted_by",
            "examiner",
        )
        .prefetch_related(
            "project__team__members",
            "project__team__member_infos",
            "project__documents",
        )
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


class VivaScheduleListCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    def get(self, request):
        vivas = (
            get_viva_queryset()
            .all()
            .order_by("-id")
        )

        serializer = VivaScheduleSerializer(
            vivas,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": vivas.count(),
            "data": serializer.data,
        })

    def post(self, request):
        serializer = VivaScheduleSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        viva = serializer.save()

        response_serializer = (
            VivaScheduleSerializer(
                viva,
                context={
                    "request": request,
                },
            )
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Viva schedule created successfully."
                ),
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class AssignExaminerAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    def patch(self, request, viva_id):
        try:
            viva = (
                get_viva_queryset()
                .get(id=viva_id)
            )

        except VivaSchedule.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Viva schedule not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AssignExaminerSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        examiner = User.objects.get(
            id=serializer.validated_data[
                "examiner_id"
            ],
            role="EXAMINER",
            is_active=True,
        )

        viva.examiner = examiner

        viva.save(
            update_fields=[
                "examiner",
            ]
        )

        create_notification(
            examiner,
            "New Viva Assigned",
            (
                f'You have been assigned to the viva for '
                f'project "{viva.project.title}" on '
                f"{viva.date} at {viva.time}."
            ),
        )

        response_serializer = (
            VivaScheduleSerializer(
                viva,
                context={
                    "request": request,
                },
            )
        )

        return Response({
            "success": True,
            "message": (
                "Examiner assigned successfully."
            ),
            "data": response_serializer.data,
        })


class ExaminerAssignedVivaAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsExaminer,
    ]

    def get(self, request):
        vivas = (
            get_viva_queryset()
            .filter(
                examiner=request.user,
            )
            .order_by("-id")
        )

        serializer = VivaScheduleSerializer(
            vivas,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": vivas.count(),
            "data": serializer.data,
        })


class VivaStatusUpdateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def patch(self, request, viva_id):
        try:
            viva = (
                get_viva_queryset()
                .get(id=viva_id)
            )

        except VivaSchedule.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Viva schedule not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role == "EXAMINER":
            if viva.examiner_id != request.user.id:
                return Response(
                    {
                        "success": False,
                        "message": (
                            "You can update only your "
                            "assigned viva."
                        ),
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        elif request.user.role != "SUPER_ADMIN":
            return Response(
                {
                    "success": False,
                    "message": (
                        "You do not have permission "
                        "to perform this action."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get(
            "status"
        )

        allowed_statuses = {
            "SCHEDULED",
            "COMPLETED",
            "CANCELLED",
        }

        if new_status not in allowed_statuses:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Invalid viva status."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        viva.status = new_status

        viva.save(
            update_fields=[
                "status",
            ]
        )

        response_serializer = (
            VivaScheduleSerializer(
                viva,
                context={
                    "request": request,
                },
            )
        )

        return Response({
            "success": True,
            "message": (
                "Viva status updated successfully."
            ),
            "data": response_serializer.data,
        })