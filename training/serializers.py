from pathlib import Path

from rest_framework import serializers

from .models import (
    Company,
    IndustrialTraining,
    TrainingFeedback,
    TrainingStatusHistory,
)


ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}


class CompanySerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "address",
            "contact_person",
            "email",
            "phone",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "created_at",
            "updated_at",
        ]

    def validate_name(self, value):
        value = str(value or "").strip()

        if not value:
            raise serializers.ValidationError(
                "Company name is required."
            )

        queryset = Company.objects.filter(
            name__iexact=value,
        )

        if self.instance:
            queryset = queryset.exclude(
                id=self.instance.id,
            )

        if queryset.exists():
            raise serializers.ValidationError(
                "A company with this name already exists."
            )

        return value


class TrainingFeedbackListSerializer(
    serializers.ModelSerializer
):
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

        read_only_fields = fields

    def get_supervisor_name(self, obj):
        full_name = (
            f"{obj.supervisor.first_name or ''} "
            f"{obj.supervisor.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.supervisor.email
            or "Supervisor"
        )


class TrainingStatusHistorySerializer(
    serializers.ModelSerializer
):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = TrainingStatusHistory

        fields = [
            "id",
            "previous_status",
            "new_status",
            "reason",
            "changed_by",
            "changed_by_name",
            "created_at",
        ]

        read_only_fields = fields

    def get_changed_by_name(self, obj):
        if not obj.changed_by:
            return None

        full_name = (
            f"{obj.changed_by.first_name or ''} "
            f"{obj.changed_by.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.changed_by.email
            or obj.changed_by.student_id
            or "User"
        )


class IndustrialTrainingSerializer(
    serializers.ModelSerializer
):
    student_name = serializers.SerializerMethodField()

    student_id_number = serializers.CharField(
        source="student.student_id",
        read_only=True,
    )

    company_name = serializers.CharField(
        source="company.name",
        read_only=True,
    )

    supervisor_name = serializers.SerializerMethodField()

    status_display = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    offer_letter_url = serializers.SerializerMethodField()

    final_report_url = serializers.SerializerMethodField()

    feedbacks = TrainingFeedbackListSerializer(
        many=True,
        read_only=True,
    )

    status_history = TrainingStatusHistorySerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = IndustrialTraining

        fields = [
            "id",
            "student",
            "student_name",
            "student_id_number",
            "company",
            "company_name",
            "supervisor",
            "supervisor_name",
            "title",
            "designation",
            "description",
            "start_date",
            "end_date",
            "status",
            "status_display",
            "status_reason",
            "offer_letter",
            "offer_letter_url",
            "final_report",
            "final_report_url",
            "company_feedback",
            "supervisor_feedback",
            "approved_by",
            "approved_at",
            "completed_at",
            "created_at",
            "updated_at",
            "feedbacks",
            "status_history",
        ]

        read_only_fields = [
            "student",
            "supervisor",
            "status",
            "status_reason",
            "supervisor_feedback",
            "approved_by",
            "approved_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        start_date = attrs.get(
            "start_date",
            getattr(
                self.instance,
                "start_date",
                None,
            ),
        )

        end_date = attrs.get(
            "end_date",
            getattr(
                self.instance,
                "end_date",
                None,
            ),
        )

        if (
            start_date
            and end_date
            and end_date < start_date
        ):
            raise serializers.ValidationError({
                "end_date": (
                    "End date cannot be earlier than start date."
                )
            })

        return attrs

    def validate_offer_letter(self, file):
        return self._validate_document(
            file,
            "Offer letter",
        )

    def validate_final_report(self, file):
        return self._validate_document(
            file,
            "Final report",
        )

    def _validate_document(
        self,
        file,
        label,
    ):
        if not file:
            return file

        extension = Path(
            file.name
        ).suffix.lower()

        if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
            raise serializers.ValidationError(
                f"{label} must be PDF, DOC or DOCX."
            )

        if file.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                f"{label} cannot be larger than 10 MB."
            )

        return file

    def get_student_name(self, obj):
        full_name = (
            f"{obj.student.first_name or ''} "
            f"{obj.student.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.student.student_id
            or "Student"
        )

    def get_supervisor_name(self, obj):
        if not obj.supervisor:
            return None

        full_name = (
            f"{obj.supervisor.first_name or ''} "
            f"{obj.supervisor.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.supervisor.email
            or "Supervisor"
        )

    def get_offer_letter_url(self, obj):
        if not obj.offer_letter:
            return None

        request = self.context.get(
            "request"
        )

        url = obj.offer_letter.url

        return (
            request.build_absolute_uri(url)
            if request
            else url
        )

    def get_final_report_url(self, obj):
        if not obj.final_report:
            return None

        request = self.context.get(
            "request"
        )

        url = obj.final_report.url

        return (
            request.build_absolute_uri(url)
            if request
            else url
        )

    def create(self, validated_data):
        request = self.context.get(
            "request"
        )

        validated_data["student"] = (
            request.user
        )

        return super().create(
            validated_data
        )


class TrainingStatusUpdateSerializer(
    serializers.Serializer
):
    status = serializers.ChoiceField(
        choices=[
            "PENDING",
            "APPROVED",
            "ONGOING",
            "COMPLETED",
            "REJECTED",
            "CANCELLED",
        ]
    )

    reason = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate(self, attrs):
        status_value = attrs[
            "status"
        ]

        reason = str(
            attrs.get(
                "reason",
                "",
            )
            or ""
        ).strip()

        if (
            status_value
            in {
                "REJECTED",
                "CANCELLED",
            }
            and not reason
        ):
            raise serializers.ValidationError({
                "reason": (
                    "A reason is required for rejected or cancelled status."
                )
            })

        attrs["reason"] = reason

        return attrs


class AssignTrainingSupervisorSerializer(
    serializers.Serializer
):
    supervisor_id = serializers.IntegerField()


class TrainingFeedbackCreateSerializer(
    serializers.Serializer
):
    comment = serializers.CharField(
        max_length=3000,
    )

    def validate_comment(self, value):
        value = str(value or "").strip()

        if not value:
            raise serializers.ValidationError(
                "Feedback comment is required."
            )

        return value