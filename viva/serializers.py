from rest_framework import serializers

from accounts.models import User
from projects.models import Project
from projects.serializers import ProjectSerializer
from .models import VivaSchedule


class VivaScheduleSerializer(serializers.ModelSerializer):
    project_details = ProjectSerializer(source="project", read_only=True)

    class Meta:
        model = VivaSchedule
        fields = [
            "id",
            "project",
            "project_details",
            "examiner",
            "date",
            "time",
            "room",
            "status",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class AssignExaminerSerializer(serializers.Serializer):
    examiner_id = serializers.IntegerField()

    def validate_examiner_id(self, value):
        try:
            User.objects.get(id=value, role="EXAMINER")
        except User.DoesNotExist:
            raise serializers.ValidationError("Valid examiner not found.")
        return value