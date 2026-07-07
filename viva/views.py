from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.models import User
from accounts.permissions import IsSuperAdmin, IsExaminer
from .models import VivaSchedule
from .serializers import VivaScheduleSerializer, AssignExaminerSerializer


class VivaScheduleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        vivas = VivaSchedule.objects.all().order_by("-id")
        serializer = VivaScheduleSerializer(vivas, many=True)

        return Response({
            "success": True,
            "count": vivas.count(),
            "data": serializer.data
        })

    def post(self, request):
        serializer = VivaScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Viva schedule created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)


class AssignExaminerAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request, viva_id):
        try:
            viva = VivaSchedule.objects.get(id=viva_id)
        except VivaSchedule.DoesNotExist:
            return Response({
                "success": False,
                "message": "Viva schedule not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = AssignExaminerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        examiner = User.objects.get(
            id=serializer.validated_data["examiner_id"],
            role="EXAMINER"
        )

        viva.examiner = examiner
        viva.save()

        return Response({
            "success": True,
            "message": "Examiner assigned successfully.",
            "data": VivaScheduleSerializer(viva).data
        })


class ExaminerAssignedVivaAPIView(APIView):
    permission_classes = [IsAuthenticated, IsExaminer]

    def get(self, request):
        vivas = VivaSchedule.objects.filter(
            examiner=request.user
        ).order_by("-id")

        serializer = VivaScheduleSerializer(vivas, many=True)

        return Response({
            "success": True,
            "count": vivas.count(),
            "data": serializer.data
        })


class VivaStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, viva_id):
        try:
            viva = VivaSchedule.objects.get(id=viva_id)
        except VivaSchedule.DoesNotExist:
            return Response({
                "success": False,
                "message": "Viva schedule not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Only assigned examiner OR super admin can update
        if request.user.role == "EXAMINER":
            if viva.examiner != request.user:
                return Response({
                    "success": False,
                    "message": "You can update only your assigned viva."
                }, status=status.HTTP_403_FORBIDDEN)

        elif request.user.role != "SUPER_ADMIN":
            return Response({
                "success": False,
                "message": "You do not have permission to perform this action."
            }, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get("status")

        if new_status not in ["SCHEDULED", "COMPLETED", "CANCELLED"]:
            return Response({
                "success": False,
                "message": "Invalid viva status."
            }, status=status.HTTP_400_BAD_REQUEST)

        viva.status = new_status
        viva.save()

        return Response({
            "success": True,
            "message": "Viva status updated successfully.",
            "data": VivaScheduleSerializer(viva).data
        })