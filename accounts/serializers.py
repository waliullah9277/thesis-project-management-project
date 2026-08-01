import os

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    ExaminerProfile,
    SEMESTER_TERM_CHOICES,
    StudentProfile,
    SupervisorProfile,
    User,
)


# =========================================================
# PROFILE HELPERS
# =========================================================


def get_student_profile(user):
    """
    Safely return a student's profile.
    Returns None if the profile does not exist.
    """

    try:
        return user.student_profile
    except StudentProfile.DoesNotExist:
        return None


def get_supervisor_profile(user):
    """
    Safely return a supervisor's profile.
    """

    try:
        return user.supervisor_profile
    except SupervisorProfile.DoesNotExist:
        return None


def get_examiner_profile(user):
    """
    Safely return an examiner's profile.
    """

    try:
        return user.examiner_profile
    except ExaminerProfile.DoesNotExist:
        return None


# =========================================================
# USER PROFILE REPRESENTATION MIXIN
# =========================================================


class UserProfileRepresentationMixin:
    """
    Adds role-specific profile data to serialized user responses.
    """

    def add_profile_data(self, representation, user):
        representation["department"] = ""
        representation["batch"] = ""
        representation["semester"] = ""
        representation["designation"] = ""

        representation["project_start_term"] = None
        representation["project_start_term_display"] = None
        representation["project_start_year"] = None
        representation["project_duration"] = 3

        representation["project_start_semester_label"] = None
        representation["project_end_semester"] = None
        representation["project_end_semester_label"] = None
        representation["project_semester_timeline"] = []

        if user.role == "STUDENT":
            profile = get_student_profile(user)

            if profile:
                representation["department"] = profile.department
                representation["batch"] = profile.batch
                representation["semester"] = profile.semester

                representation["project_start_term"] = (
                    profile.project_start_term
                )

                representation["project_start_term_display"] = (
                    profile.get_project_start_term_display()
                    if profile.project_start_term
                    else None
                )

                representation["project_start_year"] = (
                    profile.project_start_year
                )

                representation["project_duration"] = (
                    profile.project_duration
                )

                representation["project_start_semester_label"] = (
                    profile.project_start_semester_label
                )

                representation["project_end_semester"] = (
                    profile.project_end_semester
                )

                representation["project_end_semester_label"] = (
                    profile.project_end_semester_label
                )

                representation["project_semester_timeline"] = (
                    profile.project_semester_timeline
                )

        elif user.role == "SUPERVISOR":
            profile = get_supervisor_profile(user)

            if profile:
                representation["department"] = profile.department
                representation["designation"] = profile.designation

        elif user.role == "EXAMINER":
            profile = get_examiner_profile(user)

            if profile:
                representation["department"] = profile.department
                representation["designation"] = profile.designation

        return representation


# =========================================================
# LOGIN SERIALIZER
# =========================================================


class LoginSerializer(serializers.Serializer):
    login_id = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        login_id = str(
            attrs.get("login_id", "")
        ).strip()

        password = attrs.get("password")

        user = User.objects.filter(
            student_id=login_id,
        ).first()

        if not user:
            user = User.objects.filter(
                email__iexact=login_id,
            ).first()

        if not user:
            raise serializers.ValidationError({
                "login_id": (
                    "No account was found with this login ID."
                )
            })

        if not user.check_password(password):
            raise serializers.ValidationError({
                "password": (
                    "The password you entered is incorrect."
                )
            })

        if not user.is_active:
            raise serializers.ValidationError({
                "login_id": (
                    "This account is inactive. "
                    "Please contact the administrator."
                )
            })

        attrs["user"] = user

        return attrs


# =========================================================
# PROFILE SERIALIZER
# =========================================================


class ProfileSerializer(
    UserProfileRepresentationMixin,
    serializers.ModelSerializer,
):
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

    def to_representation(self, instance):
        representation = super().to_representation(
            instance
        )

        return self.add_profile_data(
            representation,
            instance,
        )


# =========================================================
# PASSWORD SERIALIZERS
# =========================================================


class FirstPasswordChangeSerializer(
    serializers.Serializer
):
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attrs):
        if (
            attrs["new_password"]
            != attrs["confirm_password"]
        ):
            raise serializers.ValidationError({
                "confirm_password": (
                    "Passwords do not match."
                )
            })

        validate_password(
            attrs["new_password"]
        )

        return attrs


class ChangePasswordSerializer(
    serializers.Serializer
):
    current_password = serializers.CharField(
        write_only=True,
    )

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    confirm_password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    def validate(self, attrs):
        user = self.context["request"].user

        if not user.check_password(
            attrs["current_password"]
        ):
            raise serializers.ValidationError({
                "current_password": (
                    "Current password is incorrect."
                )
            })

        if (
            attrs["new_password"]
            != attrs["confirm_password"]
        ):
            raise serializers.ValidationError({
                "confirm_password": (
                    "Passwords do not match."
                )
            })

        validate_password(
            attrs["new_password"],
            user=user,
        )

        return attrs


# =========================================================
# LOGOUT SERIALIZER
# =========================================================


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            RefreshToken(value)

        except Exception:
            raise serializers.ValidationError(
                "Invalid or expired refresh token."
            )

        return value

    def save(self):
        token = RefreshToken(
            self.validated_data["refresh"]
        )

        token.blacklist()


# =========================================================
# CREATE USER SERIALIZER
# =========================================================


class CreateUserSerializer(
    UserProfileRepresentationMixin,
    serializers.ModelSerializer,
):
    password = serializers.CharField(
        write_only=True,
        min_length=8,
    )

    department = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        default="",
    )

    batch = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        default="",
    )

    semester = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        default="",
    )

    designation = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        default="",
    )

    project_start_term = serializers.ChoiceField(
        choices=SEMESTER_TERM_CHOICES,
        write_only=True,
        required=False,
        allow_null=True,
    )

    project_start_year = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        min_value=2000,
        max_value=2200,
    )

    project_duration = serializers.IntegerField(
        write_only=True,
        required=False,
        default=3,
        min_value=1,
        max_value=12,
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
            "password",

            "department",
            "batch",
            "semester",
            "designation",

            "project_start_term",
            "project_start_year",
            "project_duration",
        ]

        read_only_fields = [
            "id",
        ]

        extra_kwargs = {
            "student_id": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
            "email": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
            "last_name": {
                "required": False,
                "allow_blank": True,
            },
            "phone": {
                "required": False,
                "allow_blank": True,
            },
        }

    def validate(self, attrs):
        role = attrs.get("role")

        student_id = attrs.get(
            "student_id"
        )

        email = attrs.get("email")

        project_start_term = attrs.get(
            "project_start_term"
        )

        project_start_year = attrs.get(
            "project_start_year"
        )

        if role == "STUDENT":
            if not student_id:
                raise serializers.ValidationError({
                    "student_id": (
                        "Student ID is required for a student."
                    )
                })

            if not project_start_term:
                raise serializers.ValidationError({
                    "project_start_term": (
                        "Project start semester is required."
                    )
                })

            if project_start_year is None:
                raise serializers.ValidationError({
                    "project_start_year": (
                        "Project start year is required."
                    )
                })

            if User.objects.filter(
                student_id=student_id,
            ).exists():
                raise serializers.ValidationError({
                    "student_id": (
                        "A user with this student ID "
                        "already exists."
                    )
                })

        else:
            if not email:
                raise serializers.ValidationError({
                    "email": (
                        "Email is required for this user role."
                    )
                })

            if User.objects.filter(
                email__iexact=email,
            ).exists():
                raise serializers.ValidationError({
                    "email": (
                        "A user with this email address "
                        "already exists."
                    )
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get(
            "request"
        )

        password = validated_data.pop(
            "password"
        )

        department = validated_data.pop(
            "department",
            "",
        )

        batch = validated_data.pop(
            "batch",
            "",
        )

        semester = validated_data.pop(
            "semester",
            "",
        )

        designation = validated_data.pop(
            "designation",
            "",
        )

        project_start_term = validated_data.pop(
            "project_start_term",
            None,
        )

        project_start_year = validated_data.pop(
            "project_start_year",
            None,
        )

        project_duration = validated_data.pop(
            "project_duration",
            3,
        )

        role = validated_data.get(
            "role"
        )

        if role == "STUDENT":
            validated_data["email"] = None

        else:
            validated_data["student_id"] = None

        created_by = None

        if (
            request
            and request.user.is_authenticated
        ):
            created_by = request.user

        user = User.objects.create_user(
            password=password,
            created_by=created_by,
            **validated_data,
        )

        if role == "STUDENT":
            StudentProfile.objects.create(
                user=user,
                department=department,
                batch=batch,
                semester=semester,
                project_start_term=project_start_term,
                project_start_year=project_start_year,
                project_duration=project_duration,
            )

        elif role == "SUPERVISOR":
            SupervisorProfile.objects.create(
                user=user,
                department=department,
                designation=designation,
            )

        elif role == "EXAMINER":
            ExaminerProfile.objects.create(
                user=user,
                department=department,
                designation=designation,
            )

        return user

    def to_representation(self, instance):
        representation = {
            "id": instance.id,
            "student_id": instance.student_id,
            "email": instance.email,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "phone": instance.phone,
            "role": instance.role,
            "is_active": instance.is_active,
            "is_first_login": instance.is_first_login,
            "must_change_password": (
                instance.must_change_password
            ),
        }

        return self.add_profile_data(
            representation,
            instance,
        )


# =========================================================
# USER LIST SERIALIZER
# =========================================================


class UserListSerializer(
    UserProfileRepresentationMixin,
    serializers.ModelSerializer,
):
    created_by_email = (
        serializers.SerializerMethodField()
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
            "updated_at",
        ]

    def get_created_by_email(self, obj):
        if not obj.created_by:
            return None

        return (
            obj.created_by.email
            or obj.created_by.student_id
        )

    def to_representation(self, instance):
        representation = super().to_representation(
            instance
        )

        return self.add_profile_data(
            representation,
            instance,
        )


# =========================================================
# ADMIN USER UPDATE SERIALIZER
# =========================================================


class AdminUserUpdateSerializer(
    UserProfileRepresentationMixin,
    serializers.ModelSerializer,
):
    department = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    batch = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    semester = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    designation = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )

    project_start_term = serializers.ChoiceField(
        choices=SEMESTER_TERM_CHOICES,
        write_only=True,
        required=False,
        allow_null=True,
    )

    project_start_year = serializers.IntegerField(
        write_only=True,
        required=False,
        allow_null=True,
        min_value=2000,
        max_value=2200,
    )

    project_duration = serializers.IntegerField(
        write_only=True,
        required=False,
        min_value=1,
        max_value=12,
    )

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

            "department",
            "batch",
            "semester",
            "designation",

            "project_start_term",
            "project_start_year",
            "project_duration",
        ]

        extra_kwargs = {
            "student_id": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
            "email": {
                "required": False,
                "allow_null": True,
                "allow_blank": True,
            },
            "last_name": {
                "required": False,
                "allow_blank": True,
            },
            "phone": {
                "required": False,
                "allow_blank": True,
            },
        }

    def validate(self, attrs):
        new_role = attrs.get(
            "role",
            self.instance.role,
        )

        student_id = attrs.get(
            "student_id",
            self.instance.student_id,
        )

        email = attrs.get(
            "email",
            self.instance.email,
        )

        if new_role == "STUDENT":
            if not student_id:
                raise serializers.ValidationError({
                    "student_id": (
                        "Student ID is required for a student."
                    )
                })

            duplicate_exists = (
                User.objects.filter(
                    student_id=student_id,
                )
                .exclude(
                    id=self.instance.id,
                )
                .exists()
            )

            if duplicate_exists:
                raise serializers.ValidationError({
                    "student_id": (
                        "A user with this student ID "
                        "already exists."
                    )
                })

            current_profile = (
                get_student_profile(
                    self.instance
                )
            )

            current_term = (
                current_profile.project_start_term
                if current_profile
                else None
            )

            current_year = (
                current_profile.project_start_year
                if current_profile
                else None
            )

            final_term = attrs.get(
                "project_start_term",
                current_term,
            )

            final_year = attrs.get(
                "project_start_year",
                current_year,
            )

            if not final_term:
                raise serializers.ValidationError({
                    "project_start_term": (
                        "Project start semester is required."
                    )
                })

            if final_year is None:
                raise serializers.ValidationError({
                    "project_start_year": (
                        "Project start year is required."
                    )
                })

        else:
            if not email:
                raise serializers.ValidationError({
                    "email": (
                        "Email is required for this user role."
                    )
                })

            duplicate_exists = (
                User.objects.filter(
                    email__iexact=email,
                )
                .exclude(
                    id=self.instance.id,
                )
                .exists()
            )

            if duplicate_exists:
                raise serializers.ValidationError({
                    "email": (
                        "A user with this email address "
                        "already exists."
                    )
                })

        return attrs

    @transaction.atomic
    def update(
        self,
        instance,
        validated_data,
    ):
        department_supplied = (
            "department" in validated_data
        )

        batch_supplied = (
            "batch" in validated_data
        )

        semester_supplied = (
            "semester" in validated_data
        )

        designation_supplied = (
            "designation" in validated_data
        )

        start_term_supplied = (
            "project_start_term"
            in validated_data
        )

        start_year_supplied = (
            "project_start_year"
            in validated_data
        )

        duration_supplied = (
            "project_duration"
            in validated_data
        )

        department = validated_data.pop(
            "department",
            "",
        )

        batch = validated_data.pop(
            "batch",
            "",
        )

        semester = validated_data.pop(
            "semester",
            "",
        )

        designation = validated_data.pop(
            "designation",
            "",
        )

        project_start_term = validated_data.pop(
            "project_start_term",
            None,
        )

        project_start_year = validated_data.pop(
            "project_start_year",
            None,
        )

        project_duration = validated_data.pop(
            "project_duration",
            3,
        )

        old_role = instance.role

        new_role = validated_data.get(
            "role",
            old_role,
        )

        if new_role == "STUDENT":
            validated_data["email"] = None

        else:
            validated_data["student_id"] = None

        for field, value in validated_data.items():
            setattr(
                instance,
                field,
                value,
            )

        instance.save()

        if old_role != new_role:
            StudentProfile.objects.filter(
                user=instance,
            ).delete()

            SupervisorProfile.objects.filter(
                user=instance,
            ).delete()

            ExaminerProfile.objects.filter(
                user=instance,
            ).delete()

        if new_role == "STUDENT":
            profile, _ = (
                StudentProfile.objects.get_or_create(
                    user=instance,
                    defaults={
                        "project_duration": 3,
                    },
                )
            )

            if department_supplied:
                profile.department = department

            if batch_supplied:
                profile.batch = batch

            if semester_supplied:
                profile.semester = semester

            if start_term_supplied:
                profile.project_start_term = (
                    project_start_term
                )

            if start_year_supplied:
                profile.project_start_year = (
                    project_start_year
                )

            if duration_supplied:
                profile.project_duration = (
                    project_duration
                )

            profile.save()

        elif new_role == "SUPERVISOR":
            profile, _ = (
                SupervisorProfile.objects.get_or_create(
                    user=instance
                )
            )

            if department_supplied:
                profile.department = department

            if designation_supplied:
                profile.designation = designation

            profile.save()

        elif new_role == "EXAMINER":
            profile, _ = (
                ExaminerProfile.objects.get_or_create(
                    user=instance
                )
            )

            if department_supplied:
                profile.department = department

            if designation_supplied:
                profile.designation = designation

            profile.save()

        return instance

    def to_representation(self, instance):
        representation = {
            "id": instance.id,
            "student_id": instance.student_id,
            "email": instance.email,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "phone": instance.phone,
            "role": instance.role,
            "is_active": instance.is_active,
        }

        return self.add_profile_data(
            representation,
            instance,
        )


# =========================================================
# BULK USER IMPORT FILE SERIALIZER
# =========================================================


class BulkUserImportSerializer(
    serializers.Serializer
):
    file = serializers.FileField(
        required=True,
        allow_null=False,
    )

    def validate_file(self, value):
        """
        Allow only .xlsx Excel files up to 5 MB.
        """

        extension = os.path.splitext(
            value.name
        )[1].lower()

        if extension != ".xlsx":
            raise serializers.ValidationError(
                "Only .xlsx Excel files are allowed."
            )

        maximum_size = 5 * 1024 * 1024

        if value.size > maximum_size:
            raise serializers.ValidationError(
                "Excel file size cannot exceed 5 MB."
            )

        return value