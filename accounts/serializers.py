from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class LoginSerializer(serializers.Serializer):
    login_id = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        login_id = attrs.get("login_id")
        password = attrs.get("password")

        user = User.objects.filter(student_id=login_id).first()
        if not user:
            user = User.objects.filter(email=login_id).first()

        if not user or not user.check_password(password):
            raise serializers.ValidationError("Invalid login ID or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")

        attrs["user"] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "student_id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "is_first_login",
            "must_change_password",
            "is_active",
        ]


class FirstPasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")

        validate_password(attrs["new_password"])
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context["request"].user

        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError("Current password is incorrect.")

        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")

        validate_password(attrs["new_password"])
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self):
        token = RefreshToken(self.validated_data["refresh"])
        token.blacklist()


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "student_id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "password",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        role = attrs.get("role")

        if role == "STUDENT":
            if not attrs.get("student_id"):
                raise serializers.ValidationError({
                    "student_id": "Student ID is required for student."
                })
        else:
            if not attrs.get("email"):
                raise serializers.ValidationError({
                    "email": "Email is required for this role."
                })

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            created_by=request.user if request else None,
            **validated_data
        )
        return user
    
class UserListSerializer(serializers.ModelSerializer):
    created_by_email = serializers.CharField(
        source="created_by.email",
        read_only=True
    )

    class Meta:
        model = User
        fields = [
            "id",
            "student_id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "role",
            "is_active",
            "is_first_login",
            "must_change_password",
            "created_by_email",
            "created_at",
        ]


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "student_id",
            "phone",
            "role",
            "is_active",
        ]

    def validate(self, attrs):
        role = attrs.get("role", self.instance.role)

        if role == "STUDENT":
            if not attrs.get("student_id", self.instance.student_id):
                raise serializers.ValidationError({
                    "student_id": "Student ID is required for student."
                })
        else:
            if not attrs.get("email", self.instance.email):
                raise serializers.ValidationError({
                    "email": "Email is required for this role."
                })

        return attrs