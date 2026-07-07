from django.db import models
from accounts.models import User
from projects.models import Project


class Evaluation(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="evaluation"
    )

    examiner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluations",
        limit_choices_to={"role": "EXAMINER"}
    )

    proposal_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    progress_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    viva_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    remarks = models.TextField(blank=True)

    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=10, blank=True)

    published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_result(self):
        self.total_marks = self.proposal_marks + self.progress_marks + self.viva_marks

        if self.total_marks >= 80:
            self.grade = "A+"
        elif self.total_marks >= 70:
            self.grade = "A"
        elif self.total_marks >= 60:
            self.grade = "B"
        elif self.total_marks >= 50:
            self.grade = "C"
        else:
            self.grade = "F"

    def save(self, *args, **kwargs):
        self.calculate_result()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Evaluation - {self.project.title}"