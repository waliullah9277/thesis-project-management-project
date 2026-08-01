from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import User
from projects.models import Project


GRADE_CHOICES = (
    ("A+", "A+"),
    ("A", "A"),
    ("A-", "A-"),
    ("B+", "B+"),
    ("B", "B"),
    ("B-", "B-"),
    ("C+", "C+"),
    ("C", "C"),
    ("D", "D"),
    ("F", "F"),
)


AUDIT_ACTION_CHOICES = (
    ("CREATED", "Created"),
    ("UPDATED", "Updated"),
    ("PUBLISHED", "Published"),
    ("UNPUBLISHED", "Unpublished"),
)


class Evaluation(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="evaluation",
    )

    examiner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluations",
        limit_choices_to={"role": "EXAMINER"},
    )

    # =====================================================
    # LEGACY / SUMMARY MARKS
    #
    # These fields are retained so the existing frontend and
    # previously saved records continue to work.
    # =====================================================

    proposal_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    progress_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    viva_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    # =====================================================
    # PROFESSIONAL RUBRIC BREAKDOWN
    # =====================================================

    rubric_enabled = models.BooleanField(
        default=False,
        help_text=(
            "When enabled, proposal, progress and viva totals are "
            "calculated from the detailed rubric fields."
        ),
    )

    # Proposal = 30
    proposal_problem_identification = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    proposal_literature_review = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    proposal_methodology = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    # Progress = 30
    progress_implementation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    progress_documentation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    progress_presentation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    # Viva = 40
    viva_knowledge = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    viva_presentation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    viva_question_answer = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    viva_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    remarks = models.TextField(
        blank=True,
    )

    total_marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    grade = models.CharField(
        max_length=10,
        choices=GRADE_CHOICES,
        blank=True,
    )

    grade_point = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
    )

    grade_definition = models.CharField(
        max_length=30,
        blank=True,
    )

    published = models.BooleanField(
        default=False,
    )

    published_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="published_evaluations",
        limit_choices_to={"role": "SUPER_ADMIN"},
    )

    published_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    locked_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
            "-id",
        ]

    @property
    def is_locked(self):
        return bool(
            self.published
            or self.locked_at
        )

    def clean(self):
        errors = {}

        if (
            self.examiner_id
            and self.examiner.role != "EXAMINER"
        ):
            errors["examiner"] = (
                "The selected user must be an examiner."
            )

        if (
            self.published_by_id
            and self.published_by.role != "SUPER_ADMIN"
        ):
            errors["published_by"] = (
                "Only a Super Admin can publish an evaluation."
            )

        if self.rubric_enabled:
            rubric_limits = {
                "proposal_problem_identification": Decimal("10"),
                "proposal_literature_review": Decimal("10"),
                "proposal_methodology": Decimal("10"),
                "progress_implementation": Decimal("10"),
                "progress_documentation": Decimal("10"),
                "progress_presentation": Decimal("10"),
                "viva_knowledge": Decimal("10"),
                "viva_presentation": Decimal("10"),
                "viva_question_answer": Decimal("10"),
                "viva_confidence": Decimal("10"),
            }

            for field_name, maximum in rubric_limits.items():
                value = getattr(
                    self,
                    field_name,
                    Decimal("0"),
                )

                if value < 0 or value > maximum:
                    errors[field_name] = (
                        f"Marks must be between 0 and {maximum}."
                    )

        else:
            summary_limits = {
                "proposal_marks": Decimal("30"),
                "progress_marks": Decimal("30"),
                "viva_marks": Decimal("40"),
            }

            for field_name, maximum in summary_limits.items():
                value = getattr(
                    self,
                    field_name,
                    Decimal("0"),
                )

                if value < 0 or value > maximum:
                    errors[field_name] = (
                        f"Marks must be between 0 and {maximum}."
                    )

        if self.total_marks < 0 or self.total_marks > 100:
            errors["total_marks"] = (
                "Total marks must be between 0 and 100."
            )

        if errors:
            raise ValidationError(errors)

    def calculate_result(self):
        if self.rubric_enabled:
            self.proposal_marks = (
                self.proposal_problem_identification
                + self.proposal_literature_review
                + self.proposal_methodology
            )

            self.progress_marks = (
                self.progress_implementation
                + self.progress_documentation
                + self.progress_presentation
            )

            self.viva_marks = (
                self.viva_knowledge
                + self.viva_presentation
                + self.viva_question_answer
                + self.viva_confidence
            )

        self.total_marks = (
            self.proposal_marks
            + self.progress_marks
            + self.viva_marks
        )

        # Green University of Bangladesh grading scale.
        if self.total_marks >= 80:
            self.grade = "A+"
            self.grade_point = Decimal("4.00")
            self.grade_definition = "Excellent"

        elif self.total_marks >= 75:
            self.grade = "A"
            self.grade_point = Decimal("3.75")
            self.grade_definition = "Excellent"

        elif self.total_marks >= 70:
            self.grade = "A-"
            self.grade_point = Decimal("3.50")
            self.grade_definition = "Very Good"

        elif self.total_marks >= 65:
            self.grade = "B+"
            self.grade_point = Decimal("3.25")
            self.grade_definition = "Good"

        elif self.total_marks >= 60:
            self.grade = "B"
            self.grade_point = Decimal("3.00")
            self.grade_definition = "Good"

        elif self.total_marks >= 55:
            self.grade = "B-"
            self.grade_point = Decimal("2.75")
            self.grade_definition = "Good"

        elif self.total_marks >= 50:
            self.grade = "C+"
            self.grade_point = Decimal("2.50")
            self.grade_definition = "Average"

        elif self.total_marks >= 45:
            self.grade = "C"
            self.grade_point = Decimal("2.25")
            self.grade_definition = "Average"

        elif self.total_marks >= 40:
            self.grade = "D"
            self.grade_point = Decimal("2.00")
            self.grade_definition = "Below Average"

        else:
            self.grade = "F"
            self.grade_point = Decimal("0.00")
            self.grade_definition = "Failing"

    def publish(self, user):
        self.published = True
        self.published_by = user
        self.published_at = timezone.now()
        self.locked_at = timezone.now()

    def unpublish(self):
        self.published = False
        self.published_by = None
        self.published_at = None
        self.locked_at = None

    def save(self, *args, **kwargs):
        self.calculate_result()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"Evaluation - {self.project.title}"
        )


class EvaluationAuditLog(models.Model):
    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="audit_logs",
    )

    action = models.CharField(
        max_length=20,
        choices=AUDIT_ACTION_CHOICES,
    )

    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluation_audit_logs",
    )

    old_data = models.JSONField(
        default=dict,
        blank=True,
    )

    new_data = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "-created_at",
            "-id",
        ]

    def __str__(self):
        return (
            f"{self.get_action_display()} - "
            f"{self.evaluation.project.title}"
        )