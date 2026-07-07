from rest_framework import serializers
from django.utils import timezone

from .models import ProgressReport


class ProgressReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressReport
        fields = [
            "id",
            "project",
            "submitted_by",
            "title",
            "description",
            "file",
            "status",
            "supervisor_comment",
            "submitted_at",
            "reviewed_at",
        ]
        read_only_fields = [
            "submitted_by",
            "status",
            "supervisor_comment",
            "submitted_at",
            "reviewed_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        return ProgressReport.objects.create(
            submitted_by=request.user,
            **validated_data
        )


class ProgressReportReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["REVIEWED", "NEEDS_IMPROVEMENT"]
    )
    supervisor_comment = serializers.CharField()