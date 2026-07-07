from django.db import models
from accounts.models import User
from projects.models import Project


VIVA_STATUS_CHOICES = (
    ("SCHEDULED", "Scheduled"),
    ("COMPLETED", "Completed"),
    ("CANCELLED", "Cancelled"),
)


class VivaSchedule(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="viva_schedule"
    )

    examiner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_vivas",
        limit_choices_to={"role": "EXAMINER"}
    )

    date = models.DateField()
    time = models.TimeField()
    room = models.CharField(max_length=100)

    status = models.CharField(
        max_length=20,
        choices=VIVA_STATUS_CHOICES,
        default="SCHEDULED"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Viva - {self.project.title}"