from django.db import models
from accounts.models import User


TRAINING_STATUS_CHOICES = (
    ("PENDING", "Pending"),
    ("ONGOING", "Ongoing"),
    ("COMPLETED", "Completed"),
    ("CANCELLED", "Cancelled"),
)


class Company(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class IndustrialTraining(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="industrial_trainings",
        limit_choices_to={"role": "STUDENT"}
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="trainings"
    )

    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_trainings",
        limit_choices_to={"role": "SUPERVISOR"}
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    start_date = models.DateField()
    end_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=TRAINING_STATUS_CHOICES,
        default="PENDING"
    )

    final_report = models.FileField(
        upload_to="industrial_training_reports/",
        blank=True,
        null=True
    )

    company_feedback = models.TextField(blank=True)
    supervisor_feedback = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.company.name}"
    
class TrainingFeedback(models.Model):
    training = models.ForeignKey(
        IndustrialTraining,
        on_delete=models.CASCADE,
        related_name="feedbacks"
    )
    supervisor = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.training}"