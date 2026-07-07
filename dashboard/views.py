from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import (
    IsSuperAdmin,
    IsStudent,
    IsSupervisor,
    IsExaminer,
)


class StudentDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudent]

    def get(self, request):
        return Response({
            "success": True,
            "dashboard": "student",
            "message": "Welcome to Student Dashboard",
            "user": {
                "id": request.user.id,
                "student_id": request.user.student_id,
                "name": f"{request.user.first_name} {request.user.last_name}",
                "role": request.user.role,
            }
        })


class SupervisorDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSupervisor]

    def get(self, request):
        return Response({
            "success": True,
            "dashboard": "supervisor",
            "message": "Welcome to Supervisor Dashboard",
            "user": {
                "id": request.user.id,
                "email": request.user.email,
                "name": f"{request.user.first_name} {request.user.last_name}",
                "role": request.user.role,
            }
        })


class ExaminerDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsExaminer]

    def get(self, request):
        return Response({
            "success": True,
            "dashboard": "examiner",
            "message": "Welcome to Examiner Dashboard",
            "user": {
                "id": request.user.id,
                "email": request.user.email,
                "name": f"{request.user.first_name} {request.user.last_name}",
                "role": request.user.role,
            }
        })


class AdminDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        return Response({
            "success": True,
            "dashboard": "super_admin",
            "message": "Welcome to Super Admin Dashboard",
            "user": {
                "id": request.user.id,
                "email": request.user.email,
                "name": f"{request.user.first_name} {request.user.last_name}",
                "role": request.user.role,
            }
        })