from rest_framework import serializers
from .models import Company, IndustrialTraining


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = "__all__"


class IndustrialTrainingSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    company_name = serializers.CharField(source="company.name", read_only=True)
    supervisor_name = serializers.SerializerMethodField()

    class Meta:
        model = IndustrialTraining
        fields = "__all__"
        read_only_fields = ["student", "supervisor", "status", "supervisor_feedback"]

    def get_student_name(self, obj):
        if obj.student:
            return f"{obj.student.first_name} {obj.student.last_name}"
        return None

    def get_supervisor_name(self, obj):
        if obj.supervisor:
            return f"{obj.supervisor.first_name} {obj.supervisor.last_name}"
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["student"] = request.user
        return super().create(validated_data)


class TrainingStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["PENDING", "ONGOING", "APPROVED", "REJECTED", "COMPLETED"]
    )


class TrainingFeedbackSerializer(serializers.Serializer):
    supervisor_feedback = serializers.CharField()

from .models import TrainingFeedback


class TrainingFeedbackListSerializer(serializers.ModelSerializer):
    supervisor_name = serializers.SerializerMethodField()

    class Meta:
        model = TrainingFeedback
        fields = [
            "id",
            "training",
            "supervisor",
            "supervisor_name",
            "comment",
            "created_at",
        ]

    def get_supervisor_name(self, obj):
        return f"{obj.supervisor.first_name} {obj.supervisor.last_name}"


class TrainingFeedbackCreateSerializer(serializers.Serializer):
    comment = serializers.CharField()