from rest_framework import serializers

from .models import (
    Evaluation,
    EvaluationAuditLog,
)


RUBRIC_FIELD_LIMITS = {
    "proposal_problem_identification": 10,
    "proposal_literature_review": 10,
    "proposal_methodology": 10,

    "progress_implementation": 10,
    "progress_documentation": 10,
    "progress_presentation": 10,

    "viva_knowledge": 10,
    "viva_presentation": 10,
    "viva_question_answer": 10,
    "viva_confidence": 10,
}


SUMMARY_FIELD_LIMITS = {
    "proposal_marks": 30,
    "progress_marks": 30,
    "viva_marks": 40,
}


class EvaluationAuditLogSerializer(
    serializers.ModelSerializer
):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = EvaluationAuditLog

        fields = [
            "id",
            "action",
            "changed_by",
            "changed_by_name",
            "old_data",
            "new_data",
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


class EvaluationSerializer(
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

    team_name = serializers.CharField(
        source="project.team.name",
        read_only=True,
    )

    supervisor_name = serializers.SerializerMethodField()

    examiner_name = serializers.SerializerMethodField()

    is_locked = serializers.BooleanField(
        read_only=True,
    )

    audit_logs = EvaluationAuditLogSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Evaluation

        fields = [
            "id",

            "project",
            "project_title",
            "project_type",
            "team_name",
            "supervisor_name",

            "examiner",
            "examiner_name",

            "rubric_enabled",

            "proposal_problem_identification",
            "proposal_literature_review",
            "proposal_methodology",

            "progress_implementation",
            "progress_documentation",
            "progress_presentation",

            "viva_knowledge",
            "viva_presentation",
            "viva_question_answer",
            "viva_confidence",

            "proposal_marks",
            "progress_marks",
            "viva_marks",

            "remarks",

            "total_marks",
            "grade",
            "grade_point",
            "grade_definition",

            "published",
            "published_by",
            "published_at",
            "locked_at",
            "is_locked",

            "created_at",
            "updated_at",

            "audit_logs",
        ]

        read_only_fields = [
            "examiner",

            "total_marks",
            "grade",
            "grade_point",
            "grade_definition",

            "published",
            "published_by",
            "published_at",
            "locked_at",

            "created_at",
            "updated_at",
        ]

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

    def validate(self, attrs):
        instance = self.instance

        if (
            instance
            and instance.is_locked
        ):
            raise serializers.ValidationError(
                "Published evaluations are locked and cannot be edited."
            )

        incoming_keys = set(
            self.initial_data.keys()
        )

        rubric_keys = set(
            RUBRIC_FIELD_LIMITS.keys()
        )

        summary_keys = set(
            SUMMARY_FIELD_LIMITS.keys()
        )

        has_rubric_input = bool(
            incoming_keys & rubric_keys
        )

        has_summary_input = bool(
            incoming_keys & summary_keys
        )

        if has_rubric_input and has_summary_input:
            raise serializers.ValidationError(
                "Submit either detailed rubric marks or summary marks, not both."
            )

        if has_rubric_input:
            missing_fields = [
                field_name
                for field_name in rubric_keys
                if field_name not in incoming_keys
            ]

            if missing_fields:
                raise serializers.ValidationError({
                    "rubric": (
                        "All rubric fields are required. Missing: "
                        + ", ".join(
                            sorted(missing_fields)
                        )
                    )
                })

            attrs["rubric_enabled"] = True

            for field_name, maximum in (
                RUBRIC_FIELD_LIMITS.items()
            ):
                value = attrs.get(field_name)

                if value is None:
                    continue

                if value < 0 or value > maximum:
                    raise serializers.ValidationError({
                        field_name: (
                            f"Marks must be between 0 and {maximum}."
                        )
                    })

        else:
            attrs["rubric_enabled"] = False

            for field_name, maximum in (
                SUMMARY_FIELD_LIMITS.items()
            ):
                raw_value = self.initial_data.get(
                    field_name
                )

                if raw_value is None:
                    continue

                try:
                    numeric_value = float(
                        raw_value
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    raise serializers.ValidationError({
                        field_name: (
                            "A valid numeric mark is required."
                        )
                    })

                if (
                    numeric_value < 0
                    or numeric_value > maximum
                ):
                    raise serializers.ValidationError({
                        field_name: (
                            f"Marks must be between 0 and {maximum}."
                        )
                    })

                attrs[field_name] = raw_value

        remarks = str(
            attrs.get(
                "remarks",
                getattr(
                    instance,
                    "remarks",
                    "",
                ),
            )
            or ""
        ).strip()

        if not remarks:
            raise serializers.ValidationError({
                "remarks": (
                    "Evaluation remarks are required."
                )
            })

        attrs["remarks"] = remarks

        return attrs


class PublishResultSerializer(
    serializers.Serializer
):
    published = serializers.BooleanField()