from rest_framework import serializers

from accounts.models import User
from projects.models import Project
from projects.serializers import ProjectSerializer
from .models import VivaSchedule


class VivaScheduleSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)
    project_type = serializers.CharField(source="project.project_type", read_only=True)
    team_name = serializers.CharField(source="project.team.name", read_only=True)
    examiner_name = serializers.SerializerMethodField()

    class Meta:
        model = VivaSchedule
        fields = [
            "id",
            "project",
            "project_title",
            "project_type",
            "team_name",
            "date",
            "time",
            "room",
            "examiner",
            "examiner_name",
            "status",
        ]

    def get_examiner_name(self, obj):
        if obj.examiner:
            return f"{obj.examiner.first_name} {obj.examiner.last_name}"
        return None

class AssignExaminerSerializer(serializers.Serializer):
    examiner_id = serializers.IntegerField()

    def validate_examiner_id(self, value):
        try:
            User.objects.get(id=value, role="EXAMINER")
        except User.DoesNotExist:
            raise serializers.ValidationError("Valid examiner not found.")
        return value