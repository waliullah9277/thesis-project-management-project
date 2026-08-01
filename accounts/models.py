from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models

from .managers import UserManager
from .semester_utils import get_end_semester, get_semester_timeline


ROLE_CHOICES = (
    ("SUPER_ADMIN", "Super Admin"),
    ("STUDENT", "Student"),
    ("SUPERVISOR", "Supervisor"),
    ("EXAMINER", "Examiner"),
)


SEMESTER_TERM_CHOICES = (
    ("SPRING", "Spring"),
    ("SUMMER", "Summer"),
    ("FALL", "Fall"),
)


class User(AbstractBaseUser, PermissionsMixin):
    student_id = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )

    email = models.EmailField(
        unique=True,
        null=True,
        blank=True,
    )

    first_name = models.CharField(
        max_length=100,
    )

    last_name = models.CharField(
        max_length=100,
        blank=True,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
    )

    is_active = models.BooleanField(
        default=True,
    )

    is_staff = models.BooleanField(
        default=False,
    )

    is_first_login = models.BooleanField(
        default=True,
    )

    must_change_password = models.BooleanField(
        default=True,
    )

    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    def clean(self):
        errors = {}

        if self.role == "STUDENT":
            if not self.student_id:
                errors["student_id"] = "Student ID is required for a student."

        elif self.role in {"SUPER_ADMIN", "SUPERVISOR", "EXAMINER"}:
            if not self.email:
                errors["email"] = "Email is required for this user role."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        if self.role == "STUDENT":
            return self.student_id or "Student"

        return self.email or "User"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )

    department = models.CharField(
        max_length=100,
        blank=True,
    )

    batch = models.CharField(
        max_length=50,
        blank=True,
    )

    # Existing field kept for backward compatibility.
    semester = models.CharField(
        max_length=50,
        blank=True,
    )

    project_start_term = models.CharField(
        max_length=10,
        choices=SEMESTER_TERM_CHOICES,
        null=True,
        blank=True,
    )

    project_start_year = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    project_duration = models.PositiveSmallIntegerField(
        default=3,
        help_text="Total number of semesters for the project or thesis.",
    )

    class Meta:
        ordering = ["-id"]

    def clean(self):
        errors = {}

        if self.user_id and self.user.role != "STUDENT":
            errors["user"] = (
                "StudentProfile can only be assigned to a student."
            )

        has_start_term = bool(self.project_start_term)
        has_start_year = self.project_start_year is not None

        if has_start_term != has_start_year:
            if not has_start_term:
                errors["project_start_term"] = (
                    "Project start semester is required when a start year "
                    "is provided."
                )

            if not has_start_year:
                errors["project_start_year"] = (
                    "Project start year is required when a start semester "
                    "is provided."
                )

        if self.project_duration is None:
            errors["project_duration"] = (
                "Project duration is required."
            )

        elif self.project_duration < 1:
            errors["project_duration"] = (
                "Project duration must be at least 1 semester."
            )

        elif self.project_duration > 12:
            errors["project_duration"] = (
                "Project duration cannot be more than 12 semesters."
            )

        if self.project_start_year is not None:
            if (
                self.project_start_year < 2000
                or self.project_start_year > 2200
            ):
                errors["project_start_year"] = (
                    "Project start year must be between 2000 and 2200."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def has_project_semester(self):
        return bool(
            self.project_start_term
            and self.project_start_year is not None
        )

    @property
    def project_start_semester_label(self):
        if not self.has_project_semester:
            return None

        return (
            f"{self.get_project_start_term_display()} "
            f"{self.project_start_year}"
        )

    @property
    def project_semester_timeline(self):
        if not self.has_project_semester:
            return []

        return get_semester_timeline(
            start_term=self.project_start_term,
            start_year=self.project_start_year,
            duration=self.project_duration,
        )

    @property
    def project_end_semester(self):
        if not self.has_project_semester:
            return None

        return get_end_semester(
            start_term=self.project_start_term,
            start_year=self.project_start_year,
            duration=self.project_duration,
        )

    @property
    def project_end_semester_label(self):
        end_semester = self.project_end_semester

        if not end_semester:
            return None

        return end_semester["label"]

    def __str__(self):
        return self.user.student_id or "Student Profile"


class SupervisorProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="supervisor_profile",
    )

    department = models.CharField(
        max_length=100,
        blank=True,
    )

    designation = models.CharField(
        max_length=100,
        blank=True,
    )

    def clean(self):
        if self.user_id and self.user.role != "SUPERVISOR":
            raise ValidationError({
                "user": (
                    "SupervisorProfile can only be assigned "
                    "to a supervisor."
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.email or "Supervisor Profile"


class ExaminerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="examiner_profile",
    )

    department = models.CharField(
        max_length=100,
        blank=True,
    )

    designation = models.CharField(
        max_length=100,
        blank=True,
    )

    def clean(self):
        if self.user_id and self.user.role != "EXAMINER":
            raise ValidationError({
                "user": (
                    "ExaminerProfile can only be assigned "
                    "to an examiner."
                )
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.email or "Examiner Profile"