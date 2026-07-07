from rest_framework import serializers
from .models import Evaluation


class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = [
            "id",
            "project",
            "examiner",
            "proposal_marks",
            "progress_marks",
            "viva_marks",
            "remarks",
            "total_marks",
            "grade",
            "published",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "examiner",
            "total_marks",
            "grade",
            "published",
            "created_at",
            "updated_at",
        ]


class PublishResultSerializer(serializers.Serializer):
    published = serializers.BooleanField()