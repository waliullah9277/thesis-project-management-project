from django.db import models
from accounts.models import User
from projects.models import Project


REPORT_STATUS_CHOICES = (
    ("SUBMITTED", "Submitted"),
    ("REVIEWED", "Reviewed"),
    ("NEEDS_IMPROVEMENT", "Needs Improvement"),
)


class ProgressReport(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="progress_reports"
    )

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submitted_progress_reports",
        limit_choices_to={"role": "STUDENT"}
    )

    title = models.CharField(max_length=200)
    description = models.TextField()

    file = models.FileField(
        upload_to="progress_reports/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=REPORT_STATUS_CHOICES,
        default="SUBMITTED"
    )

    supervisor_comment = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title