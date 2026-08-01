from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import User


TRAINING_STATUS_CHOICES = (
    ("PENDING", "Pending"),
    ("APPROVED", "Approved"),
    ("ONGOING", "Ongoing"),
    ("COMPLETED", "Completed"),
    ("REJECTED", "Rejected"),
    ("CANCELLED", "Cancelled"),
)


class Company(models.Model):
    name = models.CharField(
        max_length=200,
    )

    address = models.TextField(
        blank=True,
    )

    contact_person = models.CharField(
        max_length=100,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    phone = models.CharField(
        max_length=20,
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
            "name",
        ]

    def __str__(self):
        return self.name


class IndustrialTraining(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="industrial_trainings",
        limit_choices_to={
            "role": "STUDENT",
        },
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="trainings",
    )

    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_trainings",
        limit_choices_to={
            "role": "SUPERVISOR",
        },
    )

    title = models.CharField(
        max_length=200,
    )

    designation = models.CharField(
        max_length=150,
        blank=True,
    )

    description = models.TextField(
        blank=True,
    )

    start_date = models.DateField()

    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=TRAINING_STATUS_CHOICES,
        default="PENDING",
    )

    status_reason = models.TextField(
        blank=True,
    )

    offer_letter = models.FileField(
        upload_to="industrial_training_offer_letters/",
        blank=True,
        null=True,
    )

    final_report = models.FileField(
        upload_to="industrial_training_reports/",
        blank=True,
        null=True,
    )

    company_feedback = models.TextField(
        blank=True,
    )

    supervisor_feedback = models.TextField(
        blank=True,
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_trainings",
        limit_choices_to={
            "role": "SUPER_ADMIN",
        },
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
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

    def clean(self):
        errors = {}

        if (
            self.student_id
            and self.student.role != "STUDENT"
        ):
            errors["student"] = (
                "The selected user must be a student."
            )

        if (
            self.supervisor_id
            and self.supervisor.role != "SUPERVISOR"
        ):
            errors["supervisor"] = (
                "The selected user must be a supervisor."
            )

        if (
            self.start_date
            and self.end_date
            and self.end_date < self.start_date
        ):
            errors["end_date"] = (
                "End date cannot be earlier than start date."
            )

        if (
            self.status == "ONGOING"
            and not self.supervisor_id
        ):
            errors["supervisor"] = (
                "A supervisor must be assigned before training can be ongoing."
            )

        if (
            self.status == "COMPLETED"
            and not self.final_report
        ):
            errors["final_report"] = (
                "Final report is required before completing training."
            )

        if errors:
            raise ValidationError(errors)

    def set_status(
        self,
        new_status,
        changed_by=None,
        reason="",
    ):
        self.status = new_status
        self.status_reason = str(reason or "").strip()

        if new_status == "APPROVED":
            self.approved_by = changed_by
            self.approved_at = timezone.now()

        elif new_status == "COMPLETED":
            self.completed_at = timezone.now()

        elif new_status in {
            "PENDING",
            "REJECTED",
            "CANCELLED",
        }:
            if new_status != "PENDING":
                self.completed_at = None

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.company.name}"
        )


class TrainingFeedback(models.Model):
    training = models.ForeignKey(
        IndustrialTraining,
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )

    supervisor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="training_feedback_entries",
        limit_choices_to={
            "role": "SUPERVISOR",
        },
    )

    comment = models.TextField()

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
            f"Feedback for "
            f"{self.training}"
        )


class TrainingStatusHistory(models.Model):
    training = models.ForeignKey(
        IndustrialTraining,
        on_delete=models.CASCADE,
        related_name="status_history",
    )

    previous_status = models.CharField(
        max_length=20,
        choices=TRAINING_STATUS_CHOICES,
        blank=True,
    )

    new_status = models.CharField(
        max_length=20,
        choices=TRAINING_STATUS_CHOICES,
    )

    reason = models.TextField(
        blank=True,
    )

    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="training_status_changes",
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
            f"{self.training} - "
            f"{self.new_status}"
        )