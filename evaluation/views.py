from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.permissions import IsExaminer, IsSuperAdmin, IsStudent
from projects.models import Project
from .models import Evaluation
from .serializers import EvaluationSerializer, PublishResultSerializer


class EvaluationCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsExaminer]

    def post(self, request):
        project_id = request.data.get("project")

        try:
            project = Project.objects.get(
                id=project_id,
                viva_schedule__examiner=request.user
            )
        except Project.DoesNotExist:
            return Response({
                "success": False,
                "message": "Project not found or viva is not assigned to you."
            }, status=status.HTTP_404_NOT_FOUND)

        if hasattr(project, "evaluation"):
            return Response({
                "success": False,
                "message": "Evaluation already exists for this project."
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = EvaluationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(examiner=request.user)

        return Response({
            "success": True,
            "message": "Evaluation submitted successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class ExaminerEvaluationListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsExaminer]

    def get(self, request):
        evaluations = Evaluation.objects.filter(
            examiner=request.user
        ).order_by("-id")

        serializer = EvaluationSerializer(evaluations, many=True)

        return Response({
            "success": True,
            "count": evaluations.count(),
            "data": serializer.data
        })


class AdminEvaluationListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        evaluations = Evaluation.objects.all().order_by("-id")
        serializer = EvaluationSerializer(evaluations, many=True)

        return Response({
            "success": True,
            "count": evaluations.count(),
            "data": serializer.data
        })


class PublishResultAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request, evaluation_id):
        try:
            evaluation = Evaluation.objects.get(id=evaluation_id)
        except Evaluation.DoesNotExist:
            return Response({
                "success": False,
                "message": "Evaluation not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PublishResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        evaluation.published = serializer.validated_data["published"]
        evaluation.save()

        return Response({
            "success": True,
            "message": "Result publication status updated successfully.",
            "data": EvaluationSerializer(evaluation).data
        })


class StudentResultAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        evaluations = Evaluation.objects.filter(
            project__team__members=request.user,
            published=True
        ).order_by("-id")

        serializer = EvaluationSerializer(evaluations, many=True)

        return Response({
            "success": True,
            "count": evaluations.count(),
            "data": serializer.data
        })