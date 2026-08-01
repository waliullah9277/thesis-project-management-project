from django.contrib import admin

from .models import (
    ExaminerProfile,
    StudentProfile,
    SupervisorProfile,
    User,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "display_login_id",
        "full_name",
        "role",
        "is_active",
        "is_staff",
        "created_at",
    ]

    list_filter = [
        "role",
        "is_active",
        "is_staff",
        "is_first_login",
        "must_change_password",
    ]

    search_fields = [
        "student_id",
        "email",
        "first_name",
        "last_name",
        "phone",
    ]

    ordering = [
        "-id",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
        "last_login",
    ]

    fieldsets = (
        (
            "Login Information",
            {
                "fields": (
                    "student_id",
                    "email",
                    "password",
                )
            },
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "phone",
                    "role",
                )
            },
        ),
        (
            "Account Status",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "is_first_login",
                    "must_change_password",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_by",
                    "last_login",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def display_login_id(self, obj):
        return obj.student_id or obj.email or "-"

    display_login_id.short_description = "Login ID"

    def full_name(self, obj):
        return (
            f"{obj.first_name or ''} "
            f"{obj.last_name or ''}"
        ).strip() or "-"

    full_name.short_description = "Full Name"


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "student_id",
        "student_name",
        "department",
        "batch",
        "project_start",
        "project_end",
        "project_duration",
    ]

    list_filter = [
        "department",
        "project_start_term",
        "project_start_year",
        "project_duration",
    ]

    search_fields = [
        "user__student_id",
        "user__first_name",
        "user__last_name",
        "department",
        "batch",
    ]

    ordering = [
        "-id",
    ]

    def student_id(self, obj):
        return obj.user.student_id or "-"

    student_id.short_description = "Student ID"

    def student_name(self, obj):
        return (
            f"{obj.user.first_name or ''} "
            f"{obj.user.last_name or ''}"
        ).strip() or "-"

    student_name.short_description = "Student Name"

    def project_start(self, obj):
        return obj.project_start_semester_label or "-"

    project_start.short_description = "Project Start"

    def project_end(self, obj):
        return obj.project_end_semester_label or "-"

    project_end.short_description = "Project End"


@admin.register(SupervisorProfile)
class SupervisorProfileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "supervisor_name",
        "email",
        "department",
        "designation",
    ]

    list_filter = [
        "department",
        "designation",
    ]

    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "department",
        "designation",
    ]

    ordering = [
        "-id",
    ]

    def supervisor_name(self, obj):
        return (
            f"{obj.user.first_name or ''} "
            f"{obj.user.last_name or ''}"
        ).strip() or "-"

    supervisor_name.short_description = "Supervisor Name"

    def email(self, obj):
        return obj.user.email or "-"

    email.short_description = "Email"


@admin.register(ExaminerProfile)
class ExaminerProfileAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "examiner_name",
        "email",
        "department",
        "designation",
    ]

    list_filter = [
        "department",
        "designation",
    ]

    search_fields = [
        "user__email",
        "user__first_name",
        "user__last_name",
        "department",
        "designation",
    ]

    ordering = [
        "-id",
    ]

    def examiner_name(self, obj):
        return (
            f"{obj.user.first_name or ''} "
            f"{obj.user.last_name or ''}"
        ).strip() or "-"

    examiner_name.short_description = "Examiner Name"

    def email(self, obj):
        return obj.user.email or "-"

    email.short_description = "Email"