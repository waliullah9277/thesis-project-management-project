from django.db import models
from django.utils import timezone

from accounts.models import User


NOTICE_AUDIENCE_CHOICES = (
    ("ALL", "All"),
    ("STUDENT", "Student"),
    ("SUPERVISOR", "Supervisor"),
    ("EXAMINER", "Examiner"),
)


NOTIFICATION_TYPE_CHOICES = (
    ("GENERAL", "General"),
    ("NOTICE", "Notice"),
    ("PROJECT", "Project"),
    ("DOCUMENT", "Document"),
    ("FEEDBACK", "Feedback"),
    ("VIVA", "Viva"),
    ("EVALUATION", "Evaluation"),
    ("RESULT", "Result"),
    ("TRAINING", "Industrial Training"),
    ("ACCOUNT", "Account"),
)


class Notice(models.Model):
    title = models.CharField(
        max_length=200,
    )

    message = models.TextField()

    audience = models.CharField(
        max_length=20,
        choices=NOTICE_AUDIENCE_CHOICES,
        default="ALL",
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_notices",
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

    def __str__(self):
        return self.title


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    title = models.CharField(
        max_length=200,
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES,
        default="GENERAL",
    )

    action_url = models.CharField(
        max_length=500,
        blank=True,
        help_text=(
            "Frontend page URL opened when the notification is selected."
        ),
    )

    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=(
            "Optional related project, document, viva or evaluation ID."
        ),
    )

    is_read = models.BooleanField(
        default=False,
    )

    read_at = models.DateTimeField(
        null=True,
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

        indexes = [
            models.Index(
                fields=[
                    "user",
                    "is_read",
                    "-created_at",
                ],
                name="notif_user_read_idx",
            ),
            models.Index(
                fields=[
                    "notification_type",
                    "-created_at",
                ],
                name="notif_type_date_idx",
            ),
        ]

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()

    def mark_as_unread(self):
        self.is_read = False
        self.read_at = None

    def __str__(self):
        return self.title