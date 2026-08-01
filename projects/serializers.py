from django.db import transaction

from rest_framework import serializers

from accounts.models import (
    StudentProfile,
    User,
)

from .models import (
    DOCUMENT_STATUS_CHOICES,
    DOCUMENT_TYPE_CHOICES,
    Project,
    ProjectDocument,
    ProjectFeedback,
    Team,
    TeamMemberInfo,
)


# =========================================================
# COMMON USER SERIALIZER
# =========================================================


class SimpleUserSerializer(
    serializers.ModelSerializer
):
    full_name = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = User

        fields = [
            "id",
            "student_id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "role",
        ]

    def get_full_name(self, obj):
        full_name = (
            f"{obj.first_name or ''} "
            f"{obj.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.student_id
            or obj.email
            or "User"
        )


# =========================================================
# TEAM MEMBER SERIALIZER
# =========================================================


class TeamMemberInfoSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = TeamMemberInfo

        fields = [
            "id",
            "team",
            "name",
            "student_id",
            "phone",
            "created_at",
        ]

        read_only_fields = [
            "team",
            "created_at",
        ]

    def validate_student_id(
        self,
        value,
    ):
        student_id = str(
            value or ""
        ).strip()

        if not student_id:
            raise serializers.ValidationError(
                "Student ID is required."
            )

        team = self.context.get(
            "team"
        )

        if (
            not team
            and self.instance
        ):
            team = self.instance.team

        if team:
            duplicate_query = (
                TeamMemberInfo.objects.filter(
                    team=team,
                    student_id__iexact=(
                        student_id
                    ),
                )
            )

            if self.instance:
                duplicate_query = (
                    duplicate_query.exclude(
                        id=self.instance.id
                    )
                )

            if duplicate_query.exists():
                raise serializers.ValidationError(
                    (
                        "This student ID has "
                        "already been added "
                        "to the team."
                    )
                )

        return student_id

    def validate_name(
        self,
        value,
    ):
        name = str(
            value or ""
        ).strip()

        if not name:
            raise serializers.ValidationError(
                "Member name is required."
            )

        return name


# =========================================================
# TEAM SERIALIZER
# =========================================================


class TeamSerializer(
    serializers.ModelSerializer
):
    leader_name = (
        serializers.SerializerMethodField()
    )

    leader_student_id = (
        serializers.CharField(
            source="leader.student_id",
            read_only=True,
        )
    )

    members_info = (
        serializers.SerializerMethodField()
    )

    member_infos = (
        TeamMemberInfoSerializer(
            many=True,
            read_only=True,
        )
    )

    project_start_semester_label = (
        serializers.SerializerMethodField()
    )

    project_end_semester_label = (
        serializers.SerializerMethodField()
    )

    project_duration = (
        serializers.SerializerMethodField()
    )

    project_semester_timeline = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = Team

        fields = [
            "id",
            "name",

            "leader",
            "leader_name",
            "leader_student_id",

            "members",
            "members_info",
            "member_infos",
            "member_count",

            "project_start_semester_label",
            "project_end_semester_label",
            "project_duration",
            "project_semester_timeline",

            "created_at",
        ]

        read_only_fields = [
            "leader",
            "members",
            "created_at",
        ]

    def validate_name(
        self,
        value,
    ):
        name = str(
            value or ""
        ).strip()

        if not name:
            raise serializers.ValidationError(
                "Team name is required."
            )

        duplicate_query = (
            Team.objects.filter(
                name__iexact=name
            )
        )

        if self.instance:
            duplicate_query = (
                duplicate_query.exclude(
                    id=self.instance.id
                )
            )

        if duplicate_query.exists():
            raise serializers.ValidationError(
                (
                    "A team with this name "
                    "already exists."
                )
            )

        return name

    def validate_member_count(
        self,
        value,
    ):
        if value < 1:
            raise serializers.ValidationError(
                "Minimum 1 member is required."
            )

        if value > 3:
            raise serializers.ValidationError(
                "Maximum 3 members are allowed."
            )

        if (
            self.instance
            and self.instance.member_infos.count()
            > value
        ):
            raise serializers.ValidationError(
                (
                    "Remove extra members before "
                    "reducing the team size."
                )
            )

        return value

    def create(
        self,
        validated_data,
    ):
        request = self.context.get(
            "request"
        )

        if (
            not request
            or not request.user.is_authenticated
        ):
            raise serializers.ValidationError(
                (
                    "Authenticated student "
                    "is required."
                )
            )

        if request.user.role != "STUDENT":
            raise serializers.ValidationError(
                (
                    "Only a student can "
                    "create a team."
                )
            )

        team = Team.objects.create(
            name=validated_data["name"],
            leader=request.user,
            member_count=validated_data.get(
                "member_count",
                1,
            ),
        )

        team.members.add(
            request.user
        )

        return team

    def get_leader_name(
        self,
        obj,
    ):
        full_name = (
            f"{obj.leader.first_name or ''} "
            f"{obj.leader.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.leader.student_id
            or "Team Leader"
        )

    def get_members_info(
        self,
        obj,
    ):
        return [
            {
                "id": member.id,
                "student_id": (
                    member.student_id
                ),
                "name": (
                    f"{member.first_name or ''} "
                    f"{member.last_name or ''}"
                ).strip(),
                "email": member.email,
                "phone": member.phone,
            }
            for member
            in obj.members.all()
        ]

    def get_leader_student_profile(
        self,
        obj,
    ):
        try:
            return (
                obj.leader.student_profile
            )

        except StudentProfile.DoesNotExist:
            return None

    def get_project_start_semester_label(
        self,
        obj,
    ):
        profile = (
            self.get_leader_student_profile(
                obj
            )
        )

        if not profile:
            return None

        return (
            profile
            .project_start_semester_label
        )

    def get_project_end_semester_label(
        self,
        obj,
    ):
        profile = (
            self.get_leader_student_profile(
                obj
            )
        )

        if not profile:
            return None

        return (
            profile
            .project_end_semester_label
        )

    def get_project_duration(
        self,
        obj,
    ):
        profile = (
            self.get_leader_student_profile(
                obj
            )
        )

        if not profile:
            return None

        return profile.project_duration

    def get_project_semester_timeline(
        self,
        obj,
    ):
        profile = (
            self.get_leader_student_profile(
                obj
            )
        )

        if not profile:
            return []

        return (
            profile
            .project_semester_timeline
        )


# =========================================================
# PROJECT DOCUMENT SERIALIZER
# =========================================================


class ProjectDocumentSerializer(
    serializers.ModelSerializer
):
    project_title = (
        serializers.CharField(
            source="project.title",
            read_only=True,
        )
    )

    team_name = (
        serializers.CharField(
            source="project.team.name",
            read_only=True,
        )
    )

    uploaded_by_details = (
        SimpleUserSerializer(
            source="uploaded_by",
            read_only=True,
        )
    )

    uploaded_by_name = (
        serializers.SerializerMethodField()
    )

    reviewed_by_details = (
        SimpleUserSerializer(
            source="reviewed_by",
            read_only=True,
        )
    )

    reviewed_by_name = (
        serializers.SerializerMethodField()
    )

    document_type_display = (
        serializers.CharField(
            source=(
                "get_document_type_display"
            ),
            read_only=True,
        )
    )

    status_display = (
        serializers.CharField(
            source="get_status_display",
            read_only=True,
        )
    )

    file_name = (
        serializers.SerializerMethodField()
    )

    file_extension = (
        serializers.SerializerMethodField()
    )

    file_size = (
        serializers.SerializerMethodField()
    )

    file_size_display = (
        serializers.SerializerMethodField()
    )

    file_url = (
        serializers.SerializerMethodField()
    )

    can_delete = (
        serializers.SerializerMethodField()
    )

    can_review = (
        serializers.SerializerMethodField()
    )

    version_count = (
        serializers.SerializerMethodField()
    )

    has_previous_version = (
        serializers.SerializerMethodField()
    )

    previous_version_id = (
        serializers.IntegerField(
            source="previous_version.id",
            read_only=True,
        )
    )

    previous_document_id = (
        serializers.IntegerField(
            write_only=True,
            required=False,
            allow_null=True,
        )
    )

    class Meta:
        model = ProjectDocument

        fields = [
            "id",

            "project",
            "project_title",
            "team_name",

            "title",
            "description",

            "document_type",
            "document_type_display",

            "file",
            "file_url",
            "file_name",
            "original_file_name",
            "file_extension",
            "file_size",
            "file_size_display",

            "submission_group",
            "previous_version",
            "previous_version_id",
            "previous_document_id",

            "version",
            "version_count",
            "has_previous_version",
            "is_latest",

            "status",
            "status_display",

            "supervisor_remarks",

            "uploaded_by",
            "uploaded_by_details",
            "uploaded_by_name",

            "reviewed_by",
            "reviewed_by_details",
            "reviewed_by_name",
            "reviewed_at",

            "download_count",

            "uploaded_at",
            "updated_at",

            "can_delete",
            "can_review",
        ]

        read_only_fields = [
            "project",

            "original_file_name",
            "submission_group",
            "previous_version",

            "version",
            "is_latest",

            "status",
            "supervisor_remarks",

            "uploaded_by",

            "reviewed_by",
            "reviewed_at",

            "download_count",

            "uploaded_at",
            "updated_at",
        ]

        extra_kwargs = {
            "file": {
                "required": True,
                "allow_null": False,
            },
            "description": {
                "required": False,
                "allow_blank": True,
            },
        }

    def validate_title(
        self,
        value,
    ):
        title = str(
            value or ""
        ).strip()

        if not title:
            raise serializers.ValidationError(
                (
                    "Document title "
                    "is required."
                )
            )

        if len(title) < 3:
            raise serializers.ValidationError(
                (
                    "Document title must "
                    "contain at least "
                    "3 characters."
                )
            )

        return title

    def validate_description(
        self,
        value,
    ):
        return str(
            value or ""
        ).strip()

    def validate_document_type(
        self,
        value,
    ):
        allowed_values = {
            choice[0]
            for choice
            in DOCUMENT_TYPE_CHOICES
        }

        if value not in allowed_values:
            raise serializers.ValidationError(
                "Invalid document type."
            )

        return value

    def validate_file(
        self,
        value,
    ):
        if not value:
            raise serializers.ValidationError(
                (
                    "Please select a file "
                    "to upload."
                )
            )

        return value

    def validate(
        self,
        attrs,
    ):
        request = self.context.get(
            "request"
        )

        project = self.context.get(
            "project"
        )

        if (
            not request
            or not request.user.is_authenticated
        ):
            raise serializers.ValidationError(
                "Authentication is required."
            )

        if not project:
            raise serializers.ValidationError(
                (
                    "Project information "
                    "is required."
                )
            )

        user = request.user

        if user.role == "STUDENT":
            is_member = (
                project.team.members.filter(
                    id=user.id
                ).exists()
            )

            is_leader = (
                project.team.leader_id
                == user.id
            )

            if (
                not is_member
                and not is_leader
            ):
                raise serializers.ValidationError(
                    (
                        "You can upload documents "
                        "only for your own project."
                    )
                )

        elif user.role == "SUPERVISOR":
            if (
                project.supervisor_id
                != user.id
            ):
                raise serializers.ValidationError(
                    (
                        "You are not assigned "
                        "to this project."
                    )
                )

        elif user.role != "SUPER_ADMIN":
            raise serializers.ValidationError(
                (
                    "You are not allowed to "
                    "upload project documents."
                )
            )

        previous_document_id = attrs.get(
            "previous_document_id"
        )

        if previous_document_id:
            try:
                previous_document = (
                    ProjectDocument
                    .objects
                    .select_related(
                        "project"
                    )
                    .get(
                        id=previous_document_id
                    )
                )

            except ProjectDocument.DoesNotExist:
                raise serializers.ValidationError({
                    "previous_document_id": (
                        "The selected previous "
                        "version was not found."
                    )
                })

            if (
                previous_document.project_id
                != project.id
            ):
                raise serializers.ValidationError({
                    "previous_document_id": (
                        "The previous version "
                        "must belong to the "
                        "same project."
                    )
                })

            document_type = attrs.get(
                "document_type",
                previous_document.document_type,
            )

            if (
                previous_document.document_type
                != document_type
            ):
                raise serializers.ValidationError({
                    "document_type": (
                        "The new version must "
                        "use the same document "
                        "type as the previous version."
                    )
                })

            if not previous_document.is_latest:
                raise serializers.ValidationError({
                    "previous_document_id": (
                        "Only the latest document "
                        "version can be replaced."
                    )
                })

            attrs[
                "_previous_document"
            ] = previous_document

        return attrs

    @transaction.atomic
    def create(
        self,
        validated_data,
    ):
        request = self.context[
            "request"
        ]

        project = self.context[
            "project"
        ]

        previous_document = (
            validated_data.pop(
                "_previous_document",
                None,
            )
        )

        validated_data.pop(
            "previous_document_id",
            None,
        )

        uploaded_file = (
            validated_data.get("file")
        )

        if previous_document:
            previous_document.is_latest = False

            previous_document.save(
                update_fields=[
                    "is_latest",
                    "updated_at",
                ]
            )

            submission_group = (
                previous_document
                .submission_group
            )

            next_version = (
                previous_document.version
                + 1
            )

            document = (
                ProjectDocument.objects.create(
                    project=project,
                    uploaded_by=request.user,
                    submission_group=(
                        submission_group
                    ),
                    previous_version=(
                        previous_document
                    ),
                    version=next_version,
                    is_latest=True,
                    status="PENDING",
                    original_file_name=(
                        uploaded_file.name
                        if uploaded_file
                        else ""
                    ),
                    **validated_data,
                )
            )

            return document

        document_type = (
            validated_data.get(
                "document_type",
                "OTHER",
            )
        )

        title = validated_data.get(
            "title",
            "",
        )

        existing_latest = (
            ProjectDocument.objects.filter(
                project=project,
                document_type=document_type,
                title__iexact=title,
                is_latest=True,
            )
            .order_by(
                "-uploaded_at",
                "-id",
            )
            .first()
        )

        if existing_latest:
            raise serializers.ValidationError({
                "previous_document_id": (
                    "A latest submission with "
                    "this title and document type "
                    "already exists. Submit the "
                    "new file as a revised version."
                )
            })

        document = (
            ProjectDocument.objects.create(
                project=project,
                uploaded_by=request.user,
                version=1,
                is_latest=True,
                status="PENDING",
                original_file_name=(
                    uploaded_file.name
                    if uploaded_file
                    else ""
                ),
                **validated_data,
            )
        )

        return document

    def get_uploaded_by_name(
        self,
        obj,
    ):
        full_name = (
            f"{obj.uploaded_by.first_name or ''} "
            f"{obj.uploaded_by.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.uploaded_by.student_id
            or obj.uploaded_by.email
            or "User"
        )

    def get_reviewed_by_name(
        self,
        obj,
    ):
        if not obj.reviewed_by:
            return None

        full_name = (
            f"{obj.reviewed_by.first_name or ''} "
            f"{obj.reviewed_by.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.reviewed_by.email
            or "Supervisor"
        )

    def get_file_name(
        self,
        obj,
    ):
        return obj.file_name

    def get_file_extension(
        self,
        obj,
    ):
        return obj.file_extension

    def get_file_size(
        self,
        obj,
    ):
        return obj.file_size

    def get_file_size_display(
        self,
        obj,
    ):
        return obj.file_size_display

    def get_file_url(
        self,
        obj,
    ):
        if not obj.file:
            return None

        request = self.context.get(
            "request"
        )

        if request:
            return (
                request.build_absolute_uri(
                    obj.file.url
                )
            )

        return obj.file.url

    def get_can_delete(
        self,
        obj,
    ):
        request = self.context.get(
            "request"
        )

        if (
            not request
            or not request.user.is_authenticated
        ):
            return False

        user = request.user

        if user.role == "SUPER_ADMIN":
            return True

        if (
            user.role == "STUDENT"
            and obj.uploaded_by_id
            == user.id
            and obj.is_latest
            and obj.status
            in {
                "PENDING",
                "REVISION_REQUIRED",
                "REJECTED",
            }
        ):
            return True

        return False

    def get_can_review(
        self,
        obj,
    ):
        request = self.context.get(
            "request"
        )

        if (
            not request
            or not request.user.is_authenticated
        ):
            return False

        user = request.user

        return (
            user.role == "SUPERVISOR"
            and obj.is_latest
            and obj.project.supervisor_id
            == user.id
        )

    def get_version_count(
        self,
        obj,
    ):
        return obj.version_count

    def get_has_previous_version(
        self,
        obj,
    ):
        return obj.has_previous_version


# =========================================================
# DOCUMENT REVIEW SERIALIZER
# =========================================================


class ProjectDocumentReviewSerializer(
    serializers.Serializer
):
    status = serializers.ChoiceField(
        choices=DOCUMENT_STATUS_CHOICES,
    )

    supervisor_remarks = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            trim_whitespace=True,
            max_length=3000,
        )
    )

    def validate(
        self,
        attrs,
    ):
        status_value = attrs.get(
            "status"
        )

        remarks = str(
            attrs.get(
                "supervisor_remarks",
                "",
            )
            or ""
        ).strip()

        if (
            status_value
            in {
                "REVISION_REQUIRED",
                "REJECTED",
            }
            and not remarks
        ):
            raise serializers.ValidationError({
                "supervisor_remarks": (
                    "Remarks are required when "
                    "a document needs revision "
                    "or is rejected."
                )
            })

        attrs[
            "supervisor_remarks"
        ] = remarks

        return attrs


# =========================================================
# PROJECT SERIALIZER
# =========================================================


class ProjectSerializer(
    serializers.ModelSerializer
):
    team_details = TeamSerializer(
        source="team",
        read_only=True,
    )

    supervisor_details = (
        SimpleUserSerializer(
            source="supervisor",
            read_only=True,
        )
    )

    submitted_by_details = (
        SimpleUserSerializer(
            source="submitted_by",
            read_only=True,
        )
    )

    team_name = serializers.CharField(
        source="team.name",
        read_only=True,
    )

    team_leader_name = (
        serializers.SerializerMethodField()
    )

    team_leader_student_id = (
        serializers.SerializerMethodField()
    )

    supervisor_name = (
        serializers.SerializerMethodField()
    )

    submitted_by_name = (
        serializers.SerializerMethodField()
    )

    submitted_by_student_id = (
        serializers.CharField(
            source=(
                "submitted_by.student_id"
            ),
            read_only=True,
        )
    )

    project_start_term = (
        serializers.SerializerMethodField()
    )

    project_start_term_display = (
        serializers.SerializerMethodField()
    )

    project_start_year = (
        serializers.SerializerMethodField()
    )

    project_duration = (
        serializers.SerializerMethodField()
    )

    project_start_semester_label = (
        serializers.SerializerMethodField()
    )

    project_end_semester = (
        serializers.SerializerMethodField()
    )

    project_end_semester_label = (
        serializers.SerializerMethodField()
    )

    project_semester_timeline = (
        serializers.SerializerMethodField()
    )

    document_count = (
        serializers.SerializerMethodField()
    )

    latest_document_count = (
        serializers.SerializerMethodField()
    )

    pending_document_count = (
        serializers.SerializerMethodField()
    )

    approved_document_count = (
        serializers.SerializerMethodField()
    )

    revision_document_count = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = Project

        fields = [
            "id",

            "team",
            "team_details",
            "team_name",
            "team_leader_name",
            "team_leader_student_id",

            "supervisor",
            "supervisor_details",
            "supervisor_name",

            "submitted_by",
            "submitted_by_details",
            "submitted_by_name",
            "submitted_by_student_id",

            "title",
            "project_type",
            "description",
            "technology_stack",
            "status",

            "project_start_term",
            "project_start_term_display",
            "project_start_year",
            "project_duration",

            "project_start_semester_label",
            "project_end_semester",
            "project_end_semester_label",
            "project_semester_timeline",

            "document_count",
            "latest_document_count",
            "pending_document_count",
            "approved_document_count",
            "revision_document_count",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "status",
            "submitted_by",
            "created_at",
            "updated_at",
        ]

    def validate_team(
        self,
        team,
    ):
        request = self.context.get(
            "request"
        )

        if (
            not request
            or not request.user.is_authenticated
        ):
            raise serializers.ValidationError(
                (
                    "Authenticated student "
                    "is required."
                )
            )

        if request.user.role != "STUDENT":
            raise serializers.ValidationError(
                (
                    "Only a student can "
                    "submit a project."
                )
            )

        is_team_member = (
            team.members.filter(
                id=request.user.id
            ).exists()
        )

        is_team_leader = (
            team.leader_id
            == request.user.id
        )

        if (
            not is_team_member
            and not is_team_leader
        ):
            raise serializers.ValidationError(
                (
                    "You can submit a project "
                    "only for your own team."
                )
            )

        existing_project = (
            Project.objects.filter(
                team=team
            )
        )

        if self.instance:
            existing_project = (
                existing_project.exclude(
                    id=self.instance.id
                )
            )

        if existing_project.exists():
            raise serializers.ValidationError(
                (
                    "This team already "
                    "has a project."
                )
            )

        return team

    def create(
        self,
        validated_data,
    ):
        request = self.context.get(
            "request"
        )

        if (
            not request
            or not request.user.is_authenticated
        ):
            raise serializers.ValidationError(
                (
                    "Authenticated student "
                    "is required."
                )
            )

        return Project.objects.create(
            submitted_by=request.user,
            **validated_data,
        )

    def get_student_profile(
        self,
        obj,
    ):
        try:
            return (
                obj.submitted_by
                .student_profile
            )

        except StudentProfile.DoesNotExist:
            pass

        try:
            return (
                obj.team.leader
                .student_profile
            )

        except (
            StudentProfile.DoesNotExist,
            AttributeError,
        ):
            return None

    def get_team_leader_name(
        self,
        obj,
    ):
        leader = getattr(
            obj.team,
            "leader",
            None,
        )

        if not leader:
            return None

        full_name = (
            f"{leader.first_name or ''} "
            f"{leader.last_name or ''}"
        ).strip()

        return (
            full_name
            or leader.student_id
            or "Team Leader"
        )

    def get_team_leader_student_id(
        self,
        obj,
    ):
        leader = getattr(
            obj.team,
            "leader",
            None,
        )

        if not leader:
            return None

        return leader.student_id

    def get_supervisor_name(
        self,
        obj,
    ):
        if not obj.supervisor:
            return None

        full_name = (
            f"{obj.supervisor.first_name or ''} "
            f"{obj.supervisor.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.supervisor.email
            or "Supervisor"
        )

    def get_submitted_by_name(
        self,
        obj,
    ):
        full_name = (
            f"{obj.submitted_by.first_name or ''} "
            f"{obj.submitted_by.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.submitted_by.student_id
            or "Student"
        )

    def get_project_start_term(
        self,
        obj,
    ):
        profile = self.get_student_profile(
            obj
        )

        return (
            profile.project_start_term
            if profile
            else None
        )

    def get_project_start_term_display(
        self,
        obj,
    ):
        profile = self.get_student_profile(
            obj
        )

        if (
            not profile
            or not profile.project_start_term
        ):
            return None

        return (
            profile
            .get_project_start_term_display()
        )

    def get_project_start_year(
        self,
        obj,
    ):
        profile = self.get_student_profile(
            obj
        )

        return (
            profile.project_start_year
            if profile
            else None
        )

    def get_project_duration(
        self,
        obj,
    ):
        profile = self.get_student_profile(
            obj
        )

        return (
            profile.project_duration
            if profile
            else None
        )

    def get_project_start_semester_label(
        self,
        obj,
    ):
        profile = self.get_student_profile(
            obj
        )

        return (
            profile.project_start_semester_label
            if profile
            else None
        )

    def get_project_end_semester(
        self,
        obj,
    ):
        profile = self.get_student_profile(
            obj
        )

        return (
            profile.project_end_semester
            if profile
            else None
        )

    def get_project_end_semester_label(
        self,
        obj,
    ):
        profile = self.get_student_profile(
            obj
        )

        return (
            profile.project_end_semester_label
            if profile
            else None
        )

    def get_project_semester_timeline(
        self,
        obj,
    ):
        profile = self.get_student_profile(
            obj
        )

        return (
            profile.project_semester_timeline
            if profile
            else []
        )

    def get_document_count(
        self,
        obj,
    ):
        return obj.documents.count()

    def get_latest_document_count(
        self,
        obj,
    ):
        return obj.documents.filter(
            is_latest=True
        ).count()

    def get_pending_document_count(
        self,
        obj,
    ):
        return obj.documents.filter(
            is_latest=True,
            status="PENDING",
        ).count()

    def get_approved_document_count(
        self,
        obj,
    ):
        return obj.documents.filter(
            is_latest=True,
            status="APPROVED",
        ).count()

    def get_revision_document_count(
        self,
        obj,
    ):
        return obj.documents.filter(
            is_latest=True,
            status__in=[
                "REVISION_REQUIRED",
                "REJECTED",
            ],
        ).count()


# =========================================================
# ASSIGN SUPERVISOR SERIALIZER
# =========================================================


class AssignSupervisorSerializer(
    serializers.Serializer
):
    supervisor_id = (
        serializers.IntegerField()
    )

    def validate_supervisor_id(
        self,
        value,
    ):
        try:
            User.objects.get(
                id=value,
                role="SUPERVISOR",
                is_active=True,
            )

        except User.DoesNotExist:
            raise serializers.ValidationError(
                (
                    "An active and valid "
                    "supervisor was not found."
                )
            )

        return value


# =========================================================
# PROJECT STATUS SERIALIZER
# =========================================================


class ProjectStatusUpdateSerializer(
    serializers.Serializer
):
    status = serializers.ChoiceField(
        choices=[
            "PENDING",
            "SUPERVISOR_ASSIGNED",
            "PROPOSAL_APPROVED",
            "REVISION_REQUIRED",
            "REJECTED",
            "IN_PROGRESS",
            "PROGRESS_REVIEW",
            "FINAL_SUBMITTED",
            "READY_FOR_VIVA",
            "COMPLETED",
        ]
    )


# =========================================================
# PROJECT FEEDBACK SERIALIZER
# =========================================================


class ProjectFeedbackSerializer(
    serializers.ModelSerializer
):
    supervisor_details = (
        SimpleUserSerializer(
            source="supervisor",
            read_only=True,
        )
    )

    supervisor_name = (
        serializers.SerializerMethodField()
    )

    class Meta:
        model = ProjectFeedback

        fields = [
            "id",
            "project",

            "supervisor",
            "supervisor_details",
            "supervisor_name",

            "comment",
            "created_at",
        ]

        read_only_fields = [
            "supervisor",
            "created_at",
        ]

    def validate_comment(
        self,
        value,
    ):
        comment = str(
            value or ""
        ).strip()

        if not comment:
            raise serializers.ValidationError(
                (
                    "Feedback comment "
                    "is required."
                )
            )

        return comment

    def create(
        self,
        validated_data,
    ):
        request = self.context.get(
            "request"
        )

        if (
            not request
            or not request.user.is_authenticated
        ):
            raise serializers.ValidationError(
                (
                    "Authenticated supervisor "
                    "is required."
                )
            )

        if (
            request.user.role
            != "SUPERVISOR"
        ):
            raise serializers.ValidationError(
                (
                    "Only a supervisor can "
                    "submit project feedback."
                )
            )

        return (
            ProjectFeedback.objects.create(
                supervisor=request.user,
                **validated_data,
            )
        )

    def get_supervisor_name(
        self,
        obj,
    ):
        full_name = (
            f"{obj.supervisor.first_name or ''} "
            f"{obj.supervisor.last_name or ''}"
        ).strip()

        return (
            full_name
            or obj.supervisor.email
            or "Supervisor"
        )


# =========================================================
# SUPERVISOR PROJECT REVIEW SERIALIZER
# =========================================================


class SupervisorProjectReviewSerializer(
    serializers.Serializer
):
    status = serializers.ChoiceField(
        choices=[
            (
                "SUPERVISOR_ASSIGNED",
                "Supervisor Assigned",
            ),
            (
                "PROPOSAL_APPROVED",
                "Proposal Approved",
            ),
            (
                "REVISION_REQUIRED",
                "Revision Required",
            ),
            (
                "IN_PROGRESS",
                "In Progress",
            ),
            (
                "PROGRESS_REVIEW",
                "Progress Under Review",
            ),
            (
                "FINAL_SUBMITTED",
                "Final Submitted",
            ),
            (
                "READY_FOR_VIVA",
                "Ready For Viva",
            ),
            (
                "COMPLETED",
                "Completed",
            ),
            (
                "REJECTED",
                "Rejected",
            ),
        ]
    )

    comment = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=3000,
    )