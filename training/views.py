from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.permissions import IsSuperAdmin, IsStudent, IsSupervisor
from accounts.models import User
from .models import Company, IndustrialTraining
from .serializers import (
    CompanySerializer,
    IndustrialTrainingSerializer,
    TrainingStatusUpdateSerializer,
    TrainingFeedbackSerializer,
)


class CompanyListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        companies = Company.objects.all().order_by("-id")
        serializer = CompanySerializer(companies, many=True)

        return Response({
            "success": True,
            "count": companies.count(),
            "data": serializer.data
        })

    def post(self, request):
        serializer = CompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Company created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class StudentTrainingListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        trainings = IndustrialTraining.objects.filter(
            student=request.user
        ).order_by("-id")

        serializer = IndustrialTrainingSerializer(trainings, many=True)

        return Response({
            "success": True,
            "count": trainings.count(),
            "data": serializer.data
        })

    def post(self, request):
        serializer = IndustrialTrainingSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Industrial training request submitted successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class AdminTrainingListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        trainings = IndustrialTraining.objects.all().order_by("-id")
        serializer = IndustrialTrainingSerializer(trainings, many=True)

        return Response({
            "success": True,
            "count": trainings.count(),
            "data": serializer.data
        })


class AssignTrainingSupervisorAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request, training_id):
        try:
            training = IndustrialTraining.objects.get(id=training_id)
        except IndustrialTraining.DoesNotExist:
            return Response({
                "success": False,
                "message": "Training record not found."
            }, status=status.HTTP_404_NOT_FOUND)

        supervisor_id = request.data.get("supervisor_id")

        try:
            supervisor = User.objects.get(id=supervisor_id, role="SUPERVISOR")
        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "Valid supervisor not found."
            }, status=status.HTTP_404_NOT_FOUND)

        training.supervisor = supervisor
        training.status = "ONGOING"
        training.save()

        return Response({
            "success": True,
            "message": "Training supervisor assigned successfully.",
            "data": IndustrialTrainingSerializer(training).data
        })


class TrainingStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request, training_id):
        try:
            training = IndustrialTraining.objects.get(id=training_id)
        except IndustrialTraining.DoesNotExist:
            return Response({
                "success": False,
                "message": "Training record not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TrainingStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        training.status = serializer.validated_data["status"]
        training.save()

        return Response({
            "success": True,
            "message": "Training status updated successfully.",
            "data": IndustrialTrainingSerializer(training).data
        })


class SupervisorTrainingListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def get(self, request):
        trainings = IndustrialTraining.objects.filter(
            supervisor=request.user
        ).order_by("-id")

        serializer = IndustrialTrainingSerializer(trainings, many=True)

        return Response({
            "success": True,
            "count": trainings.count(),
            "data": serializer.data
        })


class TrainingFeedbackAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def patch(self, request, training_id):
        try:
            training = IndustrialTraining.objects.get(
                id=training_id,
                supervisor=request.user
            )
        except IndustrialTraining.DoesNotExist:
            return Response({
                "success": False,
                "message": "Training record not found or not assigned to you."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = TrainingFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        training.supervisor_feedback = serializer.validated_data["supervisor_feedback"]
        training.save()

        return Response({
            "success": True,
            "message": "Training feedback submitted successfully.",
            "data": IndustrialTrainingSerializer(training).data
        })