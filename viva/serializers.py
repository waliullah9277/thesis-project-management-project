from rest_framework import serializers

from accounts.models import User
from projects.serializers import ProjectSerializer

from .models import VivaSchedule


class VivaScheduleSerializer(
    serializers.ModelSerializer
):
    project_title = serializers.CharField(
        source="project.title",
        read_only=True,
    )

    project_type = serializers.CharField(
        source="project.project_type",
        read_only=True,
    )

    project_type_display = serializers.CharField(
        source="project.get_project_type_display",
        read_only=True,
    )

    team_name = serializers.CharField(
        source="project.team.name",
        read_only=True,
    )

    supervisor_name = serializers.SerializerMethodField()

    examiner_name = serializers.SerializerMethodField()

    project_details = ProjectSerializer(
        source="project",
        read_only=True,
    )

    class Meta:
        model = VivaSchedule

        fields = [
            "id",

            "project",
            "project_title",
            "project_type",
            "project_type_display",
            "team_name",
            "supervisor_name",
            "project_details",

            "date",
            "time",
            "room",

            "examiner",
            "examiner_name",

            "status",
            "created_at",
        ]

        read_only_fields = [
            "created_at",
        ]

    def validate_examiner(self, value):
        if value is None:
            return value

        if value.role != "EXAMINER":
            raise serializers.ValidationError(
                "The selected user must be an examiner."
            )

        if not value.is_active:
            raise serializers.ValidationError(
                "The selected examiner account is inactive."
            )

        return value

    def get_examiner_name(self, obj):
        if not obj.examiner:
            return None

        full_name = (
            f"{obj.examiner.first_name or ''} "
            f"{obj.examiner.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.examiner.email
            or "Examiner"
        )

    def get_supervisor_name(self, obj):
        supervisor = obj.project.supervisor

        if not supervisor:
            return None

        full_name = (
            f"{supervisor.first_name or ''} "
            f"{supervisor.last_name or ''}"
        ).strip()

        return (
            full_name
            or supervisor.email
            or "Supervisor"
        )


class AssignExaminerSerializer(
    serializers.Serializer
):
    examiner_id = serializers.IntegerField()

    def validate_examiner_id(self, value):
        try:
            examiner = User.objects.get(
                id=value,
                role="EXAMINER",
                is_active=True,
            )

        except User.DoesNotExist:
            raise serializers.ValidationError(
                "An active and valid examiner was not found."
            )

        return examiner.id