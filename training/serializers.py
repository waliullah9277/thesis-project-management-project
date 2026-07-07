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
        fields = [
            "id",
            "student",
            "student_name",
            "company",
            "company_name",
            "supervisor",
            "supervisor_name",
            "title",
            "description",
            "start_date",
            "end_date",
            "status",
            "final_report",
            "company_feedback",
            "supervisor_feedback",
            "created_at",
        ]
        read_only_fields = [
            "student",
            "status",
            "company_feedback",
            "supervisor_feedback",
            "created_at",
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_supervisor_name(self, obj):
        if obj.supervisor:
            return f"{obj.supervisor.first_name} {obj.supervisor.last_name}"
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        return IndustrialTraining.objects.create(
            student=request.user,
            **validated_data
        )


class TrainingStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["PENDING", "ONGOING", "COMPLETED", "CANCELLED"]
    )


class TrainingFeedbackSerializer(serializers.Serializer):
    supervisor_feedback = serializers.CharField()