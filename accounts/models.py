from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from .managers import UserManager


ROLE_CHOICES = (
    ("SUPER_ADMIN", "Super Admin"),
    ("STUDENT", "Student"),
    ("SUPERVISOR", "Supervisor"),
    ("EXAMINER", "Examiner"),
)


class User(AbstractBaseUser, PermissionsMixin):
    student_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    is_first_login = models.BooleanField(default=True)
    must_change_password = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_users"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    def __str__(self):
        if self.role == "STUDENT":
            return self.student_id or "Student"
        return self.email or "User"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    department = models.CharField(max_length=100, blank=True)
    batch = models.CharField(max_length=50, blank=True)
    semester = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.user.student_id or "Student Profile"


class SupervisorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="supervisor_profile")
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.email or "Supervisor Profile"


class ExaminerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="examiner_profile")
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.email or "Examiner Profile"