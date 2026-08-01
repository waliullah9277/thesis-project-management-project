from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q

from rest_framework import status
from rest_framework.parsers import (
    FormParser,
    MultiPartParser,
)
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
    Company,
    IndustrialTraining,
    TrainingFeedback,
    TrainingStatusHistory,
)
from .serializers import (
    AssignTrainingSupervisorSerializer,
    CompanySerializer,
    IndustrialTrainingSerializer,
    TrainingFeedbackCreateSerializer,
    TrainingFeedbackListSerializer,
    TrainingStatusUpdateSerializer,
)


def get_training_queryset():
    return (
        IndustrialTraining.objects
        .select_related(
            "student",
            "company",
            "supervisor",
            "approved_by",
        )
        .prefetch_related(
            "feedbacks",
            "feedbacks__supervisor",
            "status_history",
            "status_history__changed_by",
        )
    )


def create_training_notification(
    user,
    title,
    message,
    action_url,
    related_object_id,
):
    if not user:
        return

    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type="TRAINING",
        action_url=action_url,
        related_object_id=related_object_id,
    )


def serialize_training(
    training,
    request,
):
    return IndustrialTrainingSerializer(
        training,
        context={
            "request": request,
        },
    ).data


class CompanyListCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(self, request):
        companies = Company.objects.all()

        serializer = CompanySerializer(
            companies,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": companies.count(),
            "data": serializer.data,
        })

    def post(self, request):
        if request.user.role != "SUPER_ADMIN":
            return Response(
                {
                    "success": False,
                    "message": (
                        "Only Super Admin can create a company."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CompanySerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        company = serializer.save()

        return Response(
            {
                "success": True,
                "message": (
                    "Company created successfully."
                ),
                "data": CompanySerializer(
                    company
                ).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CompanyDetailAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    def patch(
        self,
        request,
        company_id,
    ):
        try:
            company = Company.objects.get(
                id=company_id,
            )

        except Company.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Company not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CompanySerializer(
            company,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        company = serializer.save()

        return Response({
            "success": True,
            "message": (
                "Company updated successfully."
            ),
            "data": CompanySerializer(
                company
            ).data,
        })

    def delete(
        self,
        request,
        company_id,
    ):
        try:
            company = Company.objects.get(
                id=company_id,
            )

        except Company.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Company not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if company.trainings.exists():
            return Response(
                {
                    "success": False,
                    "message": (
                        "This company cannot be deleted because training records use it."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        company.delete()

        return Response({
            "success": True,
            "message": (
                "Company deleted successfully."
            ),
        })


class StudentTrainingListCreateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def get(self, request):
        trainings = (
            get_training_queryset()
            .filter(
                student=request.user,
            )
        )

        serializer = IndustrialTrainingSerializer(
            trainings,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": trainings.count(),
            "data": serializer.data,
        })

    @transaction.atomic
    def post(self, request):
        serializer = IndustrialTrainingSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        training = serializer.save()

        TrainingStatusHistory.objects.create(
            training=training,
            previous_status="",
            new_status="PENDING",
            reason=(
                "Training request submitted."
            ),
            changed_by=request.user,
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Industrial training request submitted successfully."
                ),
                "data": serialize_training(
                    training,
                    request,
                ),
            },
            status=status.HTTP_201_CREATED,
        )


class StudentTrainingDetailAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsStudent,
    ]

    parser_classes = [
        MultiPartParser,
        FormParser,
    ]

    def patch(
        self,
        request,
        training_id,
    ):
        try:
            training = (
                get_training_queryset()
                .get(
                    id=training_id,
                    student=request.user,
                )
            )

        except IndustrialTraining.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Training record not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        editable_fields = {
            "title",
            "designation",
            "description",
            "company",
            "start_date",
            "end_date",
            "offer_letter",
            "final_report",
            "company_feedback",
        }

        if training.status in {
            "REJECTED",
            "CANCELLED",
            "COMPLETED",
        }:
            allowed_fields = {
                "final_report",
                "company_feedback",
            }

        else:
            allowed_fields = editable_fields

        disallowed = (
            set(request.data.keys())
            - allowed_fields
        )

        if disallowed:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Some submitted fields cannot be updated."
                    ),
                    "fields": sorted(
                        disallowed
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = IndustrialTrainingSerializer(
            training,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        training = serializer.save()

        return Response({
            "success": True,
            "message": (
                "Training information updated successfully."
            ),
            "data": serialize_training(
                training,
                request,
            ),
        })


class AdminTrainingListAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    def get(self, request):
        trainings = get_training_queryset()

        search = request.query_params.get(
            "search",
            "",
        ).strip()

        status_value = request.query_params.get(
            "status",
            "",
        ).strip()

        if search:
            trainings = trainings.filter(
                Q(title__icontains=search)
                | Q(designation__icontains=search)
                | Q(student__first_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(student__student_id__icontains=search)
                | Q(company__name__icontains=search)
                | Q(supervisor__first_name__icontains=search)
                | Q(supervisor__last_name__icontains=search)
            )

        if status_value:
            trainings = trainings.filter(
                status=status_value,
            )

        serializer = IndustrialTrainingSerializer(
            trainings,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": trainings.count(),
            "data": serializer.data,
        })


class AssignTrainingSupervisorAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSuperAdmin,
    ]

    @transaction.atomic
    def patch(
        self,
        request,
        training_id,
    ):
        try:
            training = (
                get_training_queryset()
                .get(id=training_id)
            )

        except IndustrialTraining.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Training record not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = AssignTrainingSupervisorSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            supervisor = User.objects.get(
                id=serializer.validated_data[
                    "supervisor_id"
                ],
                role="SUPERVISOR",
                is_active=True,
            )

        except User.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "An active and valid supervisor was not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        training.supervisor = supervisor

        if training.status == "PENDING":
            previous_status = training.status
            training.set_status(
                "APPROVED",
                changed_by=request.user,
                reason=(
                    "Supervisor assigned and training approved."
                ),
            )

            TrainingStatusHistory.objects.create(
                training=training,
                previous_status=previous_status,
                new_status="APPROVED",
                reason=training.status_reason,
                changed_by=request.user,
            )

        training.save()

        create_training_notification(
            supervisor,
            "Industrial Training Assigned",
            (
                f'You have been assigned to supervise '
                f'"{training.title}" for '
                f"{training.student}."
            ),
            "../training.html",
            training.id,
        )

        create_training_notification(
            training.student,
            "Training Supervisor Assigned",
            (
                f"{supervisor} has been assigned as "
                f'your supervisor for "{training.title}".'
            ),
            "../training.html",
            training.id,
        )

        return Response({
            "success": True,
            "message": (
                "Training supervisor assigned successfully."
            ),
            "data": serialize_training(
                training,
                request,
            ),
        })


class TrainingStatusUpdateAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    @transaction.atomic
    def patch(
        self,
        request,
        training_id,
    ):
        try:
            training = (
                get_training_queryset()
                .get(id=training_id)
            )

        except IndustrialTraining.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Training record not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role == "SUPER_ADMIN":
            pass

        elif request.user.role == "SUPERVISOR":
            if training.supervisor_id != request.user.id:
                return Response(
                    {
                        "success": False,
                        "message": (
                            "You can update only your assigned training."
                        ),
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        else:
            return Response(
                {
                    "success": False,
                    "message": (
                        "You do not have permission to update training status."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = TrainingStatusUpdateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        new_status = serializer.validated_data[
            "status"
        ]

        reason = serializer.validated_data[
            "reason"
        ]

        if (
            request.user.role == "SUPERVISOR"
            and new_status not in {
                "APPROVED",
                "ONGOING",
                "COMPLETED",
                "REJECTED",
            }
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "Supervisor cannot set this training status."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        previous_status = training.status

        training.set_status(
            new_status,
            changed_by=request.user,
            reason=reason,
        )

        try:
            training.save()

        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                error_data = exc.message_dict

            else:
                error_data = {
                    "non_field_errors": exc.messages,
                }

            return Response(
                {
                    "success": False,
                    "message": (
                        "Training status could not be updated."
                    ),
                    "errors": error_data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        TrainingStatusHistory.objects.create(
            training=training,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            changed_by=request.user,
        )

        create_training_notification(
            training.student,
            "Training Status Updated",
            (
                f'Your training "{training.title}" '
                f"status is now "
                f"{training.get_status_display()}."
            ),
            "../training.html",
            training.id,
        )

        return Response({
            "success": True,
            "message": (
                "Training status updated successfully."
            ),
            "data": serialize_training(
                training,
                request,
            ),
        })


class SupervisorTrainingListAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsSupervisor,
    ]

    def get(self, request):
        trainings = (
            get_training_queryset()
            .filter(
                supervisor=request.user,
            )
        )

        serializer = IndustrialTrainingSerializer(
            trainings,
            many=True,
            context={
                "request": request,
            },
        )

        return Response({
            "success": True,
            "count": trainings.count(),
            "data": serializer.data,
        })


class TrainingFeedbackAPIView(APIView):
    permission_classes = [
        IsAuthenticated,
    ]

    def get(
        self,
        request,
        training_id,
    ):
        try:
            training = (
                get_training_queryset()
                .get(id=training_id)
            )

        except IndustrialTraining.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Training record not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            request.user.role == "STUDENT"
            and training.student_id != request.user.id
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You can view only your own training feedback."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            request.user.role == "SUPERVISOR"
            and training.supervisor_id != request.user.id
        ):
            return Response(
                {
                    "success": False,
                    "message": (
                        "You can view only assigned training feedback."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.user.role not in {
            "STUDENT",
            "SUPERVISOR",
            "SUPER_ADMIN",
        }:
            return Response(
                {
                    "success": False,
                    "message": (
                        "You do not have permission to view feedback."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        feedbacks = training.feedbacks.all()

        serializer = TrainingFeedbackListSerializer(
            feedbacks,
            many=True,
        )

        return Response({
            "success": True,
            "count": feedbacks.count(),
            "data": serializer.data,
        })

    @transaction.atomic
    def patch(
        self,
        request,
        training_id,
    ):
        if request.user.role != "SUPERVISOR":
            return Response(
                {
                    "success": False,
                    "message": (
                        "Only a supervisor can give feedback."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            training = (
                get_training_queryset()
                .get(
                    id=training_id,
                    supervisor=request.user,
                )
            )

        except IndustrialTraining.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": (
                        "Training record not found or not assigned to you."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TrainingFeedbackCreateSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        feedback = TrainingFeedback.objects.create(
            training=training,
            supervisor=request.user,
            comment=serializer.validated_data[
                "comment"
            ],
        )

        training.supervisor_feedback = (
            feedback.comment
        )

        training.save(
            update_fields=[
                "supervisor_feedback",
                "updated_at",
            ]
        )

        create_training_notification(
            training.student,
            "New Training Feedback",
            (
                f'Your supervisor added feedback '
                f'for "{training.title}".'
            ),
            "../training.html",
            training.id,
        )

        return Response({
            "success": True,
            "message": (
                "Training feedback submitted successfully."
            ),
            "data": TrainingFeedbackListSerializer(
                feedback
            ).data,
        })