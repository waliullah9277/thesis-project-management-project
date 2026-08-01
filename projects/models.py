import os
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from accounts.models import User


PROJECT_TYPE_CHOICES = (
    ("PROJECT", "Project"),
    ("THESIS", "Thesis"),
    ("INDUSTRIAL_TRAINING", "Industrial Training"),
)


PROJECT_STATUS_CHOICES = (
    ("PENDING", "Pending"),
    ("SUPERVISOR_ASSIGNED", "Supervisor Assigned"),
    ("REVISION_REQUIRED", "Revision Required"),
    ("PROPOSAL_APPROVED", "Proposal Approved"),
    ("IN_PROGRESS", "In Progress"),
    ("PROGRESS_REVIEW", "Progress Under Review"),
    ("FINAL_SUBMITTED", "Final Submitted"),
    ("READY_FOR_VIVA", "Ready For Viva"),
    ("COMPLETED", "Completed"),
    ("REJECTED", "Rejected"),
)


DOCUMENT_TYPE_CHOICES = (
    ("PROPOSAL", "Proposal"),
    ("PROPOSAL_PRESENTATION", "Proposal Presentation"),
    ("PROGRESS_REPORT", "Progress Report"),
    ("FINAL_REPORT", "Final Report"),
    ("FINAL_PRESENTATION", "Final Presentation"),
    ("THESIS_BOOK", "Thesis Book"),
    ("RESEARCH_PAPER", "Research Paper"),
    ("DATASET", "Dataset"),
    ("SOURCE_CODE", "Source Code"),
    ("POSTER", "Poster"),
    ("DIAGRAM", "Diagram or Image"),
    ("OTHER", "Other"),
)


DOCUMENT_STATUS_CHOICES = (
    ("PENDING", "Pending Review"),
    ("APPROVED", "Approved"),
    ("REVISION_REQUIRED", "Revision Required"),
    ("REJECTED", "Rejected"),
)


ALLOWED_PROJECT_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".jpg",
    ".jpeg",
    ".png",
    ".zip",
}


MAX_PROJECT_DOCUMENT_SIZE = 20 * 1024 * 1024


def validate_project_document(file):
    """
    Validate a project document's extension and maximum file size.
    """

    if not file:
        raise ValidationError(
            "Please select a file to upload."
        )

    extension = os.path.splitext(
        file.name
    )[1].lower()

    if extension not in ALLOWED_PROJECT_DOCUMENT_EXTENSIONS:
        allowed_extensions = ", ".join(
            sorted(
                ALLOWED_PROJECT_DOCUMENT_EXTENSIONS
            )
        )

        raise ValidationError(
            (
                "Unsupported file type. "
                f"Allowed file types: {allowed_extensions}."
            )
        )

    if file.size > MAX_PROJECT_DOCUMENT_SIZE:
        raise ValidationError(
            "File size cannot exceed 20 MB."
        )


class Team(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True,
    )

    leader = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="leading_teams",
        limit_choices_to={"role": "STUDENT"},
    )

    members = models.ManyToManyField(
        User,
        related_name="teams",
        limit_choices_to={"role": "STUDENT"},
        blank=True,
    )

    member_count = models.PositiveIntegerField(
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def clean(self):
        errors = {}

        if (
            self.leader_id
            and self.leader.role != "STUDENT"
        ):
            errors["leader"] = (
                "The team leader must be a student."
            )

        if self.member_count < 1:
            errors["member_count"] = (
                "Minimum 1 member is required."
            )

        if self.member_count > 3:
            errors["member_count"] = (
                "Maximum 3 members are allowed."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name


class Project(models.Model):
    team = models.OneToOneField(
        Team,
        on_delete=models.CASCADE,
        related_name="project",
    )

    supervisor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supervised_projects",
        limit_choices_to={
            "role": "SUPERVISOR"
        },
    )

    title = models.CharField(
        max_length=255,
    )

    project_type = models.CharField(
        max_length=30,
        choices=PROJECT_TYPE_CHOICES,
    )

    description = models.TextField()

    technology_stack = models.CharField(
        max_length=255,
        blank=True,
    )

    status = models.CharField(
        max_length=30,
        choices=PROJECT_STATUS_CHOICES,
        default="PENDING",
    )

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submitted_projects",
        limit_choices_to={"role": "STUDENT"},
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def clean(self):
        errors = {}

        if (
            self.submitted_by_id
            and self.submitted_by.role
            != "STUDENT"
        ):
            errors["submitted_by"] = (
                "The project submitter must be a student."
            )

        if (
            self.supervisor_id
            and self.supervisor.role
            != "SUPERVISOR"
        ):
            errors["supervisor"] = (
                "The assigned user must be a supervisor."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title


class ProjectDocument(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    title = models.CharField(
        max_length=150,
    )

    description = models.TextField(
        blank=True,
    )

    document_type = models.CharField(
        max_length=40,
        choices=DOCUMENT_TYPE_CHOICES,
        default="OTHER",
    )

    file = models.FileField(
        upload_to="project_documents/%Y/%m/",
        validators=[
            validate_project_document
        ],
    )

    original_file_name = models.CharField(
        max_length=255,
        blank=True,
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name=(
            "uploaded_project_documents"
        ),
    )

    submission_group = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )

    previous_version = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_versions",
    )

    version = models.PositiveIntegerField(
        default=1,
    )

    is_latest = models.BooleanField(
        default=True,
        db_index=True,
    )

    status = models.CharField(
        max_length=30,
        choices=DOCUMENT_STATUS_CHOICES,
        default="PENDING",
    )

    supervisor_remarks = models.TextField(
        blank=True,
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name=(
            "reviewed_project_documents"
        ),
        limit_choices_to={
            "role": "SUPERVISOR"
        },
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    download_count = (
        models.PositiveIntegerField(
            default=0,
        )
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-uploaded_at",
            "-id",
        ]

        indexes = [
            models.Index(
                fields=[
                    "project",
                    "document_type",
                    "is_latest",
                ],
                name=(
                    "project_doc_latest_idx"
                ),
            ),
            models.Index(
                fields=[
                    "submission_group",
                    "version",
                ],
                name=(
                    "project_doc_version_idx"
                ),
            ),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "submission_group",
                    "version",
                ],
                name=(
                    "unique_submission_version"
                ),
            ),
        ]

    def clean(self):
        errors = {}

        if (
            self.uploaded_by_id
            and self.uploaded_by.role
            not in {
                "STUDENT",
                "SUPERVISOR",
                "SUPER_ADMIN",
            }
        ):
            errors["uploaded_by"] = (
                "This user is not allowed to "
                "upload project documents."
            )

        if (
            self.reviewed_by_id
            and self.reviewed_by.role
            != "SUPERVISOR"
        ):
            errors["reviewed_by"] = (
                "Only a supervisor can review "
                "a project document."
            )

        if (
            self.reviewed_by_id
            and self.project_id
            and self.project.supervisor_id
            != self.reviewed_by_id
        ):
            errors["reviewed_by"] = (
                "Only the assigned project "
                "supervisor can review this document."
            )

        if self.version < 1:
            errors["version"] = (
                "Document version must be at least 1."
            )

        if (
            self.previous_version_id
            and self.previous_version_id == self.id
        ):
            errors["previous_version"] = (
                "A document cannot reference itself "
                "as the previous version."
            )

        if self.previous_version_id:
            previous = self.previous_version

            if (
                previous.project_id
                != self.project_id
            ):
                errors["previous_version"] = (
                    "The previous version must belong "
                    "to the same project."
                )

            if (
                previous.document_type
                != self.document_type
            ):
                errors["previous_version"] = (
                    "The previous version must have "
                    "the same document type."
                )

            if (
                previous.submission_group
                != self.submission_group
            ):
                errors["submission_group"] = (
                    "All document versions must use "
                    "the same submission group."
                )

            if (
                self.version
                != previous.version + 1
            ):
                errors["version"] = (
                    "The new version number must be "
                    "one greater than the previous version."
                )

        if errors:
            raise ValidationError(errors)

    def save(
        self,
        *args,
        **kwargs,
    ):
        if self.file:
            if not self.original_file_name:
                self.original_file_name = (
                    os.path.basename(
                        self.file.name
                    )
                )

        if self.status == "PENDING":
            self.reviewed_by = None
            self.reviewed_at = None
            self.supervisor_remarks = ""

        elif (
            self.reviewed_by_id
            and not self.reviewed_at
        ):
            self.reviewed_at = (
                timezone.now()
            )

        self.full_clean()

        super().save(
            *args,
            **kwargs,
        )

    @property
    def file_name(self):
        if self.original_file_name:
            return self.original_file_name

        if not self.file:
            return None

        return os.path.basename(
            self.file.name
        )

    @property
    def file_extension(self):
        file_name = self.file_name

        if not file_name:
            return None

        return os.path.splitext(
            file_name
        )[1].lower()

    @property
    def file_size(self):
        if not self.file:
            return 0

        try:
            return self.file.size

        except (
            FileNotFoundError,
            OSError,
        ):
            return 0

    @property
    def file_size_display(self):
        size = self.file_size

        if size < 1024:
            return f"{size} B"

        if size < 1024 * 1024:
            return (
                f"{size / 1024:.2f} KB"
            )

        return (
            f"{size / (1024 * 1024):.2f} MB"
        )

    @property
    def has_previous_version(self):
        return bool(
            self.previous_version_id
        )

    @property
    def version_count(self):
        return (
            ProjectDocument.objects.filter(
                submission_group=(
                    self.submission_group
                )
            ).count()
        )

    def __str__(self):
        return (
            f"{self.title} - "
            f"{self.get_document_type_display()} "
            f"(Version {self.version})"
        )


class ProjectFeedback(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="feedbacks",
    )

    supervisor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="project_feedbacks",
        limit_choices_to={
            "role": "SUPERVISOR"
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

    def clean(self):
        if (
            self.supervisor_id
            and self.project_id
            and self.project.supervisor_id
            != self.supervisor_id
        ):
            raise ValidationError({
                "supervisor": (
                    "Only the assigned supervisor "
                    "can provide feedback for "
                    "this project."
                )
            })

    def __str__(self):
        return (
            f"Feedback for "
            f"{self.project.title}"
        )


class TeamMemberInfo(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="member_infos",
    )

    name = models.CharField(
        max_length=150,
    )

    student_id = models.CharField(
        max_length=30,
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["id"]

    def clean(self):
        if (
            self.team_id
            and self.pk is None
            and self.team.member_infos.count()
            >= self.team.member_count
        ):
            raise ValidationError({
                "team": (
                    f"This team allows maximum "
                    f"{self.team.member_count} "
                    f"member(s)."
                )
            })

    def __str__(self):
        return (
            f"{self.name} - "
            f"{self.team.name}"
        )