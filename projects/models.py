from django.db import models
from accounts.models import User


PROJECT_TYPE_CHOICES = (
    ("PROJECT", "Project"),
    ("THESIS", "Thesis"),
    ("INDUSTRIAL_TRAINING", "Industrial Training"),
)

PROJECT_STATUS_CHOICES = (
    ("PENDING", "Pending"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
    ("IN_PROGRESS", "In Progress"),
    ("COMPLETED", "Completed"),
)


class Team(models.Model):
    name = models.CharField(max_length=150, unique=True)
    leader = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="leading_teams",
        limit_choices_to={"role": "STUDENT"}
    )
    members = models.ManyToManyField(
        User,
        related_name="teams",
        limit_choices_to={"role": "STUDENT"},
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Project(models.Model):
    team = models.OneToOneField(
        Team,
        on_delete=models.CASCADE,
        related_name="project"
    )
    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_projects",
        limit_choices_to={"role": "SUPERVISOR"}
    )

    title = models.CharField(max_length=255)
    project_type = models.CharField(
        max_length=30,
        choices=PROJECT_TYPE_CHOICES
    )
    description = models.TextField()
    technology_stack = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=PROJECT_STATUS_CHOICES,
        default="PENDING"
    )

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submitted_projects",
        limit_choices_to={"role": "STUDENT"}
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class ProjectDocument(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="documents"
    )
    title = models.CharField(max_length=150)
    file = models.FileField(upload_to="project_documents/")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="uploaded_project_documents"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ProjectFeedback(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )

    supervisor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="project_feedbacks",
        limit_choices_to={"role": "SUPERVISOR"}
    )

    comment = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.project.title}"