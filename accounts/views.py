from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

from .serializers import (
    LoginSerializer,
    ProfileSerializer,
    FirstPasswordChangeSerializer,
    ChangePasswordSerializer,
    LogoutSerializer,
    CreateUserSerializer,
)
from .permissions import IsSuperAdmin
from .serializers import UserListSerializer


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "message": "Login successful.",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "force_password_change": user.must_change_password,
            "user": ProfileSerializer(user).data,
        })


class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "success": True,
            "data": ProfileSerializer(request.user).data
        })


class FirstPasswordChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FirstPasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.is_first_login = False
        user.must_change_password = False
        user.save()

        return Response({
            "success": True,
            "message": "Password changed successfully. You can now access dashboard."
        })


class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response({
            "success": True,
            "message": "Password changed successfully."
        })


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Logout successful."
        }, status=status.HTTP_200_OK)
    

class CreateUserAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def post(self, request):
        serializer = CreateUserSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "User created successfully.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    

class UserListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        users = User.objects.all().order_by("-id")
        serializer = UserListSerializer(users, many=True)

        return Response({
            "success": True,
            "count": users.count(),
            "data": serializer.data
        })


class UserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = UserListSerializer(user)

        return Response({
            "success": True,
            "data": serializer.data
        })
    

class UserStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "User not found."
            }, status=status.HTTP_404_NOT_FOUND)

        if user.role == "SUPER_ADMIN":
            return Response({
                "success": False,
                "message": "Super admin status cannot be changed."
            }, status=status.HTTP_400_BAD_REQUEST)

        is_active = request.data.get("is_active")

        if is_active is None:
            return Response({
                "success": False,
                "message": "is_active field is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        user.is_active = is_active
        user.save()

        return Response({
            "success": True,
            "message": "User status updated successfully.",
            "data": {
                "id": user.id,
                "email": user.email,
                "student_id": user.student_id,
                "role": user.role,
                "is_active": user.is_active
            }
        })


# temorary api for testing
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.models import User


class TemporaryCreateSuperAdminAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        first_name = request.data.get("first_name", "Super")
        last_name = request.data.get("last_name", "Admin")
        phone = request.data.get("phone", "01700000000")

        if User.objects.filter(email=email).exists():
            return Response({
                "success": False,
                "message": "User already exists."
                }, status=status.HTTP_400_BAD_REQUEST)

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role="SUPER_ADMIN",
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )

        user.set_password(password)
        user.save()

        return Response({
            "success": True,
            "message": "Super Admin created successfully.",
            "email": user.email,
            "role": user.role
        }, status=status.HTTP_201_CREATED)