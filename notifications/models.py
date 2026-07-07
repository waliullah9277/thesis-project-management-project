from django.db import models
from accounts.models import User


NOTICE_AUDIENCE_CHOICES = (
    ("ALL", "All"),
    ("STUDENT", "Student"),
    ("SUPERVISOR", "Supervisor"),
    ("EXAMINER", "Examiner"),
)


class Notice(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()

    audience = models.CharField(
        max_length=20,
        choices=NOTICE_AUDIENCE_CHOICES,
        default="ALL"
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_notices"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    title = models.CharField(max_length=200)
    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title